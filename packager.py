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
import tempfile
import zipfile
import subprocess
import base64
import shutil
import functools

class Sandbox:
    '''
    A temporary directory for staging a lambda package.

    We import files, write new files, and run commands in the Sandbox to
    produce the image we want to zip for the lambda.
    '''
    FILE_STRING_MTIME = 1493649512

    def __init__(self):
        self.dir = tempfile.mkdtemp(suffix='lambda-packager')

    def run_command(self, cmd):
        cwd = os.getcwd()
        os.chdir(self.dir)
        result = os.system(cmd)
        os.chdir(cwd)
        return result

    def import_path(self, path):
        if os.path.isdir(path):
            shutil.copytree(path, os.path.join(
                self.dir, os.path.basename(path)))
        else:
            shutil.copy2(path, self.dir)

    def add_file_string(self, path, contents):
        full_path = os.path.join(self.dir, path)
        with open(full_path, 'w') as f:
            f.write(contents)
        os.utime(full_path, (self.FILE_STRING_MTIME, self.FILE_STRING_MTIME))

    def fix_time(self, full_path):
        os.utime(full_path, (self.FILE_STRING_MTIME, self.FILE_STRING_MTIME))

    def files(self):
        result = []
        for root, dirs, files in os.walk(self.dir):
            for name in files:
                if root == self.dir:
                    dest = name
                else:
                    #raise Exception("self : {}, dst : {}".format(self.dir, root[len(self.dir)+1:]))
                    dest = os.path.join(root[len(self.dir) + 1:], name)
                result.append(dest)
            for name in dirs:
                if root == self.dir:
                    dest = name
                    result.append(dest)
                else:
                    dest = os.path.join(root[len(self.dir) + 1:], name)
                result.append(dest)
        result = list(set(result))
        result.sort()
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

    def rewrite_python_dist_info_record(self):
        # pylint: disable=unused-variable
        for root, dirs, files in os.walk(self.dir):
            for f in files:
                if f == 'RECORD':
                    #raise Exception('record filename: {}'.format(f))
                    if root.endswith('.dist-info'):
                        fpath = os.path.join(root, f)
                        with open(fpath, 'r') as rf:
                            lines = sorted(rf.readlines())
                        self.add_file_string(fpath, os.linesep.join(lines))


    def clean_pycache(self):
        # pylint: disable=unused-variable
        for root, dirs, files in os.walk(self.dir):
            for dir in dirs:
                if dir == '__pycache__':
                    shutil.rmtree(os.path.join(root,dir))
                    self.fix_time(root)

    def clean_setup_tool(self):
        # pylint: disable=unused-variable
        for root, dirs, files in os.walk(self.dir):
            for dir in dirs:
                if dir.startswith('setuptools'):
                    shutil.rmtree(os.path.join(root,dir))
                    self.fix_time(root)

class SandboxMtimeDecorator:
    '''A decorator for Sandbox which sets all files newly created by some command to `mtime'.'''

    def __init__(self, sb, mtime):
        self.sb = sb
        self.mtime = mtime
        # use fixed time, avoid scenario, if we clone lamba source repo, the requirements mtime will change
        # though nothing may be changed
        #self.mtime = sb.FILE_STRING_MTIME
        self.before_files = set(self.sb.files())

    def __getattr__(self, name):
        return getattr(self.sb, name)

    def run_command(self, cmd):
        self.sb.run_command(cmd)
        all_paths =[]
        for filename in set(self.sb.files()).difference(self.before_files):
            if os.path.exists(os.path.join(self.sb.dir, filename)):
                all_paths.append(os.path.join(self.sb.dir, filename))

        #sort the path so parent timestamp not changed after children
        sorted_paths =sorted(all_paths, key=lambda p : p.count(os.path.sep), reverse=True)
        for path in sorted_paths:
            os.utime(path,(self.mtime, self.mtime))


