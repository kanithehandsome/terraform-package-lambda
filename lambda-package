#!/usr/bin/env python
#
# Python because it comes on Mac and Linux - Node must be installed.
#

import sys
import json
import shutil
import os.path
import hashlib
import base64

class Packager:
    def __init__(self, input_values):
        self.start_dir = os.getcwd()
        self.basename = os.path.join(self.start_dir, input_values["basename"])
        self.source_dir = os.path.dirname(self.basename)

    def zipfile(self):
        return self.basename + '.zip'

    def clean_tree(self):
        try:
            shutil.rmtree(self.basename)
        except:
            pass

    def requirements_file(self):
        return os.path.join(self.source_dir, 'requirements.txt')

    def package(self):
        self.clean_tree()
        os.mkdir(self.basename)
        shutil.copy(self.basename + ".py", self.basename)
        with open(os.path.join(self.basename, 'setup.cfg'), 'w') as f:
            f.write("[install]\nprefix=\n")
        try:
            os.remove(self.zipfile())
        except:
            pass
        os.chdir(self.basename)
        if os.path.isfile(self.requirements_file()):
            os.system('pip install -r ../requirements.txt -t {}/ >/dev/null'.format(os.getcwd()))
        os.system('zip -9r {} . >/dev/null'.format(self.zipfile()))
        os.chdir(self.start_dir)
        self.clean_tree()

    def output_base64sha256(self):
        with open(self.zipfile(), 'r') as f:
            contents = f.read()
        return base64.b64encode(hashlib.sha256(contents).digest())

    def output(self):
        return {
          "basename": self.basename,
          "runtime": "python2.7",
          "filename": self.zipfile(),
          "output_base64sha256": self.output_base64sha256()
        }

def main():
    packager = Packager(json.load(sys.stdin))
    packager.package()
    json.dump(packager.output(), sys.stdout)

if __name__=='__main__':
    main()
