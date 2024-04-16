import os
import unittest
import sys
if sys.version_info >= (3, 3):
    from unittest.mock import patch, mock_open
else:
    # Expect the `mock` package for python 2.
    # https://pypi.python.org/pypi/mock
    from mock import patch, mock_open
from rosdoc_lite import doxygenator as doxy

def builtins_name():
    return "__builtin__.open" if sys.version_info.major < 3 else "builtins.open"

def urlopen_name():
    return "urllib2.urlopen" if sys.version_info.major < 3 else "urllib.request.urlopen"

class TestGetDocPath(unittest.TestCase):

    def setUp(self):
        self.tagfile_spec = "test_tagfile_spec.yaml"
        self.tagfile_dir = "./test_tagfiles"
        self.output_subfolder = "/path/to/"

    def tearDown(self):
        if os.path.exists(self.tagfile_spec):
            os.remove(self.tagfile_spec)
        if os.path.exists(self.tagfile_dir):
            os.rmdir(self.tagfile_dir)

    def test_relative_doc_path(self):
        tag_pair = {'docs_url':"relative/path"}
        output = doxy.get_doc_path("sub/folders", tag_pair)
        self.assertEqual("../../relative/path", output)

        tag_pair = {'docs_url':"relative/path",'doxygen_output_folder':"doxygen_output_folder"}
        output = doxy.get_doc_path("sub/folders", tag_pair)
        self.assertEqual("../../relative/path/doxygen_output_folder", output)

    def test_absolute_doc_path(self):
        tag_pair = {'docs_url': "https://absolu.te/path"}
        output = doxy.get_doc_path("sub/folders", tag_pair)
        self.assertEqual("https://absolu.te/path", output)

        tag_pair = {'docs_url': "https://absolu.te/path",'doxygen_output_folder':"doxygen_output_folder"}
        output = doxy.get_doc_path("sub/folders", tag_pair)
        self.assertEqual("https://absolu.te/path/doxygen_output_folder", output)

    def test_prepare_tagfiles_valid_http_location(self):
        input_tagfile_spec = "- location: http://example.com/tagfile.yaml\n  docs_url: http://example.com/docs"
        expected_result = os.path.join(self.tagfile_dir, 'tagfile.yaml') + "=http://example.com/docs "
        with patch(builtins_name(), mock_open(read_data=input_tagfile_spec)) as _:
            with patch(urlopen_name()) as mock_urlopen:
                mock_urlopen.return_value.code = 200
                mock_urlopen.return_value.read.return_value = b"tagfile_content"
                mock_urlopen.return_value.headers.getparam.return_value = "utf-8"  # python 2
                mock_urlopen.return_value.headers.get_param.return_value = "utf-8"  # python 3

                result = doxy.prepare_tagfiles(self.tagfile_spec, self.tagfile_dir, self.output_subfolder)

                self.assertEqual(result, expected_result)

    def test_prepare_tagfiles_invalid_http_location(self):
        input_tagfile_spec = "- location: http://example.com/invalid_tagfile.yaml\n  docs_url: http://example.com/docs"
        with patch(builtins_name(), mock_open(read_data=input_tagfile_spec)) as _:
            with patch(urlopen_name()) as mock_urlopen:
                mock_urlopen.return_value.code = 404

                result = doxy.prepare_tagfiles(self.tagfile_spec, self.tagfile_dir, self.output_subfolder)

                self.assertEqual(result, "")

    def test_prepare_tagfiles_valid_file_location(self):
        input_tagfile_spec = "- location: file:///path/to/tagfile.yaml\n  docs_url: /path/to/docs"
        expected_result = "/path/to/tagfile.yaml=/path/to/docs "

        with patch(builtins_name(), mock_open(read_data=input_tagfile_spec)) as _:
            result = doxy.prepare_tagfiles(self.tagfile_spec, self.tagfile_dir, self.output_subfolder)

            self.assertEqual(result, expected_result)

    def test_prepare_tagfiles_invalid_location_prefix(self):
        input_tagfile_spec = "- location: invalid_prefix://example.com/tagfile.yaml\n  docs_url: http://example.com/docs"
        with patch(builtins_name(), mock_open(read_data=input_tagfile_spec)) as _:
            result = doxy.prepare_tagfiles(self.tagfile_spec, self.tagfile_dir, self.output_subfolder)

            self.assertEqual(result, "")
