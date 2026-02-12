#!/usr/bin/env python
"""
Unit tests for docker_operations.py helpers.
"""

import os
import sys
import unittest

# Add the utils directory to the path so we can import module functions.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from docker_operations import normalize_tag_suffix


class TestNormalizeTagSuffix(unittest.TestCase):
    """Tests for normalize_tag_suffix()."""

    def test_empty_suffix_returns_empty(self):
        self.assertEqual(normalize_tag_suffix(""), "")
        self.assertEqual(normalize_tag_suffix("   "), "")
        self.assertEqual(normalize_tag_suffix(None), "")

    def test_plain_text_suffix_is_preserved(self):
        self.assertEqual(normalize_tag_suffix("temp"), "temp")
        self.assertEqual(normalize_tag_suffix("temp2"), "temp2")

    def test_existing_hyphen_prefix_is_preserved(self):
        self.assertEqual(normalize_tag_suffix("-temp"), "-temp")
        self.assertEqual(normalize_tag_suffix("-temp_2.1"), "-temp_2.1")

    def test_valid_characters_are_accepted(self):
        self.assertEqual(normalize_tag_suffix("release_1.2"), "release_1.2")
        self.assertEqual(normalize_tag_suffix("A1_b-2.3"), "A1_b-2.3")

    def test_invalid_characters_raise_value_error(self):
        with self.assertRaises(ValueError):
            normalize_tag_suffix("bad suffix")
        with self.assertRaises(ValueError):
            normalize_tag_suffix("../temp")
        with self.assertRaises(ValueError):
            normalize_tag_suffix("@temp")


if __name__ == "__main__":
    unittest.main()
