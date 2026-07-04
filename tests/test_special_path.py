import os
import unittest
from test_binary_inputs import safe_read_staged_file

class TestSpecialFilePaths(unittest.TestCase):

    def setUp(self):
        self.test_files = []

    def tearDown(self):
        for path in self.test_files:
            if os.path.exists(path):
                os.remove(path)

    def _create_special_file(self, filename):
        path = os.path.join(os.path.dirname(__file__), filename)
        with open(path, 'w', encoding='utf-8') as f:
            f.write("Special path test content payload.")
        self.test_files.append(path)
        return path

    def test_path_with_spaces(self):
        # Validate handling of file paths containing blank spaces
        path = self._create_special_file("staged file with spaces.txt")
        content = safe_read_staged_file(path)
        self.assertEqual(content, "Special path test content payload.")

    def test_path_with_non_ascii(self):
        # Validate handling of international or non-ASCII characters
        path = self._create_special_file("test_unicode_मशीन_café.txt")
        content = safe_read_staged_file(path)
        self.assertEqual(content, "Special path test content payload.")

if __name__ == '__main__':
    unittest.main()
