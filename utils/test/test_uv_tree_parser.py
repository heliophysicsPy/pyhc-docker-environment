#!/usr/bin/env python
"""
Unit tests for uv dependency-tree parsing and package extraction flow.
"""

import os
import sys
import unittest
from unittest.mock import patch


# Add the utils directory to the path so we can import module functions.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from generate_dependency_table import (
    parse_uv_tree_output,
    get_dependency_ranges_by_package,
)


class TestParseUvTreeOutput(unittest.TestCase):
    def test_parse_simple_tree(self):
        output = """
requests v2.32.5
├── certifi v2026.1.4 [required: >=2017.4.17]
├── charset-normalizer v3.4.4 [required: >=2, <4]
└── urllib3 v2.5.0 [required: >=1.21.1, <3]
""".strip()

        version, dependencies = parse_uv_tree_output("requests", output)

        self.assertEqual(version, "2.32.5")
        self.assertEqual(dependencies["certifi"], ">=2017.4.17")
        self.assertEqual(dependencies["charset-normalizer"], ">=2,<4")
        self.assertEqual(dependencies["urllib3"], ">=1.21.1,<3")

    def test_parse_wildcard_and_normalization(self):
        output = """
demo v1.0.0
└── sample v1.2.3 [required: ==1.*]
""".strip()

        version, dependencies = parse_uv_tree_output("demo", output)

        self.assertEqual(version, "1.0.0")
        self.assertEqual(dependencies["sample"], ">=1.0.0,<2.0.0")

    def test_parse_invalid_root_raises(self):
        output = """
not-a-root-line
└── sample v1.2.3 [required: >=1.0]
""".strip()

        with self.assertRaises(RuntimeError):
            parse_uv_tree_output("badpkg", output)

    def test_parse_empty_output_raises(self):
        with self.assertRaises(RuntimeError):
            parse_uv_tree_output("empty", "")

    def test_parse_requires_variant_and_lowercase_name(self):
        output = """
DemoPkg v1.0.0
└── Requests v2.32.5 [requires: >=2.0, <4]
""".strip()

        version, dependencies = parse_uv_tree_output("DemoPkg", output)
        self.assertEqual(version, "1.0.0")
        self.assertEqual(dependencies["requests"], ">=2.0,<4")

    def test_parse_star_requirement_becomes_any(self):
        output = """
demo v1.0.0
└── optional-dep v0.1.0 [required: *]
""".strip()

        _, dependencies = parse_uv_tree_output("demo", output)
        self.assertEqual(dependencies["optional-dep"], "any")

    def test_parse_ignores_unmatched_lines(self):
        output = """
demo v1.0.0
this line should be ignored
└── dep-without-required v0.1.0
""".strip()

        _, dependencies = parse_uv_tree_output("demo", output)
        self.assertEqual(dependencies, {})

    def test_parse_duplicate_dependency_ranges_combines(self):
        output = """
demo v1.0.0
├── shared v3.4.5 [required: >=1.0, <3.0]
└── shared v3.4.5 [required: >=2.0]
""".strip()

        _, dependencies = parse_uv_tree_output("demo", output)
        self.assertEqual(dependencies["shared"], ">=2.0,<3.0")

    def test_parse_duplicate_dependency_ranges_conflict_raises(self):
        output = """
demo v1.0.0
├── shared v3.4.5 [required: <2.0]
└── shared v3.4.5 [required: >=3.0]
""".strip()

        with self.assertRaises(RuntimeError):
            parse_uv_tree_output("demo", output)

    def test_parse_tilde_requirement_is_normalized(self):
        output = """
demo v1.0.0
└── compat v1.2.7 [required: ~=1.2.3]
""".strip()

        _, dependencies = parse_uv_tree_output("demo", output)
        self.assertEqual(dependencies["compat"], ">=1.2.3,<1.3")


class TestGetDependencyRangesByPackageParallel(unittest.TestCase):
    @staticmethod
    def _mock_tree_for_command(command, *args, **kwargs):
        if "alpha==1.0.0" in command:
            return (
                "alpha v1.0.0\n"
                "└── shared v3.4.5 [required: >=1.0, <3.0]\n"
            )
        if "beta==2.0.0" in command:
            return (
                "beta v2.0.0\n"
                "└── shared v3.4.5 [required: >=2.0, <4.0]\n"
            )
        raise AssertionError(f"Unexpected command in test: {command}")

    @patch("generate_dependency_table.get_packages_installed_in_environment", return_value=[])
    @patch("generate_dependency_table.subprocess.check_output")
    def test_serial_and_parallel_match(self, mock_check_output, _mock_installed):
        mock_check_output.side_effect = self._mock_tree_for_command
        packages = ["alpha==1.0.0", "beta==2.0.0"]

        serial = get_dependency_ranges_by_package(packages, max_workers=1)
        parallel = get_dependency_ranges_by_package(packages, max_workers=4)

        self.assertEqual(serial, parallel)
        self.assertEqual(serial["alpha==1.0.0"]["alpha"], "==1.0.0")
        self.assertEqual(serial["beta==2.0.0"]["beta"], "==2.0.0")
        self.assertEqual(serial["alpha==1.0.0"]["shared"], ">=1.0,<3.0")
        self.assertEqual(serial["beta==2.0.0"]["shared"], ">=2.0,<4.0")

    @patch("generate_dependency_table.get_packages_installed_in_environment", return_value=["delta"])
    @patch("generate_dependency_table.subprocess.check_output")
    def test_use_installed_uses_uv_tree_command(self, mock_check_output, _mock_installed):
        mock_check_output.return_value = (
            "delta v1.2.3\n"
            "└── dep v9.9.9 [required: >=1.0]\n"
        )

        result = get_dependency_ranges_by_package(["delta==1.2.3"], use_installed=True, max_workers=1)

        called_command = mock_check_output.call_args[0][0]
        self.assertIn("uv pip tree --show-version-specifiers --package delta", called_command)
        self.assertEqual(result["delta==1.2.3"]["delta"], "==1.2.3")

    @patch("generate_dependency_table.get_packages_installed_in_environment", return_value=[])
    @patch("generate_dependency_table.subprocess.check_output")
    def test_unpinned_package_gets_resolved_version_key(self, mock_check_output, _mock_installed):
        mock_check_output.return_value = (
            "gamma v9.9.9\n"
            "└── dep v1.0.0 [required: >=1.0]\n"
        )

        result = get_dependency_ranges_by_package(["gamma[extra]"], max_workers=1)
        self.assertIn("gamma[extra]==9.9.9", result)
        self.assertEqual(result["gamma[extra]==9.9.9"]["gamma"], "==9.9.9")

    @patch("generate_dependency_table.get_packages_installed_in_environment", return_value=[])
    @patch("generate_dependency_table.subprocess.check_output")
    def test_parallel_error_wraps_package_context(self, mock_check_output, _mock_installed):
        def _raise(*_args, **_kwargs):
            raise RuntimeError("boom")

        mock_check_output.side_effect = _raise
        with self.assertRaises(RuntimeError) as exc:
            get_dependency_ranges_by_package(["explode==1.0.0"], max_workers=4)

        self.assertIn("explode==1.0.0", str(exc.exception))


if __name__ == "__main__":
    unittest.main(verbosity=2)
