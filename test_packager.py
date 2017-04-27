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
