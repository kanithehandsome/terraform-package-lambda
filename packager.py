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

    def system(self, cmd):
        cwd = os.getcwd()
        os.chdir(self.dir)
        result = os.system(cmd)
        os.chdir(cwd)
        return result

    def _zip_visit(self, zf, dirname, names):
        for name in names:
            zf.write(os.path.join(dirname, name), name)

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
        self.code = self.input["code"]

    def output_filename(self):
        if self.input.has_key('output_filename'):
            return self.input['output_filename']
        return os.path.splitext(self.code)[0] + ".zip"

    def requirements_file(self):
        source_dir = os.path.dirname(self.code)
        return os.path.join(source_dir, 'requirements.txt')

    def files_to_package(self):
        yield self.code
        source_dir = os.path.dirname(self.code)
        if self.input.has_key("extra_files"):
            for extra_file in self.input["extra_files"]:
                yield os.path.join(source_dir, extra_file)

    def package(self):
        sb = Sandbox()
        for filename in self.files_to_package():
            shutil.copy(filename, sb.dir)
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
