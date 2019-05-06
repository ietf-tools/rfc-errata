import re
import os
import html
from datetime import datetime
from utils import strip_pagebreaks

order = {"Verified": 1, "Held": 2, "Reported": 3, "Rejected": 4}


def inlineSectionKey(data):
    return "{0}||{2}||{1}".format(data["section2"], data["errata_id"], order[data["status_tag"]])


def inlineKey(data):
    return "{0}||{1}||{2}||{4}||{3}".format(data[0]["section2"], data[1].start, data[1].end,
                                            data[0]["errata_id"], order[data[0]["status_tag"]])


def sortById(data):
    return "{0:6}".format(data["errata_id"])


def increment(tag):
    if tag[0].isdigit():
        return str(int(tag)+1)
    if not tag[-1].isdigit():
        tag = tag[:-1] + chr(ord(tag[-1])+1)
        return tag
    i = len(tag)-1
    while tag[i].isdigit():
        i -= 1
    return tag[:i] + str(int(tag[i:])+1)


startTime = datetime(1970, 1, 1)


class apply_errata(object):
    def __init__(self, toBeApplied, options, state):
        self.header_re = re.compile(u'$('
                                    u'\d+(\.\d+)*\.?|'         # 1.1.1
                                    u'\w(\.\d+)*\.?|'          # A.1.1
                                    u'Appendix \w(\.\d+)*\.?)'  # Appendix A.1.1.1
                                    )

        # Section "1.0"
        self.header_re1 = re.compile("\d+(\.\d+)*\.? |Appendix \w(\.\d+)*[\.:]? |\w(\.\d+)*[\.:]? ")
        self.header_re2 = re.compile("(\s*)\d+(\.\d+)*\.? |(\s*)Appendix \w(\.\d+)*[\.:]? " +
                                     "|(\s*)\w(\.\d+)*\.? ")
        self.header_re = self.header_re2
        self.InlineCount = 0
        self.SectionCount = 0
        self.EndnoteCount = 0
        self.toApply = toBeApplied
        self.title = toBeApplied[0]["doc-id"]
        self.options = options
        self.state = state

        # Strings used in the process

        self.inlineFormat = "<span class=\"{0}-inline-styling\" id='inline-{1}'>{2}</span id__locate={1}>"
        self.inlineExpandWrapper = "<div class=\"nodeCloseClass\" id='expand_{0}'>{1}</div>"
        self.buttonFormat = " <button id=\"btn_{0}\" target=\"expand_{0}\" onclick='hideFunction(\"expand_{0}\")'>Expand</button>\n"

    def apply(self, force, templates):
        self.RfcName = self.toApply[0]["doc-id"]
        fileName = "rfc/" + self.RfcName + ".txt"
        htmlFile = "html/" + self.RfcName + ".html"

        self.templates = templates

        if not force and os.path.exists(htmlFile):
            statIfno = os.stat(htmlFile)

            update = False
            for item in self.toApply:
                updateTime = item["update_date"]
                if not updateTime:
                    updateTime = item["submit_date"]
                    if not updateTime:
                        continue
                    else:
                        itemUpdate = datetime.strptime(updateTime, "%Y-%m-%d")
                else:
                    itemUpdate = datetime.strptime(updateTime, "%Y-%m-%d %H:%M:%S")

                itemUpdate = (itemUpdate - startTime).total_seconds()
                if itemUpdate > statIfno.st_mtime:
                    update = True
                    break

            if not update:
                return

        #  Open the source file and read in.

        OldFormat = ["RFC1633", "RFC2136", "RFC2328", "RFC2361"]

        if False:
            if int(self.RfcName[3:]) > 1350 and self.RfcName not in OldFormat:
                self.header_re = self.header_re1
            else:
                self.header_re = self.header_re2

        self.buildHeader()

        self.loadDocument(fileName)

        self.sectionDocument()

        self.createInlineNotes()

        self.createSectionNotes()

        self.unsectionDocument()
        self.createFootnotes()
        self.emitHtml()

    def loadDocument(self, fileName):
        try:
            with open(fileName, "r", encoding='utf-8') as f:
                text = f.read()
        except UnicodeDecodeError:
            with open(fileName, "r") as f:
                text = f.read()

        # Do the the first set of simple changes
        # 1.  Strip page headers/footer and page-feed
        # 2.  ?????

        # Import the method from id2xml

        a, shortTitle = strip_pagebreaks(text)

        self.source = [x.txt for x in a]
        self.source = "\n".join(self.source).splitlines(True)

        # Figure out what the indent level is

        indent = 72
        pattern = re.compile("^( *)")
        for line in self.source:
            if len(line) == 1:
                continue
            match = pattern.match(line)
            if match:
                i = len(match.group(0))
                if i < indent:
                    indent = i
                    if indent == 0:
                        break

        if indent > 0:
            newSource = []
            for line in self.source:
                if len(line) > 1:
                    newSource.append(line[indent:])
                else:
                    newSource.append(line)

            self.source = newSource

    def addToKnowns(self, section):
        section = section.lower()
        if section not in self.knownSections:
            self.knownSections.append(section)

    def parseTOC(self, lineNo):
        # Different people have different styles for TOCs.  The new ones are easy to parse, but the
        # old ones are a total mess
        #  Old ones may have spaces in them so it makes the logic slightly harder

        if self.source[lineNo][0] != ' ':
            return lineNo

        lineNo += 1
        self.header_re = self.header_re2
        while lineNo < len(self.source):
            m = re.match("\s*1(.0)?", self.source[lineNo])
            if m:
                return lineNo + 1
            lineNo += 1
        return lineNo

    def isSectionStart(self, line, i):
        if line.strip().lower() in self.knownSections:
            if line.strip().lower() == "table of contents":
                return line.strip().lower(), False
            return line.strip().lower(), True

        header = self.header_re.match(line)
        if not header:
            return None, True

        potentialSection = header.group(0).strip().lower()

        lpad = len(line) - len(line.lstrip(' '))

        if potentialSection[-1] == '.' or potentialSection[-1] == ':':
            potentialSection = potentialSection[:-1]

        if len(potentialSection) > 2 and potentialSection[-2:] == '.0':
            potentialSection = potentialSection[:-2]

        if "..." in line or ". ." in line:
            self.tocSections.append(potentialSection)
            return None, False

        if potentialSection not in self.knownSections:
            if potentialSection not in self.tocSections:
                return None, True

        if potentialSection == '1':
            self.addToKnowns('a')

        frags = potentialSection.split('.')
        if len(frags) > 1 and self.sectionIndent is None:
            if frags[-1] == '1':
                self.sectionIndent = lpad
            else:
                self.sectionIndent = 0
        if len(frags) > 1:
            if self.sectionIndent and lpad != self.sectionIndent * (len(frags)-1):
                return None, True
            elif self.sectionIndent is None:
                    return None, True
        elif lpad > 0:
            return None, True

        if potentialSection in self.knownSections:
            self.knownSections.remove(potentialSection)

        # Remove items from the known set
        # For X.Y
        # Remove X.Y
        # Remove X.Y-1(.*)
        # Remove X-1.(.*)

        # Add items to the known set
        # For X.Y add
        # X+1 for Y=0 or absent
        # X.Y+1
        # X.Y.1to-
        # if X is "Appendix Z"
        # Appendix Z+1
        # Z.1

        if frags[-1] == '':
            frags = frags[:-1]
        if frags[-1] == '0':
            frags = frags[:-1]

        # --> X+1
        self.addToKnowns(increment(frags[0]))

        frags.append("1")
        self.addToKnowns('.'.join(frags))
        if len(frags) > 2:
            frags2 = frags[:-2]
            frags2.append(increment(frags[-2]))
            self.addToKnowns('.'.join(frags2))

        match = re.match("appendix (\w)", potentialSection)
        if match:
            frags = [match.group(1), '1']
            self.addToKnowns('.'.join(frags))
        return potentialSection, True

    def sectionDocument(self):
        # doc = SectionDocument(self.source)
        # doc.getSections()
        # self.allSections = doc.sectionList
        # self.sectionDict = doc.sectionDict

        self.sectionIndent = None
        self.centeredTitle = None

        self.knownSections = ["status of this memo", "copyright notice", "abstract",
                              "table of contents",
                              "1", "appendix a", "appendix i", "appendix 1",
                              "acknowledgements", "acknowledgments", "authors' addresses",
                              "author's address",
                              "full copyright statement", "security considerations"]
        self.currentSection = "Header"
        self.startLine = 0
        self.allSections = []
        self.sectionDict = {}
        self.tocSections = []

        i = 0
        while i < len(self.source):
            if self.source[i].strip() == "":
                i += 1
                continue

            isStart, skipBlock = self.isSectionStart(self.source[i], i)
            if isStart:
                self.currentSection = self.currentSection.lower().rstrip()
                self.allSections.append(self.currentSection)
                self.sectionDict[self.currentSection] = self.source[self.startLine:i]
                self.currentSection = isStart
                self.startLine = i

            if not skipBlock:
                i += 1
            else:
                while i < len(self.source) and self.source[i].strip() != "":
                    i += 1

        self.currentSection = self.currentSection.lower().rstrip()
        self.allSections.append(self.currentSection)
        self.sectionDict[self.currentSection] = self.source[self.startLine:i]

    def unsectionDocument(self):
        sections = []
        for header in self.allSections:
            sections.extend(self.sectionDict[header])
        self.source = sections

    def buildPattern(self, string):
        #  \u200C   ---- 3312 - RFC 5892  --- zero width non-joiner
        #  \u2019   ---- 5178 - RFC 6218  --- right single quotation mark
        #  \u2026   ---- 1117 - RFC 4601  --- ... - ellipsis
        #  \u2014   ---- 4483 - RFC 5952  --- emdash

        string = string.replace("\u2018", "'").replace("\u201B", "'"). \
                 replace('\u2019', "'").replace('\u201C', "'"). \
                 replace("\u201C", '"').replace('\u201D', '"')

        string = html.escape(string)

        for ch in ['\\', '`', '*', '+', '?', '(', ')', '=', '[', ']', '.', '{', '}', '~', '$', '^', '|', '-']:
            if ch in string:
                string = string.replace(ch, "\\"+ch)

        string = string.strip()
        string = re.sub("\s+", "\\s+", string)
        return re.compile(string)

    def buildPattern2(self, item):
        oldTextIn = item["orig_text"]
        if "..." in oldTextIn:
            m = re.match("\s*\[?\.\.\.\]?", oldTextIn)
            if m:
                oldTextIn = oldTextIn[m.end():]
            m = re.search("\[?\.\.\.\]?\s*$", oldTextIn)
            if m:
                oldTextIn = oldTextIn[:m.start()]

        lines, a = strip_pagebreaks(oldTextIn)
        if len(lines) == 0:
            return None

        
        newLines = []
        for line in lines:
            line = line.txt
            if len(line) > 0 and line[0] == '|':
                line = line[1:]
            match = re.match("\s*\^+\s*$", line)
            if match:
                line = None
            else:
                newLines.append(line)

        oldText = "\n".join(newLines)

        newText = item["correct_text"]
        if newText:
            lines, a = strip_pagebreaks(newText)
            newLines = []
            for line in lines:
                line = line.txt
                if len(line) > 0 and line[0] == '|':
                    line = line[1:]
                match = re.match("\s*\^+\s*$", line)
                if match:
                    line = None
                else:
                    newLines.append(line)

            newText = "\n".join(newLines)

        if oldText == oldTextIn:
            return None
        item["orig_text2"] = oldText
        item["correct_text2"] = newText
        return self.buildPattern(oldText)

    def buildInlines(self, section, itemList, searchText):

        # print("section = {0}   Number of inserts = {1}".format(section, len(itemList)))
        # print("original:\n{0}".format(searchText))

        editedText = searchText
        locations = []

        for item in itemList:
            match = re.search(item[2], editedText)
            # print("pattern = {0}".format(item[2]))
            if match:
                # M00BUG - Pick up corrrect_test2 here
                newText = item[0]["orig_text"] if item[0]["status_tag"] == "Rejected" else item[0]["correct_text"]
                editedText = editedText[:match.start()] +  \
                    self.inlineFormat.format(item[0]["status_tag"], item[0]["errata_id"], newText) + \
                    editedText[match.end():]
                locations.append([item, item[1].start(), item[1].end(), False])

        sectionLines = editedText.splitlines(True)

        for item in itemList:
            for loc in locations:
                if item == loc[0]:
                    item[3] = True
                    endTag = re.compile("id__locate={0}".format(item[0]["errata_id"]))
                    startTag = re.compile("inline-{0}".format(item[0]["errata_id"]))
                    self.header = self.header.replace("#eid{0}".format(item[0]["errata_id"]),
                                                      "#btn_{0}".format(item[0]["errata_id"]))
                    for line in range(len(sectionLines)):
                        m = startTag.search(sectionLines[line])
                        if m:
                            sectionLines[line] = sectionLines[line][:-1] + self.buttonFormat.format(item[0]["errata_id"])
                        m = endTag.search(sectionLines[line])
                        if m:
                            sectionLines.insert(line+1, self.inlineExpandWrapper.format(item[0]["errata_id"],
                                                                                        self.templates.inlineNote.substitute(item[0])))
                            break

        button = re.compile("Expand</button")
        for item in itemList:
            if item[3]:
                continue
            for locate in locations:
                if locate[1] > item[1].end() or locate[2] < item[1].start():
                    continue
                expandTag = re.compile("id='expand_{0}".format(locate[0][0]["errata_id"]))
                self.header = self.header.replace("#eid{0}".format(item[0]["errata_id"]),
                                                  "#btn_{0}".format(locate[0][0]["errata_id"]))
                for line in range(len(sectionLines)):
                    m = expandTag.search(sectionLines[line])
                    if m:
                        if sectionLines[line][-6:] != "</div>":
                            print("Internal Error")
                            break
                        sectionLines[line] = sectionLines[line][:-6] + \
                            self.templates.inlineNote.substitute(item[0]) + "</div>"
                        break
                    m = button.search(sectionLines[line])
                    if m:
                        sectionLines[line] = sectionLines[line][:m.start()] + \
                                                "Expand Multiple</button" + \
                                                sectionLines[line][m.end():]

        # print("**result:\n{0}**".format("".join(sectionLines)))
        self.sectionDict[section] = sectionLines

    def createInlineNotes(self):

        combinedLines = {}
        combinedLine = ""
        for section in self.sectionDict:
            combinedLines[section] = html.escape("".join(self.sectionDict[section]))
            self.sectionDict[section] = combinedLines[section].splitlines(True)

        if self.options.search:
            for item in self.toApply:
                section = item["section2"]
                if section in self.allSections:
                    continue
                if section[:9] == "appendix ":
                    test = section[9:]
                    if test in self.allSections:
                        item["section2"] = test
                        continue
                if len(section) > 0 and section[0].isalpha():
                    test = "appendix " + section
                    if test in self.allSections:
                        item["section2"] = test
                        continue

                if not item["orig_text"]:
                    continue

                pattern = self.buildPattern(item["orig_text"])
                pattern2 = self.buildPattern2(item)
                for section in self.sectionDict:
                    match = pattern.search(combinedLines[section])
                    if match:
                        item["section2"] = section
                        break

                    if pattern2:
                        match = pattern2.search(combinedLines[section])
                        if match:
                            item["section2"] = section
                            break

        ids = sorted(self.toApply, key=inlineSectionKey)

        putInline = []
        lastSection = ids[0]["section2"]

        for id in ids:
            item = id

            # nothing to be matched
            if not item["orig_text"]:
                continue

            section = item["section2"]
            if section not in self.allSections:
                continue

            if section != lastSection:
                self.buildInlines(lastSection, putInline, combinedLine)
                lastSection = section
                putInline = []

            combinedLine = combinedLines[section]
            pattern = self.buildPattern(item["orig_text"])

            match = pattern.search(combinedLine)
            if match:
                # print("*** FOUND PATTERN - section {0}".format(section))
                # print(pattern)
                self.toApply.remove(item)
                self.InlineCount += 1
                putInline.append([item, match, pattern, False])
            else:
                pattern2 = self.buildPattern2(item)
                if pattern2 is None:
                    continue
                match = pattern2.search(combinedLine)
                if match:
                    self.toApply.remove(item)
                    self.InlineCount += 1
                    putInline.append([item, match, pattern2, False])
                else:
                    # print("*** FAILED PATTERN - section {0}".format(section))
                    # print(pattern)
                    # print(item["orig_text"])
                    pass

        self.buildInlines(lastSection, putInline, combinedLine)

    def createSectionNotes(self):
        # M00BUG title continutations

        ids = sorted([item["errata_id"] for item in self.toApply])
        byId = dict((item["errata_id"], item) for item in self.toApply)

        for id in ids:
            item = byId[id]
            if not item["section2"] in self.allSections:
                continue

            text = self.templates.sectionNote.substitute(item)

            section = self.sectionDict[item["section2"]]
            section = section[:2] + [text] + section[2:]
            self.sectionDict[item["section2"]] = section
            self.toApply.remove(item)

            self.SectionCount += 1

    def createFootnotes(self):
        errataFooter = ""

        ids = sorted(self.toApply, key=sortById)

        for item in ids:
            if "notes" in item and item["notes"]:
                item["notes"] = item["notes"].replace("\n", "<br/>")

            errataFooter += self.templates.endNote.substitute(item)
            self.EndnoteCount += 1

        self.errataFooter = errataFooter

    def buildHeader(self):
        anchorTemplate = " <a href='#eid{0}'>Errata {0}</a>, "

        ids = sorted(self.toApply, key=sortById)

        errataHeader = {}
        for item in ids:
            code = item["status_tag"]
            item["errata_id"] = str(item["errata_id"])

            if code not in errataHeader:
                errataHeader[code] = {"status_tag": code, "errata_list": ""}

            errataHeader[code]["errata_list"] += anchorTemplate.format(item["errata_id"])

        header = ""
        for keys in ["Verified", "Held", "Reported", "Rejected"]:
            if keys in errataHeader:
                errataHeader[keys]["errata_list"] = errataHeader[keys]["errata_list"][:-2]
                header += self.templates.headNote.substitute(errataHeader[keys])
        self.header = header

    def emitHtml(self):

        fields = {}
        fields["HEADER"] = self.header
        fields["PATH"] = self.state["ossPath"]
        fields["BODY"] = "".join(self.source)
        fields["FOOTER"] = self.errataFooter
        fields["TITLE"] = self.title

        with open(os.path.join(self.state["html"], self.RfcName + ".html"), "w", encoding='utf-8') as f:
            f.write(self.templates.html.substitute(fields))
