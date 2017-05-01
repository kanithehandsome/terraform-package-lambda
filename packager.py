#!/usr/bin/env python
#
# Python because it comes on Mac and Linux - Node must be installed.
#

import sys
import os
import os.path
import json
import shutil
import hashlib
import base64
import tempfile
import zipfile

class Sandbox:
    '''
    A temporary directory for staging a lambda package.

    We import files, write new files, and run commands in the Sandbox to
    produce the image we want to zip for the lambda.
    '''
    FILE_STRING_MTIME = 1493649512

    def __init__(self):
        self.dir = tempfile.mkdtemp(suffix = 'lambda-packager')

    def run_command(self, cmd):
        cwd = os.getcwd()
        os.chdir(self.dir)
        result = os.system(cmd)
        os.chdir(cwd)
        return result

    def import_path(self, path):
        if os.path.isdir(path):
            shutil.copytree(path, os.path.join(self.dir, os.path.basename(path)))
        else:
            shutil.copy2(path, self.dir)

    def add_file_string(self, path, contents):
        full_path = os.path.join(self.dir, path)
        with open(full_path, 'w') as f:
            f.write(contents)
        os.utime(full_path, (self.FILE_STRING_MTIME, self.FILE_STRING_MTIME))

    def _files_visit(self, result, dirname, names):
        for name in names:
            src = os.path.join(dirname, name)
            if dirname == self.dir:
                dst = name
            else:
                dst = os.path.join(dirname[len(self.dir)+1:], name)
            result.append(dst)

    def files(self):
        result = []
        os.path.walk(self.dir, self._files_visit, result)
        return result

    def zip(self, output_filename):
        zf = zipfile.ZipFile(output_filename, 'w')
        for filename in self.files():
            zf.write(os.path.join(self.dir, filename), filename)
        zf.close()

    def delete(self):
        try:
            shutil.rmtree(self.dir)
        except:
            pass

class Requirements:
    def __init__(self, code):
        self.code = code

    def _source_path(self):
        return os.path.join(os.getcwd(), os.path.dirname(self.code))

class PythonRequirements(Requirements):
    def requirements_file(self):
        return 'requirements.txt'

    def collect(self, sb):
        requirements_file = os.path.join(self._source_path(), self.requirements_file())
        mtime = os.stat(requirements_file).st_mtime
        sb.add_file_string('setup.cfg', "[install]\nprefix=\n")
        files_before = set(sb.files())
        sb.run_command('pip install -r {} -t {}/ >/dev/null'.format(requirements_file, sb.dir))
        files_added = set(sb.files()).difference(files_before)
        for filename in files_added:
            os.utime(os.path.join(sb.dir, filename), (mtime, mtime))
        sb.run_command('python -c \'import time, compileall; time.time = lambda: {}; compileall.compile_dir(".", force=True)\' >/dev/null'.format(mtime))
        files_added = set(sb.files()).difference(files_before)
        for filename in files_added:
            os.utime(os.path.join(sb.dir, filename), (mtime, mtime))

class NodeRequirements(Requirements):
    def requirements_file(self):
        return 'package.json'

    def collect(self, sb):
        sb.import_path(os.path.join(self._source_path(), 'package.json'))
        sb.run_command('npm install --production >/dev/null 2>&1')

class Packager:
    def __init__(self, input_values):
        self.input = input_values
        self.code = self.input["code"]

    def code_type(self):
        return os.path.splitext(self.code)[1]

    def _requirements_class(self):
        code_type = self.code_type()
        if code_type == '.py':
            return PythonRequirements
        elif code_type == '.js':
            return NodeRequirements
        else:
            raise Exception("Unknown code type '{}'".format(self.code_type()))

    def _requirements(self):
        return self._requirements_class()(self.code)

    def output_filename(self):
        if self.input.has_key('output_filename'):
            return self.input['output_filename']
        return os.path.splitext(self.code)[0] + ".zip"

    def requirements_file(self):
        source_dir = os.path.dirname(self.code)
        return os.path.join(source_dir, self._requirements().requirements_file())

    def paths_to_import(self):
        yield self.code
        source_dir = os.path.dirname(self.code)
        if self.input.has_key("extra_files"):
            for extra_file in self.input["extra_files"]:
                yield os.path.join(source_dir, extra_file)

    def _add_requirements(self, sb):
        requirements_file = os.path.join(os.getcwd(), self.requirements_file())
        if not os.path.isfile(requirements_file):
            return
        self._requirements().collect(sb)

    def package(self):
        sb = Sandbox()
        for path in self.paths_to_import():
            sb.import_path(path)
        self._add_requirements(sb)
        sb.zip(self.output_filename())
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
