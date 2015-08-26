import unittest
from unittest.mock import patch, call

from cabot_tools import puppet


class CheckfilesForClassesTests(unittest.TestCase):
    @patch("cabot_tools.puppet._checkfile_for_class")
    def test_multiple(self, _checkfile_for_class):
        classes = ["a", "b", "c"]
        puppet.checkfiles_for_classes("/puppet", classes)
        _checkfile_for_class.assert_has_calls([
            call("/puppet", "a"),
            call("/puppet", "b"),
            call("/puppet", "c"),
        ])


class CheckfileForClassTests(unittest.TestCase):
    def test_simple_name(self):
        filename = puppet._checkfile_for_class("/puppet", "example")
        self.assertEqual(filename, "/puppet/modules/example/cabot-checks.ini")

    def test_submodule(self):
        filename = puppet._checkfile_for_class("/puppet", "example::another")
        self.assertEqual(filename, "/puppet/modules/example/another/cabot-checks.ini")

    def test_disallow_shenanigans(self):
        with self.assertRaises(Exception):
            puppet._checkfile_for_class("/puppet", "../fork")
