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
import tempfile
import zipfile

class Sandbox:
    def __init__(self):
        self.dir = tempfile.mkdtemp(suffix = 'lambda-packager')

    def _zip_visit(self, zf, dirname, names):
        for name in names:
            zf.write(os.path.join(dirname, name), name)

    def system(self, cmd):
        cwd = os.getcwd()
        os.chdir(self.dir)
        result = os.system(cmd)
        os.chdir(cwd)
        return result

    def zip(self, output_filename):
        zf = zipfile.ZipFile(output_filename, 'w')
        os.path.walk(self.dir, self._zip_visit, zf)
        zf.close()

    def delete(self):
        try:
            shutil.rmtree(self.dir)
        except:
            pass

class Packager:
    def __init__(self, input_values):
        self.input = input_values
        self.start_dir = os.getcwd()
        self.code = input_values["code"]
        self.basename = os.path.join(self.start_dir, os.path.splitext(self.code)[0])
        self.source_dir = os.path.dirname(self.code)

    def output_filename(self):
        if self.input.has_key('output_filename'):
            return self.input['output_filename']
        return self.basename + '.zip'

    def clean_tree(self):
        try:
            shutil.rmtree(self.basename)
        except:
            pass

    def requirements_file(self):
        return os.path.join(self.source_dir, 'requirements.txt')

    def package(self):
        sb = Sandbox()
        shutil.copy(self.code, sb.dir)
        with open(os.path.join(sb.dir, 'setup.cfg'), 'w') as f:
            f.write("[install]\nprefix=\n")
        output_filename = os.path.join(os.getcwd(), self.output_filename())
        try:
            os.remove(output_filename)
        except:
            pass
        if os.path.isfile(self.requirements_file()):
            sb.system('pip install -r ../requirements.txt -t {}/ >/dev/null'.format(sb.dir))

        sb.zip(output_filename)
        sb.delete()

    def output_base64sha256(self):
        with open(self.output_filename(), 'r') as f:
            contents = f.read()
        return base64.b64encode(hashlib.sha256(contents).digest())

    def output(self):
        return {
          "code": self.code,
          "output_filename": self.output_filename(),
          "output_base64sha256": self.output_base64sha256()
        }

def main():
    packager = Packager(json.load(sys.stdin))
    packager.package()
    json.dump(packager.output(), sys.stdout)

if __name__=='__main__':
    main()
