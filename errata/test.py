import pycodestyle
# import platform
import unittest
import os
# import shutil
import sys
import subprocess
import difflib
import six
import json
from template import Templates

from apply_errata import apply_errata
from optparse import Values

test_program = "rfc-errata"


def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file
    return None


class Test_Coding(unittest.TestCase):
    def test_pycodestyle_conformance(self):
        """Test that we conform to PEP8."""
        pep8style = pycodestyle.StyleGuide(quiet=False, config_file="pycode.cfg")
        result = pep8style.check_files(['run.py', 'apply_errata.py', 'checker.py',
                                        'template.py', 'test.py', 'utils.py'])
        self.assertEqual(result.total_errors, 0,
                         "Found code style errors (and warnings).")

    def test_pyflakes_confrmance(self):
        p = subprocess.Popen(['pyflakes', 'run.py', 'apply_errata.py', 'checker.py',
                              'template.py', 'test.py', 'utils.py'],
                             stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        (stdoutX, stderrX) = p.communicate()
        ret = p.wait()
        if ret > 0:
            stdoutX = stdoutX.decode('utf-8')
            stderrX = stderrX.decode('utf-8')
            print(stdoutX)
            print(stderrX)
            self.assertEqual(ret, 0)


class TestCommandLineOptions(unittest.TestCase):
    """ Run a set of command line checks to make sure they work """
    def test_get_version(self):
        check_process(self, [sys.executable, test_program, "--version"],
                      "Results/version.out", "Results/empty.txt",
                      None, None)


class TestSection(unittest.TestCase):
    """ Run a set of sectioning tests to make sure nothing changes """
    # Other files 2648, 3447, 4207, 5570, 7530, 8095, 8095

    def test_section_RFC793(self):
        errata = [{"doc-id": "RFC0793"}]
        doc = apply_errata(errata, None, None)
        doc.loadDocument("Tests/RFC793.txt")

        preDoc = "".join(doc.source)
        doc.sectionDocument()

        expectedSections = ["header", "table of contents",
                            "1.1", "1.2", "1.3", "1.4", "1.5",
                            "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8",
                            "2.9", "2.10",
                            "3.1", "3.2", "3.3",
                            "3.4", "3.5", "3.6", "3.7", "3.8", "3.9"]

        self.assertSequenceEqual(doc.allSections, expectedSections)
        doc.unsectionDocument()
        postDoc = "".join(doc.source,)
        self.assertEqual(preDoc, postDoc)

    def test_section_RFC822(self):
        errata = [{"doc-id": "RFC0822"}]
        doc = apply_errata(errata, None, None)
        doc.loadDocument("Tests/RFC822.txt")
        doc.sectionDocument()

        expectedSections = ["header", "table of contents",
                            "1", "1.1", "1.2",
                            "2", "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7", "2.8",
                            "3", "3.1", "3.1.1", "3.1.2", "3.1.3", "3.1.4", "3.2", "3.3",
                            "3.4", "3.4.1", "3.4.2", "3.4.3", "3.4.4", "3.4.5", "3.4.6",
                            "3.4.7", "3.4.8", "3.4.9", "3.4.10",
                            "4", "4.1", "4.2", "4.3", "4.3.1", "4.3.2",
                            "4.4", "4.4.1", "4.4.2", "4.4.3", "4.4.4",
                            "4.5", "4.5.1", "4.5.2", "4.5.3",
                            "4.6", "4.6.1", "4.6.2", "4.6.3", "4.6.4",
                            "4.7", "4.7.1", "4.7.2", "4.7.3", "4.7.4", "4.7.5",
                            "5", "5.1", "5.2",
                            "6", "6.1", "6.2", "6.2.1", "6.2.2", "6.2.3", "6.2.4", "6.2.5", "6.2.6",
                            "6.2.7", "6.3", "7",
                            "a", "a.1", "a.1.1", "a.1.2", "a.1.3", "a.1.4", "a.1.5",
                            "a.2", "a.2.1", "a.2.2", "a.2.3", "a.2.4", "a.2.5", "a.2.6", "a.2.7",
                            "a.3", "a.3.1", "a.3.2", "a.3.3",
                            "b", "b.1", "b.2",
                            "c", "c.1", "c.1.1", "c.2", "c.2.1", "c.2.2", "c.2.3", "c.2.4",
                            "c.3", "c.3.1", "c.3.2", "c.3.3", "c.3.4", "c.3.5", "c.3.6", "c.3.7",
                            "c.3.8", "c.4", "c.4.1", "c.5", "c.5.1", "c.5.2", "c.5.3",
                            "c.5.4", "c.5.5", "c.5.6", "c.6", "d"]

        self.assertSequenceEqual(doc.allSections, expectedSections)

    def test_section_RFC854(self):
        errata = [{"doc-id": "RFC0854"}]
        doc = apply_errata(errata, None, None)
        doc.loadDocument("Tests/RFC854.txt")
        doc.sectionDocument()

        expectedSections = ["header"]

        self.assertSequenceEqual(doc.allSections, expectedSections)

    def test_section_RFC1122(self):
        errata = [{"doc-id": "RFC1122"}]
        doc = apply_errata(errata, None, None)
        doc.loadDocument("Tests/RFC1122.txt")
        doc.sectionDocument()
        # self.maxDiff = None

        expectedSections = ["header", "status of this memo", "table of contents",
                            "1", "1.1", "1.1.1", "1.1.2", "1.1.3", "1.1.4", "1.2", "1.2.1", "1.2.2",
                            "1.2.3", "1.2.4", "1.3", "1.3.1", "1.3.2", "1.3.3", "1.4",
                            "2", "2.1", "2.2", "2.3", "2.3.1", "2.3.2", "2.3.2.1", "2.3.2.2",
                            "2.3.3", "2.4", "2.5",
                            "3", "3.1", "3.2", "3.2.1", "3.2.1.1", "3.2.1.2", "3.2.1.3", "3.2.1.4",
                            "3.2.1.5", "3.2.1.6", "3.2.1.7", "3.2.1.8", "3.2.2", "3.2.2.1",
                            "3.2.2.2", "3.2.2.3", "3.2.2.4", "3.2.2.5", "3.2.2.6",
                            "3.2.2.7", "3.2.2.8", "3.2.2.9", "3.2.3",
                            "3.3", "3.3.1", "3.3.1.1", "3.3.1.2", "3.3.1.3", "3.3.1.4", "3.3.1.5",
                            "3.3.1.6", "3.3.2", "3.3.3", "3.3.4", "3.3.4.1", "3.3.4.2", "3.3.4.3",
                            "3.3.5", "3.3.6", "3.3.7", "3.3.8",
                            "3.4", "3.5",
                            "4", "4.1", "4.1.1", "4.1.2", "4.1.3", "4.1.3.1", "4.1.3.2", "4.1.3.3",
                            "4.1.3.4", "4.1.3.5", "4.1.3.6", "4.1.4", "4.1.5",
                            "4.2", "4.2.1", "4.2.2", "4.2.2.1", "4.2.2.2", "4.2.2.3", "4.2.2.4",
                            "4.2.2.5", "4.2.2.6", "4.2.2.7", "4.2.2.8", "4.2.2.9", "4.2.2.10",
                            "4.2.2.11", "4.2.2.12", "4.2.2.13", "4.2.2.14", "4.2.2.15", "4.2.2.16",
                            "4.2.2.17", "4.2.2.18", "4.2.2.19", "4.2.2.20", "4.2.2.21",
                            "4.2.3", "4.2.3.1", "4.2.3.2", "4.2.3.3", "4.2.3.4", "4.2.3.5",
                            "4.2.3.6", "4.2.3.7", "4.2.3.8", "4.2.3.9", "4.2.3.10", "4.2.3.11",
                            "4.2.3.12", "4.2.4", "4.2.4.1", "4.2.4.2", "4.2.4.3", "4.2.4.4",
                            "4.2.5",
                            "5", "security considerations", "author's address"]

        self.assertSequenceEqual(doc.allSections, expectedSections)

    def test_section_RFC1322(self):
        errata = [{"doc-id": "RFC1322"}]
        doc = apply_errata(errata, None, None)
        doc.loadDocument("Tests/RFC1322.txt")
        doc.sectionDocument()
        # self.maxDiff = None

        expectedSections = ["header", "status of this memo", "abstract",
                            "1", "1.1", "1.2",
                            "2", "2.1", "2.1.1", "2.1.2", "2.1.3", "2.2", "2.3", "2.3.1", "2.3.2",
                            "2.4", "2.5", "2.6",
                            "3", "3.1", "3.2", "3.2.1",
                            "3.3", "3.3.1", "3.3.2", "3.3.3",
                            "3.4", "3.5", "3.6", "3.7", "3.8",
                            "4", "4.1",
                            "4.2", "4.2.1", "4.2.2", "4.3",
                            "5", "5.1", "5.2", "6", "7", "8", "security considerations",
                            "authors' addresses"]

        self.assertSequenceEqual(doc.allSections, expectedSections)

    def test_section_RFC4543(self):
        errata = [{"doc-id": "RFC4543"}]
        doc = apply_errata(errata, None, None)
        doc.loadDocument("Tests/RFC4543.txt")
        doc.sectionDocument()
        self.maxDiff = None

        expectedSections = ["header", "status of this memo", "copyright notice", "abstract",
                            "table of contents", "1", "1.1", "2", "3", "3.1", "3.2", "3.3",
                            "3.4", "3.5", "3.6", "4", "5", "5.1", "5.2", "5.3", "5.4",
                            "6", "7", "8", "9", "10", "11", "11.1", "11.2",  "authors' addresses",
                            "full copyright statement"]

        self.assertSequenceEqual(doc.allSections, expectedSections)


class TestInline(unittest.TestCase):
    """ Do the application of inline code to get things right """
    def test_one(self):
        with open("Tests/inline-one.json") as f:
            errata = json.load(f)
        if not os.exists("Temp"):
            os.mkdir("Temp")
        state = {"text": "./Tests", "html": "./Temp", "ossPath": "css"}
        options = Values(defaults={'search': False})

        doc = apply_errata(errata, options, state)

        templates = Templates(os.path.join(os.path.dirname(__file__), "Template"))

        doc.apply(True, templates)

        self.assertEqual(doc.InlineCount, 1)
        self.assertEqual(doc.SectionCount, 0)
        self.assertEqual(doc.EndnoteCount, 0)

        self.assertTrue(compare_file("./Temp/RFC8275.html", "./Results/inline-one.html", True))

    def test_two(self):
        with open("Tests/inline-two.json") as f:
            errata = json.load(f)
        if not os.exists("Temp"):
            os.mkdir("Temp")
        state = {"text": "./Tests", "html": "./Temp", "ossPath": "css"}
        options = Values(defaults={'search': False})

        doc = apply_errata(errata, options, state)

        templates = Templates(os.path.join(os.path.dirname(__file__), "Template"))

        doc.apply(True, templates)

        self.assertEqual(doc.InlineCount, 2)
        self.assertEqual(doc.SectionCount, 0)
        self.assertEqual(doc.EndnoteCount, 0)

        self.assertTrue(compare_file("./Temp/RFC8275.html", "./Results/inline-two.html", True))

    def test_three(self):
        with open("Tests/inline-three.json") as f:
            errata = json.load(f)
        if not os.exists("Temp"):
            os.mkdir("Temp")
        state = {"text": "./Tests", "html": "./Temp", "ossPath": "css"}
        options = Values(defaults={'search': False})

        doc = apply_errata(errata, options, state)

        templates = Templates(os.path.join(os.path.dirname(__file__), "Template"))

        doc.apply(True, templates)

        self.assertEqual(doc.InlineCount, 2)
        self.assertEqual(doc.SectionCount, 0)
        self.assertEqual(doc.EndnoteCount, 0)

        self.assertTrue(compare_file("./Temp/RFC8275.html", "./Results/inline-three.html", True))

    def test_four(self):
        with open("Tests/inline-four.json") as f:
            errata = json.load(f)
        if not os.exists("Temp"):
            os.mkdir("Temp")
        state = {"text": "./Tests", "html": "./Temp", "ossPath": "css"}
        options = Values(defaults={'search': False})

        doc = apply_errata(errata, options, state)

        templates = Templates(os.path.join(os.path.dirname(__file__), "Template"))

        doc.apply(True, templates)

        self.assertEqual(doc.InlineCount, 2)
        self.assertEqual(doc.SectionCount, 0)
        self.assertEqual(doc.EndnoteCount, 0)

        self.assertTrue(compare_file("./Temp/RFC8275.html", "./Results/inline-four.html", True))

    def test_five(self):
        with open("Tests/inline-five.json") as f:
            errata = json.load(f)
        if not os.exists("Temp"):
            os.mkdir("Temp")
        state = {"text": "./Tests", "html": "./Temp", "ossPath": "css"}
        options = Values(defaults={'search': False})

        doc = apply_errata(errata, options, state)

        templates = Templates(os.path.join(os.path.dirname(__file__), "Template"))

        doc.apply(True, templates)

        self.assertEqual(doc.InlineCount, 2)
        self.assertEqual(doc.SectionCount, 0)
        self.assertEqual(doc.EndnoteCount, 0)

        self.assertTrue(compare_file("./Temp/RFC8275.html", "./Results/inline-five.html", True))

    def test_six(self):
        with open("Tests/inline-six.json") as f:
            errata = json.load(f)
        if not os.exists("Temp"):
            os.mkdir("Temp")
        state = {"text": "./Tests", "html": "./Temp", "ossPath": "css"}
        options = Values(defaults={'search': False})

        doc = apply_errata(errata, options, state)

        templates = Templates(os.path.join(os.path.dirname(__file__), "Template"))

        doc.apply(True, templates)

        self.assertEqual(doc.InlineCount, 2)
        self.assertEqual(doc.SectionCount, 0)
        self.assertEqual(doc.EndnoteCount, 0)

        self.assertTrue(compare_file("./Temp/RFC8275.html", "./Results/inline-six.html", True))

    def test_seven(self):
        with open("Tests/inline-seven.json") as f:
            errata = json.load(f)
        if not os.exists("Temp"):
            os.mkdir("Temp")
        state = {"text": "./Tests", "html": "./Temp", "ossPath": "css"}
        options = Values(defaults={'search': False})

        doc = apply_errata(errata, options, state)

        templates = Templates(os.path.join(os.path.dirname(__file__), "Template"))

        doc.apply(True, templates)

        self.assertEqual(doc.InlineCount, 2)
        self.assertEqual(doc.SectionCount, 0)
        self.assertEqual(doc.EndnoteCount, 0)

        self.assertTrue(compare_file("./Temp/RFC8275.html", "./Results/inline-seven.html", True))


def compare_file2(errFile, stderr, displayError):
    with open(stderr, 'rb') as f:
        stderr = f.read()
    if six.PY2:
        lines1 = stderr.decode('utf-8')
    else:
        lines1 = stderr
    return compare_file(errFile, lines1, displayError)


def compare_file(errFile, stderr, displayError):
    if six.PY2:
        with open(errFile, 'r') as f:
            lines2 = f.readlines()
        lines1 = stderr.splitlines(True)
    else:
        with open(errFile, 'r', encoding='utf8') as f:
            lines2 = f.readlines()
        if isinstance(stderr, str):
            with open(stderr, 'rb') as f:
                stderr = f.read()
        lines1 = stderr.decode('utf-8').splitlines(True)

    if os.name == 'nt':
        lines2 = [line.replace('Tests/', 'Tests\\') for line in lines2]
        lines1 = [line.replace('\r', '') for line in lines1]

    cwd = os.getcwd()
    if os.name == 'nt':
        cwd = cwd.replace('\\', '/')
    lines2 = [line.replace('$$CWD$$', cwd) for line in lines2]

    d = difflib.Differ()
    result = list(d.compare(lines1, lines2))

    hasError = False
    for l in result:
        if l[0:2] == '+ ' or l[0:2] == '- ':
            hasError = True
            break
    if hasError and displayError:
        print("stderr")
        print("".join(result))
        return False
    return True


def check_process(tester, args, stdoutFile, errFiles, generatedFile, compareFile, input=None):
    """
    Execute a subprocess using args as the command line.
    if stdoutFile is not None, compare it to the stdout of the process
    if generatedFile and compareFile are not None, compare them to each other
    """

    # always turn off curses
    args.append("--no-curses")

    if args[1][-4:] == '.exe':
        args = args[1:]
    inputString = None
    inputX = None
    if input:
        with open(input, 'rb') as f:
            inputString = f.read()
        inputX = subprocess.PIPE
    p = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=inputX)
    (stdoutX, stderr) = p.communicate(input=inputString)

    returnValue = True
    if stdoutFile is not None:
        with open(stdoutFile, 'r') as f:
            lines2 = f.readlines()

        if six.PY2:
            lines1 = stdoutX.splitlines(True)
        else:
            lines1 = stdoutX.decode('utf-8').splitlines(True)

        if os.name == 'nt':
            lines2 = [line.replace('Tests/', 'Tests\\') for line in lines2]
            lines1 = [line.replace('\r', '') for line in lines1]

        d = difflib.Differ()
        result = list(d.compare(lines1, lines2))

        hasError = False
        for l in result:
            if l[0:2] == '+ ' or l[0:2] == '- ':
                hasError = True
                break
        if hasError:
            print("stdout:")
            print("".join(result))
            returnValue = False

    if errFiles is not None:
        if isinstance(errFiles, list):
            isClean = True
            for errFile in errFiles:
                isClean &= compare_file(errFile, stderr, False)
            if not isClean:
                compare_file(errFiles[0], stderr, True)
        else:
            returnValue &= compare_file(errFiles, stderr, True)

    if generatedFile is not None:
        with open(generatedFile, 'r') as f:
            lines2 = f.readlines()

        with open(compareFile, 'r') as f:
            lines1 = f.readlines()

        d = difflib.Differ()
        result = list(d.compare(lines1, lines2))

        hasError = False
        for l in result:
            if l[0:2] == '+ ' or l[0:2] == '- ':
                hasError = True
                break

        if hasError:
            print(generatedFile)
            print("".join(result))
            returnValue = False

    tester.assertTrue(returnValue, "Comparisons failed")


if __name__ == '__main__':
    if os.environ.get('RFCEDITOR_TEST'):
        test_program = "run.py"
    else:
        if os.name == 'nt':
            test_program += '.exe'
        test_program = which(test_program)
        if test_program is None:
            print("Failed to find the rfc-errata for testing")
            test_program = "run.py"
    unittest.main(buffer=True)
