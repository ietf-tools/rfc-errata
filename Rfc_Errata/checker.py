import json
import re
import os
import datetime
import shutil
import email.utils as eut

from http.client import HTTPSConnection, HTTPException
from Rfc_Errata.apply_errata import apply_errata


def fixSection(sectionIn):
    #  It is a number
    section = "{0}".format(sectionIn)

    # It has trailing spaces
    section = section.rstrip()

    # Strip leading 99's
    match = re.match("99\s*(.*)", section)
    if match:
        section = match.group(1)

    # Common pattern is "[In ]Appendix B.2[ [it ]says[:]]
    match = re.match("([I|i]n )?((Section|Appendix) ((\w|\d+)(\.\d+)*)) ?(says)?:?", section)
    if match:
        section = match.group(2)

    # It has a preceding section marker
    match = re.match("[sS](ection[ -])?(\d+(\.\d+)*)", section)
    if match:
        section = match.group(2)

    # 1.1, 2.2, 3.3
    section = section.split(',')[0]

    # 1.1 Introduction
    match = re.match("\d+(\.\d+)*\.? ", section)
    if match:
        section = match.group(0)[:-1]

    # spelling error
    section = section.replace("Apendix", "Appendix")
    section = section.replace("App. ", "Appendix ")
    if section == "TOC":
        section = "table of contents"

    # trailing period
    if len(section) > 1 and section[-1] == '.':
        section = section[:-1]
    return section


IgnoreSections = ["99", "global", "none", "", "index", "all", "n/a", "various"]
Reported = ["RFC0090", "RFC1033", "RFC2069", "RFC2821", "RFC3032", "RFC3696", "RFC3719",
            "RFC3810", "RFC4207", "RFC4301", "RFC5570", "RFC5663", "RFC6426"]

# RFC 5570 is missing section 5.1.4 and TOC is only two levels deep.
# RFC 4543 is missing a blank line between the TOC and the first section.
# RFC 4207 has a section 4.1.1 but not a section 4.1 or a TOC

# RFC 4302 - B2 is the appendix
# RFC 3696 - bad errata section # - augmented original text


