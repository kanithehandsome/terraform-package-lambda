import unittest
import packager
import zipfile
import time

import os #FIXME

def do(input_values):
    if not "output_filename" in input_values:
        input_values["output_filename"] = ""
    if not "extra_files" in input_values:
        input_values["extra_files"] = ''
    if not 'partial_hash' in input_values:
        input_values['partial_hash'] = 'false'
    p = packager.Packager(input_values)
    p.package()
    output = p.output()
    zf = zipfile.ZipFile(output["output_filename"], 'r')
    zip_contents = {}
    for name in zf.namelist():
        zip_contents[name] = zf.read(name)
    zf.close()
    return {
        "output": output,
        "zip_contents": zip_contents
    }

class TestPackager(unittest.TestCase):
    def test_packages_a_python_script_with_no_dependencies(self):
        result = do({"code": "test/python-simple/foo.py"})
        self.assertEqual(result["zip_contents"]["foo.py"], "# Hello, Python!\n".encode('utf-8'))

    def test_packaging_source_without_dependencies_twice_produces_the_same_hash(self):
        result1 = do({"code": "test/python-simple/foo.py"})
        time.sleep(2) # Allow for current time to "infect" result
        result2 = do({"code": "test/python-simple/foo.py"})
        self.assertEqual(result1["output"]["output_base64sha256"], result2["output"]["output_base64sha256"])

    def test_uses_specified_output_filename(self):
        result = do({
            "code": "test/python-simple/foo.py",
            "output_filename": "test/foo-x.zip"
        })
        self.assertEqual(result["output"]["output_filename"], "test/foo-x.zip")

    def test_packages_extra_files(self):
        result = do({
            "code": "test/python-simple/foo.py",
            "extra_files": "extra.txt"
        })
        self.assertEqual(result["zip_contents"]["extra.txt"], "Extra File!\n".encode('utf-8'))

    def test_packages_extra_directories(self):
        result = do({
            "code": "test/python-simple/foo.py",
            "extra_files": "extra.txt,extra-dir"
        })
        self.assertEqual(result["zip_contents"]["extra-dir/dir.txt"], "Dir File!\n".encode('utf-8'))

    def test_installs_python_requirements(self):
        result = do({"code": "test/python-deps/foo.py"})
        self.assertTrue("mock/__init__.py" in result["zip_contents"])

    def test_packaging_python_with_requirements_twice_produces_the_same_hsah(self):
        result1 = do({"code": "test/python-deps/foo.py", "partial_hash": "true"})
        time.sleep(2) # Allow for current time to "infect" result
        result2 = do({"code": "test/python-deps/foo.py", "partial_hash": "true"})
        self.assertEqual(result1["output"]["output_base64sha256"], result2["output"]["output_base64sha256"])

    def test_packages_a_node_script_with_no_dependencies(self):
        result = do({"code": "test/node-simple/foo.js"})
        self.assertEqual(result["zip_contents"]["foo.js"], "// Hello, Node!\n".encode('utf-8'))

    def test_packages_a_node_script_with_dependencies(self):
        result = do({"code": "test/node-deps/foo.js"})
        self.assertTrue("node_modules/" in result["zip_contents"])
        self.assertTrue("node_modules/underscore/" in result["zip_contents"])

    def test_packaging_node_with_dependencies_twice_produces_same_hash(self):
        result1 = do({"code": "test/node-deps/foo.js"})
        os.system("cp test/node-deps/foo.zip /tmp/a.zip")
        time.sleep(2) # Allow for current time to "infect" result
        result2 = do({"code": "test/node-deps/foo.js"})
        os.system("cp test/node-deps/foo.zip /tmp/b.zip")
        self.assertEqual(result1["output"]["output_base64sha256"], result2["output"]["output_base64sha256"])


if __name__ == '__main__':
    unittest.main()