import os
from string import Template


class Templates(object):
    def __init__(self, templateDir):
        with open(os.path.join(templateDir, "sectionNoteTemplate.txt")) as f:
            self.sectionNote = Template(f.read())
        with open(os.path.join(templateDir, "inlineNoteTemplate.txt")) as f:
            self.inlineNote = Template(f.read())
        with open(os.path.join(templateDir, "endnoteTemplate.txt")) as f:
            self.endNote = Template(f.read())
        with open(os.path.join(templateDir, "headnoteTemplate.txt")) as f:
            self.headNote = Template(f.read())
        with open(os.path.join(templateDir, "htmlTemplate.txt")) as f:
            self.html = Template(f.read())
