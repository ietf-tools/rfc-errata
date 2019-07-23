import json
import sys
import os
import optparse
from Rfc_Errata.checker import checker
# from rfc2html import markup
from Rfc_Errata.template import Templates
from Rfc_Errata.__init__ import __version__


def display_version(self, opt, value, parser):
    print(__version__)
    sys.exit()


def writeState(stateIn):
    try:
        with open("status.json", 'w', encoding='utf-8') as f:
            json.dump(stateIn, f)
    except IOError:
        pass


def main2():
    # Populate options
    formatter = optparse.IndentedHelpFormatter(max_help_position=40)
    optionparser = optparse.OptionParser(usage='rfc-errata [OPTIONS] [<List of RFCs>]'
                                         '...\nExample: rfc-errata ',
                                         formatter=formatter)

    server_options = optparse.OptionGroup(optionparser, "Server Options")
    server_options.add_option("-s", "--server", dest='serverName',
                              help="specify the server to download from as DNS name")
    server_options.add_option("--no-network", action='store_true', default=False,
                              help='don\'t use the network to resolve references')
    optionparser.add_option_group(server_options)

    item_options = optparse.OptionGroup(optionparser, "Directory Options")
    item_options.add_option("--templates", help="Directory containing templates")
    item_options.add_option("--text", help="Directory to store text versions in")
    item_options.add_option("--html", help="Directory to store html versions in")
    item_options.add_option("--css", help="Directory containing CSS and JavaScript files")
    item_options.add_option("--copyto", action="append",
                            help="Specify a destination to copy the html file, may occur multiple times")
    item_options.add_option("--nocopy", action='store_true', help="Don't copy html files anywhere")
    optionparser.add_option_group(item_options)

    item_options = optparse.OptionGroup(optionparser, "Document Options")
    item_options.add_option("--all", help="Apply to all RFCs", action='store_true')
    item_options.add_option("--search", action='store_false', default=True,
                            help="Don't search for non-sectioned errata")
    item_options.add_option("--path", help="path to css files in HTML output")
    item_options.add_option("--reported", help="apply reported errata (yes/no)")
    item_options.add_option("--held", help="apply held for update errata (yes/no)")
    item_options.add_option("--verified", help="apply verified errata (yes/no)")
    item_options.add_option("--rejected", help="apply rejected errata (yes/no)")
    optionparser.add_option_group(item_options)

    item_options = optparse.OptionGroup(optionparser, "General Options")
    item_options.add_option('-v', '--verbose', action='store_true',
                            help='print extra information')
    item_options.add_option("--force", action='store_true',
                            help='Force regeneration of html files.')
    item_options.add_option('-V', '--version', action='callback', callback=display_version,
                            help='display the version number and exit')
    optionparser.add_option_group(item_options)

    # --- Parse and validate arguments ---------------------------------

    (options, args) = optionparser.parse_args()

    # --- Load status file --------------------------------------------

    try:
        with open("status.json", encoding='utf-8') as f:
            state = json.load(f)
    except IOError:
        state = {
            "serverName": "www.rfc-editor.org",
            "lastCheck": "Sun, 21 Apr 2019 00:00:00 GMT",
            "which": ["Verified", "Held"],
            "text": "./rfc",
            "html": "./html",
            "ossPath": "./css"
        }

    updateState = False

    if options.serverName and options.serverName != state["serverName"]:
        state["serverName"] = options.serverName
        updateState = True

    if options.templates and options.templates != state["templateDir"]:
        state["templateDir"] = options.templates
        updateState = True

    if options.text and options.text != state["textDir"]:
        state["textDir"] = options.text
        updateState = True

    if options.html and options.html != state["html"]:
        state["html"] = options.html
        updateState = True

    if options.path and options.path != state["cssPath"]:
        state["cssPath"] = options.path
        updateState = True

    if options.reported:
        if options.reported.lower() == "yes":
            if "Reported" not in state["which"]:
                state["which"].append("Reported")
                updateState = True
        elif options.reported.lower() == "no":
            if "Reported" in state["which"]:
                state["which"].remove("Reported")
                updateState = True
        else:
            print("Incorrect argument '{0}' given to reported".format(options.reported))
            exit(1)

    if options.held:
        if options.held.lower() == "yes":
            if "Held" not in state["which"]:
                state["which"].append("Held")
                updateState = True
        elif options.held.lower() == "no":
            if "Held" in state["which"]:
                state["which"].remove("Held")
                updateState = True
        else:
            print("Incorrect argument '{0}' given to held".format(options.held))
            exit(1)

    if options.verified:
        if options.verified.lower() == "yes":
            if "Verified" not in state["which"]:
                state["which"].append("Verified")
                updateState = True
        elif options.verified.lower() == "no":
            if "Verified" in state["which"]:
                state["which"].remove("Verified")
                updateState = True
        else:
            print("Incorrect argument '{0}' given to verified".format(options.verified))
            exit(1)

    if options.rejected:
        if options.rejected.lower() == "yes":
            if "Rejected" not in state["which"]:
                state["which"].append("Rejected")
                updateState = True
        elif options.rejected.lower() == "no":
            if "Rejected" in state["which"]:
                state["which"].remove("Rejected")
                updateState = True
        else:
            print("Incorrect argument '{0}' given to rejected".format(options.rejected))
            exit(1)

    if options.nocopy:
        if options.copyto:
            print("copyto and no copy options are mutually exclusive")
            exit(1)
        state.remove("dest")
        updateState = True

    if options.copyto:
        state["dest"] = options.copyto
        updateState = True

    check = checker(options, state)

    if check.loadErrata():
        updateState = True
    check.filterErrata()

    #  Create directories if needed

    if not os.path.isdir(state["text"]):
        os.mkdir(state["text"])
    if not os.path.isdir(state["html"]):
        os.mkdir(state["html"])

    if "templateDir" in state:
        templates_path = state["templateDir"]
    else:
        templates_path = os.path.join(os.path.dirname(__file__), "Template")
    templates = Templates(templates_path)

    errorCount = 0
    if options.all:
        errorCount = check.processAllRfcs(templates)
    else:
        for rfc in args:
            rfc = rfc.upper()
            if not rfc.startswith("RFC"):
                if rfc.isdigit():
                    rfc = "RFC" + rfc
                else:
                    print("Only RFCs can be provided for update.  Use RFCXXXX")

            errorCount += check.processRFC(rfc, options.force, templates)
            # if False:
            #    with open('rfc/' + rfc + '.txt') as f:
            #        text = f.read()
            #    html = markup(text)
            #    with open('html2/' + rfc + '.html', "w") as f:
            #        f.write(html)

    check.printStats(errorCount)

    if updateState:
        writeState(state)
    exit(errorCount)


def main():
    try:
        main2()
    except Exception as e:
        with open("errors.log", "a") as f:
            f.write("Error while process:\n{0}\n".format(e))
        exit(1)


if __name__ == '__main__':
    major, minor = sys.version_info[:2]
    if major == 2 and minor < 7:
        print("")
        print("The rfclint script requires python 2, with a version of 2.7 or higher.")
        print("Can't proceed, quitting.")
        exit()

    main()
