import unittest
import packager
import zipfile

def do(input_values):
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
        self.assertEquals(result["zip_contents"]["foo.py"], "# Hello, Python!\n")

    def test_uses_specified_output_filename(self):
        result = do({
            "code": "test/python-simple/foo.py",
            "output_filename": "test/foo-x.zip"
        })
        self.assertEquals(result["output"]["output_filename"], "test/foo-x.zip")

    def test_packages_extra_files(self):
        result = do({
            "code": "test/python-simple/foo.py",
            "extra_files": [ "extra.txt" ]
        })
        self.assertEquals(result["zip_contents"]["extra.txt"], "Extra File!\n")

    def test_packages_extra_directories(self):
        result = do({
            "code": "test/python-simple/foo.py",
            "extra_files": [ "extra-dir" ]
        })
        self.assertEquals(result["zip_contents"]["extra-dir/dir.txt"], "Dir File!\n")
