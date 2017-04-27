import unittest
import packager
import zipfile

class TestPackager(unittest.TestCase):
    def test_packages_a_python_script_with_no_dependencies(self):
        p = packager.Packager({
            "code": "test/python-simple/foo.py"
        })
        p.package()
        zf = zipfile.ZipFile(p.output()["output_filename"], 'r')
        self.assertEquals(zf.read('foo.py'), "# Hello, Python!\n")
        zf.close()