class RequirementsCollector:
    def __init__(self, code):
        self.code = code

    def _source_path(self):
        return os.path.join(os.getcwd(), os.path.dirname(self.code))

    def _source_requirements_file(self):
        # pylint: disable=no-member
        return os.path.join(self._source_path(), self._requirements_file())

    def _requirements_mtime(self):
        return os.stat(self._source_requirements_file()).st_mtime

    @staticmethod
    def collector(code):
        code_type = os.path.splitext(code)[1]
        if code_type == '.py':
            return PythonRequirementsCollector(code)
        elif code_type == '.js':
            return NodeRequirementsCollector(code)
        elif code_type == '.rb':
            return RubyRequirementsCollector(code)
        else:
            raise Exception("Unknown code type '{}'".format(code_type))


class PythonRequirementsCollector(RequirementsCollector):
    def _requirements_file(self):
        return 'requirements.txt'

    def collect(self, sb):
        requirements_file = self._source_requirements_file()
        if not os.path.isfile(requirements_file):
            return
        mtime = self._requirements_mtime()
        sb.add_file_string('setup.cfg', "[install]\nprefix=\n")
        sbm = SandboxMtimeDecorator(sb, mtime)
        # before files initialized
        sbm.run_command(
            'pip3 install -r {} -t {}/ >/dev/null'.format(requirements_file, sb.dir))

        # set time.time() result to a fixed time
        sbm.run_command(
            'python -c \'import time, compileall; time.time = lambda: {}; compileall.compile_dir(".", force=True)\' >/dev/null'.format(sb.FILE_STRING_MTIME))

        sb.rewrite_python_dist_info_record()
        #remove setup tools, not needed
        sb.clean_setup_tool()


class NodeRequirementsCollector(RequirementsCollector):
    def _requirements_file(self):
        return 'package.json'

    def collect(self, sb):
        requirements_file = self._source_requirements_file()
        if not os.path.isfile(requirements_file):
            return
        sb.import_path(self._source_requirements_file())
        sbm = SandboxMtimeDecorator(sb, self._requirements_mtime())
        sbm.run_command('npm install --production >/dev/null 2>&1')
        for filename in sbm.files():
            if not filename.endswith('package.json'):
                continue
            full_path = os.path.join(sbm.dir, filename)
            mtime = os.stat(full_path).st_mtime
            with open(full_path, 'rb') as f:
                contents = f.read()
            contents = contents.replace(sb.dir.encode('utf-8'), '/tmp/lambda-package'.encode('utf-8'))
            with open(full_path, 'wb') as f:
                f.write(contents)
            os.utime(full_path, (mtime, mtime))

class RubyRequirementsCollector(RequirementsCollector):
    def _requirements_file(self):
        return 'Gemfile'

    def collect(self, sb):
        requirements_file = self._source_requirements_file()
        if not os.path.isfile(requirements_file):
            return
        sb.import_path(self._source_requirements_file())
        sbm = SandboxMtimeDecorator(sb, self._requirements_mtime())
        sbm.run_command('bundle install --path vendor/bundle >/dev/null 2>&1')

class Packager:
    def __init__(self, input_values):
        self.input = input_values
        self.code = self.input["code"]
        self.extra_files = []

        if len(self.input.get('extra_files', '')) > 0:
            self.extra_files = self.input['extra_files'].split(',')

    def output_filename(self):
        if self.input.get('output_filename', '') != '':
            return self.input['output_filename']
        return os.path.splitext(self.code)[0] + ".zip"

    def paths_to_import(self):
        yield self.code
        source_dir = os.path.dirname(self.code)
        for extra_file in self.extra_files:
            yield os.path.join(source_dir, extra_file)

    def package(self):
        sb = Sandbox()
        for path in self.paths_to_import():
            sb.import_path(path)
        RequirementsCollector.collector(self.code).collect(sb)
        sb.zip(self.output_filename())
        sb.delete()

    def output_base64sha256(self):
        sha256 = hashlib.sha256()
        with open(self.output_filename(), 'rb') as f:
            sha256.update(f.read())
        hash_b64= base64.b64encode(sha256.digest()).decode('utf-8')
        return hash_b64

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


if __name__ == '__main__':
    main()