class checker(object):
    def __init__(self, options, state):
        self.options = options
        self.state = state
        self.inlineCount = 0
        self.sectionCount = 0
        self.endnoteCount = 0
        self.connection = None

    # --- Download JSON file with errata data -------------------------

    def loadErrata(self):

        result = True
        if not self.options.no_network:
            if not self.downloadErrataFile():
                # Nothing to be done
                result = False

        with open("errata.json", encoding='utf-8') as f:
            self.errata = json.load(f)

        return result

    def filterErrata(self):

        # Gather together the set of errata we are going to emit

        byRfc = {}
        emitCodes = self.state["which"]
        # emitCodes = ["Verified", "Held"]

        for item in self.errata:
            item["section2"] = fixSection(item["section"]).lower()
            item["doc-id"] = 'rfc{0}'.format(int(item["doc-id"][3:]))

            if item["errata_status_code"] == "Held for Document Update":
                item["status_tag"] = "Held"
            else:
                item["status_tag"] = item["errata_status_code"]

            if not item["status_tag"] in emitCodes:
                continue

            if not item["doc-id"] in byRfc:
                byRfc[item["doc-id"]] = []

            byRfc[item["doc-id"]].append(item)
        self.byRfc = byRfc

    def processRFC(self, rfc, force, templates):
        if rfc not in self.byRfc:
            print("{0} does not have any current errata".format(rfc))
            return 0

        try:
            txt_file = os.path.join(self.state["text"], "{0}.txt".format(rfc))

            if not os.path.isfile(txt_file):
                retries = 3
                while retries:
                    try:
                        if not self.connection:
                            self.connection = HTTPSConnection(self.state["serverName"])

                        # print("RFC = {0}".format(rfc))
                        rfcNum = int(rfc[3:])
                        self.connection.request('GET', '/rfc/rfc{0}.txt'.format(rfcNum).lower())
                        res = self.connection.getresponse()
                        with open(txt_file, "wb") as f:
                            f.write(res.read())
                        retries = 0
                    except HTTPException as e:
                        if retries:
                            if self.options.verbose:
                                print("Close and reopen connection because '{0}'".format(e))

                            self.connection.close()
                            self.connection = None
                            retries -= 1
                        else:
                            errText = "Error '{1}' downloading 'errata.json' from '{0}'".format(self.state["serverName"], e)
                            if self.options.verbose:
                                print(errText)
                            with open("errors.log", "a") as f:
                                f.write(datetime.datetime.now().isoformat() + ": " + errText)
                            return 1

            x = apply_errata(self.byRfc[rfc], self.options, self.state)
            x.apply(force, templates)

            self.inlineCount += x.InlineCount
            self.sectionCount += x.SectionCount
            self.endnoteCount += x.EndnoteCount

            if x.EndnoteCount + x.SectionCount > 0 and self.options.verbose:
                print("{0}    {1}   {2}   {3}".format(rfc, x.InlineCount, x.SectionCount,
                                                      x.EndnoteCount))
                if rfc not in Reported:
                    for item in x.toApply:
                        if not item["section2"] in IgnoreSections:
                            print("        {0}  --> {1}".format(item["section"], item["section2"]))

            if "dest" in self.state and (x.InlineCount > 0 or x.SectionCount > 0 or x.EndnoteCount > 0):
                htmlFile = rfc + ".html"
                htmlSource = os.path.join(self.state["html"], htmlFile)
                for dest in self.state["dest"]:
                    shutil.copyfile(htmlSource, os.path.join(dest, htmlFile))

        except Exception as e:
            if self.options.verbose:
                print("Error processing {0}. {1}\n".format(rfc, e))
            with open("errors.log", "a") as f:
                f.write(datetime.datetime.now().isoformat() + ": Error processing {0}.  {1}\n".format(rfc, e))
            return 1
        return 0

    def processAllRfcs(self, templates):

        # create the output directories if needed

        byRfcOrdered = sorted(self.byRfc)
        errorCount = 0

        for rfc in byRfcOrdered:
            errorCount += self.processRFC(rfc, self.options.force, templates)
        return errorCount

    def printStats(self, errorCount):
        if self.options.verbose:
            allLines = self.inlineCount + self.sectionCount + self.endnoteCount
            if allLines == 0:
                allLines = 1
            print("Inline  = {0:4}     {1:2.2f}     4082".format(self.inlineCount,
                                                                 self.inlineCount/allLines*100))
            print("Section = {0:4}     {1:2.2f}      999".format(self.sectionCount,
                                                                 self.sectionCount/allLines*100))
            print("End     = {0:4}     {1:2.2f}      414".format(self.endnoteCount,
                                                                 self.endnoteCount/allLines*100))
            print("Total   = {0:4}".format(allLines))
            if errorCount > 0:
                print("Error Count: {0}".format(errorCount))

    def downloadErrataFile(self):
        try:
            self.connection = HTTPSConnection(self.state["serverName"])
            lastModified = None
            if os.path.exists("errata.json"):
                self.connection.request('HEAD', '/errata.json')
                res = self.connection.getresponse()
                if res.status != 200:
                    print("Error {0} for 'HEAD /errata.json' on '{1}'".format(res.status,
                                                                              self.state["serverName"]))
                    exit(1)
                res.read()

                lastModified = eut.parsedate_to_datetime(res.getheader("Last-Modified",
                                                                       "Mon, 22 Apr 2019 00:00:00 GMT"))
                if lastModified <= eut.parsedate_to_datetime(self.state["lastCheck"]):
                    if self.options.verbose:
                        print("errata.json is up to date.")
                        self.state["lastCheck"] = res.getheader("Last-Modified")
                    return False

            #  Should not eed to do this, but it doesn't work otherwise
            if self.options.verbose:
                print("downloading new copy of errata.json")
                if lastModified:
                    print("Old: {0}\nNew:{1}".format(self.state["lastCheck"], lastModified))

            retries = 2
            while retries:
                try:
                    if self.connection is None:
                        self.connection = HTTPSConnection(self.state["serverName"])
                    self.connection.request('GET', '/errata.json')
                    res = self.connection.getresponse()
                    if res.status != 200:
                        errText = "Error {0} for 'HEAD /errata.json' on '{1}'".format(res.status,
                                                                                      self.state["serverName"])
                        print(errText)
                        with open("errors.log", "a") as f:
                            f.write(datetime.datetime.now().isoformat() + ": " + errText)
                        exit(1)
                    with open("errata.json", "w") as f:
                        f.write(res.read().decode('utf-8').replace("\\r\\n", "\\n"))

                    if True:
                        with open("errata.json") as f:
                            data = json.load(f)

                        with open("errata.json", "w") as f:
                            json.dump(data, f, indent=2)

                    retries = 0
                    self.state["lastCheck"] = res.getheader("Last-Modified")
                except HTTPException as e:
                    if retries:
                        if self.options.verbose:
                            print("Close and reopen connection because '{0}'".format(e))

                        self.connection.close()
                        self.connection = None
                        retries -= 1
                    else:
                        errText = "Error '{1}' downloading 'errata.json' from '{0}'".format(self.state["serverName"], e)
                        if self.options.verbose:
                            print(errText)
                        with open("errors.log", "a") as f:
                            f.write(datetime.datetime.now().isoformat() + ": " + errText)
                        exit(1)
                except Exception as e:
                    errText = "Error '{1}' downloading 'errata.json' from '{0}'".format(self.state["serverName"], e)
                    if self.options.verbose:
                        print(errText)
                    with open("errors.log", "a") as f:
                        f.write(datetime.datetime.now().isoformat() + ": " + errText)
                    exit(1)

        except HTTPException as e:
            errText = "Error '{1}' downloading 'errata.json' from '{0}'".format(self.state["serverName"], e)
            if self.options.verbose:
                print(errText)
            with open("errors.log", "a") as f:
                f.write(datetime.datetime.now().isoformat() + ": " + errText)
            exit(1)
        return True
