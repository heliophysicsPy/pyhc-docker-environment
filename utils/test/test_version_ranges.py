#!/usr/bin/env python
"""
Lean unit tests for the current version range logic in generate_dependency_table.py.

Only tests public functions that still exist:
- combine_ranges
- remove_wildcards
- are_compatible
- clean_range_str
- reorder_requirements
- determine_version_range
"""

import unittest
import sys
import os

# Add the utils directory to the path so we can import the functions
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packaging.specifiers import SpecifierSet, InvalidSpecifier

from generate_dependency_table import (
    combine_ranges,
    remove_wildcards,
    are_compatible,
    clean_range_str,
    reorder_requirements,
    determine_version_range,
)


class TestVersionRangeLogic(unittest.TestCase):
    # ------------------------
    # combine_ranges
    # ------------------------
    def test_any_sentinel_handling(self):
        self.assertEqual(combine_ranges("any", ">=1.0"), ">=1.0")
        self.assertEqual(combine_ranges(">=1.0", "any"), ">=1.0")
        self.assertEqual(combine_ranges("ANY", ">=1.0"), ">=1.0")
        self.assertEqual(combine_ranges("any", "any"), "any")

    def test_combine_ranges_basic(self):
        # Use direct string match where the implementation has a stable cleaned order,
        # otherwise compare via SpecifierSet to normalize e.g. <2 vs <2.0.
        cases_strict = [
            (">=1.1.1", "any", ">=1.1.1"),
            ("any", ">=1.1.2", ">=1.1.2"),
            (">1.1.1", "==1.2.3", " ==1.2.3"),
            (">=1.1.1", ">=1.2.3,<2.0", "<2.0,>=1.2.3"),
            (">=1.2.3,<2", ">=1.1.1", "<2,>=1.2.3"),
            ("==1.1.2", ">=0.9", " ==1.1.2"),
            ("==1.1.2", "<2", " ==1.1.2"),
            (">=1.9", ">=1.21.0", ">=1.21.0"),
            (">=1.9", ">=1.19.5,<1.27.0", "<1.27.0,>=1.19.5"),
            (">=1.21.0", ">=1.19.5,<1.27.0", "<1.27.0,>=1.21.0"),
        ]
        for current, new, expected in cases_strict:
            with self.subTest(current=current, new=new):
                self.assertEqual(combine_ranges(current, new).lstrip(), expected.lstrip())

        cases_normalized = [
            # Normalize formatting differences through SpecifierSet
            ("~=1.0", ">=1.0,<2.0", "<2.0,>=1.0"),
            (">=1.0,!=1.5", ">=1.2,!=1.6", "!=1.5,!=1.6,>=1.2"),
            (">=1.0,<2.0,!=1.5", ">=1.2,<1.8", "!=1.5,<1.8,>=1.2"),
        ]
        for current, new, expected in cases_normalized:
            with self.subTest(current=current, new=new):
                result = combine_ranges(current, new)
                # Compare SpecifierSet objects directly instead of their string representations
                # to avoid inconsistent ordering in string representation
                self.assertEqual(SpecifierSet(result), SpecifierSet(expected))

    def test_combine_ranges_incompatible(self):
        cases = [
            ("<1.1.1", ">=1.2.3,<2.0"),
            (">2.0", "<1.0"),
            ("==1.0", "==2.0"),
            (">=2.0", "<=1.0"),
            ("!=1.0", "==1.0"),
            (">1.0,<2.0", ">3.0,<4.0"),
            (">=1.0,<=1.5", ">=2.0,<=3.0"),
        ]
        for current, new in cases:
            with self.subTest(current=current, new=new):
                with self.assertRaises(RuntimeError):
                    combine_ranges(current, new)

    def test_compatible_release_is_never_retained(self):
        # Ensure ~= is expanded to explicit windows and not present in the result
        cases = [
            (">=0.4.1", "~=0.4", ">=0.4.1,<1"),
            # Specific regression: mdit-py-plugins case
            (">=0.4.1", "~=0.4", ">=0.4.1,<1"),
            ("~=0.4", ">=0.4.1", ">=0.4.1,<1"),
            (">=0.1,<1", "~=0.1", ">=0.1,<1"),
            ("~=3.0", ">=2.0.0,<5.0.0", ">=3.0,<4"),
            ("~=1.2.3", ">=1.2.4", ">=1.2.4,<1.3"),
            (">=1.2.3", "~=1.2.3", ">=1.2.3,<1.3"),
            (">=0.4,<0.5", "~=0.4", ">=0.4,<0.5"),
            ("<=0.9,>=0.1", "~=0.1", ">=0.1,<=0.9"),
        ]
        for current_range, new_range, expected in cases:
            with self.subTest(current=current_range, new=new_range):
                result = combine_ranges(current_range, new_range)
                self.assertNotIn("~=", result)
                self.assertEqual(str(SpecifierSet(result)), str(SpecifierSet(expected)))

    def test_invalid_inputs_raise(self):
        with self.assertRaises(InvalidSpecifier):
            combine_ranges("invalid", ">=1.0")
        with self.assertRaises(InvalidSpecifier):
            combine_ranges(">=1.0", "invalid")
        
    # ------------------------
    # remove_wildcards
    # ------------------------
    def test_remove_wildcards(self):
        cases = [
            ("==1.*", ">=1.0.0,<2.0.0"),
            (">=1.0.4,==1.*", ">=1.0.4,>=1.0.0,<2.0.0"),
            ("!=1.6.*", "!=1.6"),
            (">=4.9.2,!=5.0.*", ">=4.9.2,!=5.0"),
            ("==1.2.*", ">=1.2.0,<1.3.0"),
            (">=1.5.0,<2.0,!=1.6.*", ">=1.5.0,<2.0,!=1.6"),
            (">=1.0.0", ">=1.0.0"),
            ("", ""),
        ]
        for input_val, expected in cases:
            with self.subTest(input_val=input_val):
                self.assertEqual(remove_wildcards(input_val), expected)

    # ------------------------
    # reorder_requirements / clean_range_str
    # ------------------------
    def test_reorder_and_clean(self):
        # Expectations aligned with our cleaning order (lower, upper, then remaining like !=)
        self.assertEqual(reorder_requirements("<2.0,!=1.6,>=1.5.0"), ">=1.5.0,<2.0,!=1.6")
        self.assertEqual(reorder_requirements("!=1.5,>=1.0,<2.0"), ">=1.0,<2.0,!=1.5")
        self.assertEqual(clean_range_str("<2.0,!=1.6,>=1.5.0"), ">=1.5.0,<2.0,!=1.6")
        self.assertEqual(clean_range_str("!=1.5,>=1.0,<2.0"), ">=1.0,<2.0,!=1.5")

    # ------------------------
    # determine_version_range
    # ------------------------
    def test_determine_version_range(self):
        deps = {"package1": ">=1.0", "package2": ">=2.0,<3.0"}
        self.assertEqual(determine_version_range(deps, "package3", ">=1.5"), ">=1.5")
        self.assertEqual(determine_version_range(deps, "package1", ">=1.2"), ">=1.2")
        # Just ensure it returns a string (combined/cleaned), not throwing
        self.assertIsInstance(determine_version_range(deps, "package1", ">=1.0"), str)

    # ------------------------
    # are_compatible
    # ------------------------
    def test_are_compatible(self):
        self.assertTrue(are_compatible(">=1.0", ">=0.9"))
        self.assertFalse(are_compatible(">=2.0", "<1.0"))


if __name__ == '__main__':
    unittest.main(verbosity=2)