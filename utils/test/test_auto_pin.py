#!/usr/bin/env python
"""
Unit tests for auto-pin functionality in pipeline_utils.py.

Tests the constraint parsing and version resolution logic that ensures
packages.txt always contains the latest versions satisfying constraints.
"""

import os
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

# Add the utils directory to the path so we can import module functions.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from packaging.specifiers import SpecifierSet

from pipeline_utils import (
    parse_constraints,
    fetch_all_versions_from_pypi,
    find_highest_satisfying_version,
    auto_pin_packages_to_latest,
    get_current_pyhc_pins,
    parse_direct_requirements_from_lockfile,
    detect_package_set_changes,
    update_packages_txt_with_pins,
)


class TestParseConstraints(unittest.TestCase):
    """Tests for parse_constraints() function."""

    def _write_constraints(self, content: str) -> str:
        """Write content to a temp file and return the path."""
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_parse_not_equal_constraint(self):
        """Test parsing != constraints."""
        path = self._write_constraints("sciqlop!=0.10.4\n")
        try:
            constraints = parse_constraints(path)
            self.assertIn("sciqlop", constraints)
            self.assertIsInstance(constraints["sciqlop"], SpecifierSet)
            self.assertNotIn("0.10.4", constraints["sciqlop"])
            self.assertIn("0.10.3", constraints["sciqlop"])
            self.assertIn("0.10.5", constraints["sciqlop"])
        finally:
            os.unlink(path)

    def test_parse_less_than_constraint(self):
        """Test parsing < constraints."""
        path = self._write_constraints("pyrfu<2.4.18\n")
        try:
            constraints = parse_constraints(path)
            self.assertIn("pyrfu", constraints)
            self.assertNotIn("2.4.18", constraints["pyrfu"])
            self.assertNotIn("2.4.19", constraints["pyrfu"])
            self.assertIn("2.4.17", constraints["pyrfu"])
            self.assertIn("2.4.0", constraints["pyrfu"])
        finally:
            os.unlink(path)

    def test_parse_less_than_or_equal_constraint(self):
        """Test parsing <= constraints."""
        path = self._write_constraints("numpy<=1.26.4\n")
        try:
            constraints = parse_constraints(path)
            self.assertIn("numpy", constraints)
            self.assertIn("1.26.4", constraints["numpy"])
            self.assertNotIn("1.26.5", constraints["numpy"])
            self.assertIn("1.26.0", constraints["numpy"])
        finally:
            os.unlink(path)

    def test_parse_greater_than_constraint(self):
        """Test parsing > constraints."""
        path = self._write_constraints("requests>2.0\n")
        try:
            constraints = parse_constraints(path)
            self.assertIn("requests", constraints)
            self.assertNotIn("2.0", constraints["requests"])
            self.assertNotIn("1.9", constraints["requests"])
            self.assertIn("2.1", constraints["requests"])
        finally:
            os.unlink(path)

    def test_parse_greater_than_or_equal_constraint(self):
        """Test parsing >= constraints."""
        path = self._write_constraints("astropy>=6.0\n")
        try:
            constraints = parse_constraints(path)
            self.assertIn("astropy", constraints)
            self.assertIn("6.0", constraints["astropy"])
            self.assertIn("6.1", constraints["astropy"])
            self.assertNotIn("5.9", constraints["astropy"])
        finally:
            os.unlink(path)

    def test_parse_exact_version_constraint(self):
        """Test parsing == constraints (freeze at exact version)."""
        path = self._write_constraints("scipy==1.10.0\n")
        try:
            constraints = parse_constraints(path)
            self.assertIn("scipy", constraints)
            self.assertIn("1.10.0", constraints["scipy"])
            self.assertNotIn("1.10.1", constraints["scipy"])
            self.assertNotIn("1.9.0", constraints["scipy"])
        finally:
            os.unlink(path)

    def test_parse_compound_constraint(self):
        """Test parsing compound constraints like >=1.0,<2.0."""
        path = self._write_constraints("xarray>=2024.1.0,<2025.0.0\n")
        try:
            constraints = parse_constraints(path)
            self.assertIn("xarray", constraints)
            self.assertIn("2024.6.0", constraints["xarray"])
            self.assertNotIn("2023.12.0", constraints["xarray"])
            self.assertNotIn("2025.1.0", constraints["xarray"])
        finally:
            os.unlink(path)

    def test_parse_multiple_constraints(self):
        """Test parsing multiple packages with different constraint types."""
        content = """# Block broken versions
sciqlop!=0.10.4
pyrfu<2.4.18
numpy<=1.26.4
"""
        path = self._write_constraints(content)
        try:
            constraints = parse_constraints(path)
            self.assertEqual(len(constraints), 3)
            self.assertIn("sciqlop", constraints)
            self.assertIn("pyrfu", constraints)
            self.assertIn("numpy", constraints)
        finally:
            os.unlink(path)

    def test_parse_ignores_comments_and_empty_lines(self):
        """Test that comments and empty lines are ignored."""
        content = """# This is a comment
sciqlop!=0.10.4

# Another comment
pyrfu<2.4.18
"""
        path = self._write_constraints(content)
        try:
            constraints = parse_constraints(path)
            self.assertEqual(len(constraints), 2)
        finally:
            os.unlink(path)

    def test_parse_inline_comments(self):
        """Test that inline comments are handled."""
        path = self._write_constraints("sciqlop!=0.10.4  # broken version\n")
        try:
            constraints = parse_constraints(path)
            self.assertIn("sciqlop", constraints)
            # Make sure the comment didn't break parsing
            self.assertNotIn("0.10.4", constraints["sciqlop"])
        finally:
            os.unlink(path)

    def test_parse_nonexistent_file_returns_empty(self):
        """Test that a nonexistent file returns empty dict."""
        constraints = parse_constraints("/nonexistent/path/constraints.txt")
        self.assertEqual(constraints, {})

    def test_parse_case_insensitive_package_names(self):
        """Test that package names are normalized to lowercase."""
        path = self._write_constraints("SciQLop!=0.10.4\n")
        try:
            constraints = parse_constraints(path)
            self.assertIn("sciqlop", constraints)
            self.assertNotIn("SciQLop", constraints)
        finally:
            os.unlink(path)


class TestFetchAllVersionsFromPyPI(unittest.TestCase):
    """Tests for fetch_all_versions_from_pypi() function."""

    @patch("pipeline_utils.requests.get")
    def test_fetch_returns_version_list(self, mock_get):
        """Test that fetch returns a list of versions."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "releases": {
                "1.0.0": [],
                "1.1.0": [],
                "2.0.0": [],
            }
        }
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response

        versions = fetch_all_versions_from_pypi("test-package")

        self.assertIsInstance(versions, list)
        self.assertEqual(set(versions), {"1.0.0", "1.1.0", "2.0.0"})

    @patch("pipeline_utils.requests.get")
    def test_fetch_returns_none_on_error(self, mock_get):
        """Test that fetch returns None on request error."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        versions = fetch_all_versions_from_pypi("test-package")

        self.assertIsNone(versions)


class TestFindHighestSatisfyingVersion(unittest.TestCase):
    """Tests for find_highest_satisfying_version() function."""

    @patch("pipeline_utils.fetch_all_versions_from_pypi")
    def test_find_highest_with_less_than_constraint(self, mock_fetch):
        """Test finding highest version with < constraint."""
        mock_fetch.return_value = [
            "2.4.15", "2.4.16", "2.4.17", "2.4.18", "2.4.19"
        ]

        constraint = SpecifierSet("<2.4.18")
        result = find_highest_satisfying_version("pyrfu", constraint)

        self.assertEqual(result, "2.4.17")

    @patch("pipeline_utils.fetch_all_versions_from_pypi")
    def test_find_highest_with_not_equal_constraint(self, mock_fetch):
        """Test finding highest version with != constraint."""
        mock_fetch.return_value = [
            "0.10.1", "0.10.2", "0.10.3", "0.10.4"
        ]

        constraint = SpecifierSet("!=0.10.4")
        result = find_highest_satisfying_version("sciqlop", constraint)

        self.assertEqual(result, "0.10.3")

    @patch("pipeline_utils.fetch_all_versions_from_pypi")
    def test_find_highest_with_compound_constraint(self, mock_fetch):
        """Test finding highest version with compound constraint."""
        mock_fetch.return_value = [
            "1.0.0", "1.5.0", "2.0.0", "2.5.0", "3.0.0"
        ]

        constraint = SpecifierSet(">=1.0,<2.5")
        result = find_highest_satisfying_version("pkg", constraint)

        self.assertEqual(result, "2.0.0")

    @patch("pipeline_utils.fetch_all_versions_from_pypi")
    def test_find_highest_with_exact_version_constraint(self, mock_fetch):
        """Test finding version with == constraint (freeze behavior)."""
        mock_fetch.return_value = [
            "1.0.0", "1.5.0", "2.0.0", "2.5.0", "3.0.0"
        ]

        constraint = SpecifierSet("==2.0.0")
        result = find_highest_satisfying_version("pkg", constraint)

        # Only 2.0.0 satisfies ==2.0.0
        self.assertEqual(result, "2.0.0")

    @patch("pipeline_utils.fetch_all_versions_from_pypi")
    def test_find_highest_skips_prereleases(self, mock_fetch):
        """Test that pre-releases are skipped."""
        mock_fetch.return_value = [
            "1.0.0", "1.1.0", "1.2.0a1", "1.2.0b2", "1.2.0rc1"
        ]

        constraint = SpecifierSet(">=1.0")
        result = find_highest_satisfying_version("pkg", constraint)

        self.assertEqual(result, "1.1.0")

    @patch("pipeline_utils.fetch_all_versions_from_pypi")
    def test_find_highest_skips_dev_releases(self, mock_fetch):
        """Test that dev releases are skipped."""
        mock_fetch.return_value = [
            "1.0.0", "1.1.0", "1.2.0.dev1", "1.2.0.dev2"
        ]

        constraint = SpecifierSet(">=1.0")
        result = find_highest_satisfying_version("pkg", constraint)

        self.assertEqual(result, "1.1.0")

    @patch("pipeline_utils.fetch_all_versions_from_pypi")
    def test_find_returns_none_when_no_version_satisfies(self, mock_fetch):
        """Test that None is returned when no version satisfies constraint."""
        mock_fetch.return_value = ["1.0.0", "2.0.0", "3.0.0"]

        constraint = SpecifierSet(">=10.0")
        result = find_highest_satisfying_version("pkg", constraint)

        self.assertIsNone(result)

    @patch("pipeline_utils.fetch_all_versions_from_pypi")
    def test_find_returns_none_on_fetch_error(self, mock_fetch):
        """Test that None is returned when PyPI fetch fails."""
        mock_fetch.return_value = None

        constraint = SpecifierSet(">=1.0")
        result = find_highest_satisfying_version("pkg", constraint)

        self.assertIsNone(result)

    @patch("pipeline_utils.fetch_all_versions_from_pypi")
    def test_find_handles_invalid_version_strings(self, mock_fetch):
        """Test that invalid version strings are skipped."""
        mock_fetch.return_value = [
            "1.0.0", "invalid", "2.0.0", "also-invalid", "3.0.0"
        ]

        constraint = SpecifierSet(">=1.0")
        result = find_highest_satisfying_version("pkg", constraint)

        self.assertEqual(result, "3.0.0")


class TestAutoPinPackagesToLatest(unittest.TestCase):
    """Tests for auto_pin_packages_to_latest() function."""

    def _create_temp_files(self, packages_content: str, constraints_content: str = ""):
        """Create temporary packages.txt and constraints.txt files."""
        # Create a temp directory
        self.temp_dir = tempfile.mkdtemp()

        packages_path = os.path.join(self.temp_dir, "packages.txt")
        with open(packages_path, "w") as f:
            f.write(packages_content)

        constraints_path = os.path.join(self.temp_dir, "constraints.txt")
        with open(constraints_path, "w") as f:
            f.write(constraints_content)

        return packages_path, constraints_path

    def _cleanup_temp_files(self):
        """Clean up temporary files."""
        import shutil
        if hasattr(self, 'temp_dir') and os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def tearDown(self):
        self._cleanup_temp_files()

    @patch("pipeline_utils.fetch_all_latest_versions")
    def test_auto_pin_updates_to_latest_when_no_constraints(self, mock_fetch_latest):
        """Test that packages are pinned to latest when no constraints exist."""
        packages_content = """# Test packages
alpha==1.0.0
beta==2.0.0
"""
        packages_path, constraints_path = self._create_temp_files(packages_content)

        mock_fetch_latest.return_value = {
            "alpha": "1.1.0",
            "beta": "2.1.0",
        }

        changes = auto_pin_packages_to_latest(packages_path, constraints_path)

        self.assertEqual(len(changes), 2)
        self.assertEqual(changes["alpha"], ("1.0.0", "1.1.0"))
        self.assertEqual(changes["beta"], ("2.0.0", "2.1.0"))

        # Verify file was updated
        with open(packages_path) as f:
            content = f.read()
        self.assertIn("alpha==1.1.0", content)
        self.assertIn("beta==2.1.0", content)

    @patch("pipeline_utils.find_highest_satisfying_version")
    @patch("pipeline_utils.fetch_all_latest_versions")
    def test_auto_pin_finds_valid_version_when_latest_blocked(self, mock_fetch_latest, mock_find_highest):
        """Test that a valid version is found when latest is blocked."""
        packages_content = "pyrfu==2.4.17\n"
        constraints_content = "pyrfu<2.4.18\n"
        packages_path, constraints_path = self._create_temp_files(
            packages_content, constraints_content
        )

        mock_fetch_latest.return_value = {"pyrfu": "2.4.19"}
        mock_find_highest.return_value = "2.4.17"

        changes = auto_pin_packages_to_latest(packages_path, constraints_path)

        # Should call find_highest_satisfying_version since latest is blocked
        mock_find_highest.assert_called_once()

        # No changes since current version is already the highest valid
        self.assertEqual(len(changes), 0)

    @patch("pipeline_utils.find_highest_satisfying_version")
    @patch("pipeline_utils.fetch_all_latest_versions")
    def test_auto_pin_updates_to_highest_valid_version(self, mock_fetch_latest, mock_find_highest):
        """Test that package is updated to highest valid version when latest blocked."""
        packages_content = "pyrfu==2.4.15\n"
        constraints_content = "pyrfu<2.4.18\n"
        packages_path, constraints_path = self._create_temp_files(
            packages_content, constraints_content
        )

        mock_fetch_latest.return_value = {"pyrfu": "2.4.19"}
        mock_find_highest.return_value = "2.4.17"

        changes = auto_pin_packages_to_latest(packages_path, constraints_path)

        self.assertEqual(len(changes), 1)
        self.assertEqual(changes["pyrfu"], ("2.4.15", "2.4.17"))

        # Verify file was updated
        with open(packages_path) as f:
            content = f.read()
        self.assertIn("pyrfu==2.4.17", content)

    @patch("pipeline_utils.find_highest_satisfying_version")
    @patch("pipeline_utils.fetch_all_latest_versions")
    def test_auto_pin_freezes_at_exact_version_constraint(self, mock_fetch_latest, mock_find_highest):
        """Test that == constraint freezes package at exact version."""
        packages_content = "frozen-pkg==1.5.0\n"
        constraints_content = "frozen-pkg==1.5.0\n"  # Freeze at this exact version
        packages_path, constraints_path = self._create_temp_files(
            packages_content, constraints_content
        )

        # Latest on PyPI is 2.0.0, but we're frozen at 1.5.0
        mock_fetch_latest.return_value = {"frozen-pkg": "2.0.0"}
        mock_find_highest.return_value = "1.5.0"  # Only 1.5.0 satisfies ==1.5.0

        changes = auto_pin_packages_to_latest(packages_path, constraints_path)

        # Should call find_highest since latest (2.0.0) doesn't satisfy ==1.5.0
        mock_find_highest.assert_called_once()

        # No changes since we're already at the frozen version
        self.assertEqual(len(changes), 0)

        # Verify file still has frozen version
        with open(packages_path) as f:
            content = f.read()
        self.assertIn("frozen-pkg==1.5.0", content)
        self.assertNotIn("frozen-pkg==2.0.0", content)

    @patch("pipeline_utils.find_highest_satisfying_version")
    @patch("pipeline_utils.fetch_all_latest_versions")
    def test_auto_pin_raises_when_no_valid_version(self, mock_fetch_latest, mock_find_highest):
        """Test that RuntimeError is raised when no version satisfies constraint."""
        packages_content = "impossible==1.0.0\n"
        constraints_content = "impossible<0.0.1\n"  # No version can satisfy this
        packages_path, constraints_path = self._create_temp_files(
            packages_content, constraints_content
        )

        mock_fetch_latest.return_value = {"impossible": "2.0.0"}
        mock_find_highest.return_value = None  # No valid version found

        with self.assertRaises(RuntimeError) as exc:
            auto_pin_packages_to_latest(packages_path, constraints_path)

        self.assertIn("impossible", str(exc.exception))
        self.assertIn("No version", str(exc.exception))

    @patch("pipeline_utils.fetch_all_latest_versions")
    def test_auto_pin_preserves_extras(self, mock_fetch_latest):
        """Test that package extras are preserved during auto-pin."""
        packages_content = "pyhc-core[tests]==0.0.6\n"
        packages_path, constraints_path = self._create_temp_files(packages_content)

        mock_fetch_latest.return_value = {"pyhc-core": "0.0.7"}

        changes = auto_pin_packages_to_latest(packages_path, constraints_path)

        self.assertEqual(len(changes), 1)

        # Verify extras are preserved
        with open(packages_path) as f:
            content = f.read()
        self.assertIn("pyhc-core[tests]==0.0.7", content)

    @patch("pipeline_utils.fetch_all_latest_versions")
    def test_auto_pin_no_changes_when_already_latest(self, mock_fetch_latest):
        """Test that no changes occur when already at latest."""
        packages_content = "alpha==1.0.0\n"
        packages_path, constraints_path = self._create_temp_files(packages_content)

        mock_fetch_latest.return_value = {"alpha": "1.0.0"}

        changes = auto_pin_packages_to_latest(packages_path, constraints_path)

        self.assertEqual(len(changes), 0)

    @patch("pipeline_utils.fetch_all_latest_versions")
    def test_auto_pin_skips_commented_packages(self, mock_fetch_latest):
        """Test that commented-out packages are skipped."""
        packages_content = """alpha==1.0.0
# beta==2.0.0  # excluded
"""
        packages_path, constraints_path = self._create_temp_files(packages_content)

        mock_fetch_latest.return_value = {"alpha": "1.1.0"}

        changes = auto_pin_packages_to_latest(packages_path, constraints_path)

        # Only alpha should be updated
        self.assertEqual(len(changes), 1)
        self.assertIn("alpha", changes)
        self.assertNotIn("beta", changes)


class TestGetCurrentPyhcPins(unittest.TestCase):
    """Tests for get_current_pyhc_pins() function."""

    def _write_packages(self, content: str) -> str:
        """Write content to a temp file and return the path."""
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_parse_pinned_package(self):
        """Test parsing a simple pinned package."""
        path = self._write_packages("requests==2.28.0\n")
        try:
            pins = get_current_pyhc_pins(path)
            self.assertIn("requests", pins)
            self.assertEqual(pins["requests"]["version"], "2.28.0")
        finally:
            os.unlink(path)

    def test_parse_package_with_extras(self):
        """Test parsing a package with extras."""
        path = self._write_packages("pyhc-core[tests]==0.0.7\n")
        try:
            pins = get_current_pyhc_pins(path)
            self.assertIn("pyhc-core", pins)
            self.assertEqual(pins["pyhc-core"]["version"], "0.0.7")
            self.assertEqual(pins["pyhc-core"]["extras"], "[tests]")
        finally:
            os.unlink(path)

    def test_parse_package_with_inline_comment(self):
        """Test parsing a package with inline comment."""
        path = self._write_packages("sciqlop==0.10.3  # v0.10.4 blocked\n")
        try:
            pins = get_current_pyhc_pins(path)
            self.assertIn("sciqlop", pins)
            self.assertEqual(pins["sciqlop"]["version"], "0.10.3")
        finally:
            os.unlink(path)

    def test_skips_comments_and_empty_lines(self):
        """Test that comments and empty lines are skipped."""
        content = """# Header comment
requests==2.28.0

# Another comment
numpy==1.24.0
"""
        path = self._write_packages(content)
        try:
            pins = get_current_pyhc_pins(path)
            self.assertEqual(len(pins), 2)
            self.assertIn("requests", pins)
            self.assertIn("numpy", pins)
        finally:
            os.unlink(path)

    def test_normalizes_package_names_to_lowercase(self):
        """Test that package names are normalized to lowercase."""
        path = self._write_packages("SciQLop==0.10.3\n")
        try:
            pins = get_current_pyhc_pins(path)
            self.assertIn("sciqlop", pins)
            self.assertNotIn("SciQLop", pins)
        finally:
            os.unlink(path)


class TestPackageSetChangeDetection(unittest.TestCase):
    """Tests for lockfile direct requirement parsing and package set drift checks."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _write_file(self, filename: str, content: str) -> str:
        path = os.path.join(self.temp_dir, filename)
        with open(path, "w") as f:
            f.write(content)
        return path

    def test_parse_direct_requirements_from_lockfile(self):
        """Direct requirements should be those with '-r ...packages.txt' in via blocks."""
        lockfile_content = """alpha==1.0.0
    # via
    #   -r docker/pyhc-environment/contents/packages.txt
beta==2.0.0
    # via
    #   alpha
gamma==3.0.0
    # via
    #   -r packages.txt
"""
        lockfile_path = self._write_file("resolved-versions.txt", lockfile_content)

        direct = parse_direct_requirements_from_lockfile(lockfile_path)
        self.assertEqual(direct, {"alpha": "1.0.0", "gamma": "3.0.0"})

    def test_detect_package_set_changes_add_remove_and_ignore_version_only_edits(self):
        """Add/remove should be detected; same-name version edits should not appear as set changes."""
        packages_content = """alpha==1.1.0
gamma==3.0.0
"""
        lockfile_content = """alpha==1.0.0
    # via
    #   -r docker/pyhc-environment/contents/packages.txt
beta==2.0.0
    # via
    #   -r docker/pyhc-environment/contents/packages.txt
"""
        packages_path = self._write_file("packages.txt", packages_content)
        lockfile_path = self._write_file("resolved-versions.txt", lockfile_content)

        changes = detect_package_set_changes(packages_path, lockfile_path)

        self.assertEqual(changes["added"], {"gamma": "3.0.0"})
        self.assertEqual(changes["removed"], {"beta": "2.0.0"})
        self.assertNotIn("alpha", changes["added"])
        self.assertNotIn("alpha", changes["removed"])

    def test_detect_package_set_changes_version_only_edit_is_noop(self):
        """If package names match, set change detector should report no changes."""
        packages_content = "alpha==1.1.0\n"
        lockfile_content = """alpha==1.0.0
    # via
    #   -r docker/pyhc-environment/contents/packages.txt
"""
        packages_path = self._write_file("packages.txt", packages_content)
        lockfile_path = self._write_file("resolved-versions.txt", lockfile_content)

        changes = detect_package_set_changes(packages_path, lockfile_path)

        self.assertEqual(changes["added"], {})
        self.assertEqual(changes["removed"], {})

    def test_detect_package_set_changes_missing_lockfile_marks_all_added(self):
        """Missing lockfile should trigger a run by marking all current packages as added."""
        packages_content = """alpha==1.0.0
beta
"""
        packages_path = self._write_file("packages.txt", packages_content)
        lockfile_path = os.path.join(self.temp_dir, "missing-resolved-versions.txt")

        changes = detect_package_set_changes(packages_path, lockfile_path)

        self.assertEqual(changes["removed"], {})
        self.assertEqual(changes["added"], {"alpha": "1.0.0", "beta": None})


class TestUpdatePackagesTxtWithPins(unittest.TestCase):
    """Tests for update_packages_txt_with_pins() function."""

    def _write_packages(self, content: str) -> str:
        """Write content to a temp file and return the path."""
        fd, path = tempfile.mkstemp(suffix=".txt")
        with os.fdopen(fd, "w") as f:
            f.write(content)
        return path

    def test_update_preserves_comments(self):
        """Test that comments are preserved during update."""
        content = """# Header
requests==2.28.0
# Footer
"""
        path = self._write_packages(content)
        try:
            update_packages_txt_with_pins(path, {"requests": "2.29.0"})
            with open(path) as f:
                result = f.read()
            self.assertIn("# Header", result)
            self.assertIn("# Footer", result)
            self.assertIn("requests==2.29.0", result)
        finally:
            os.unlink(path)

    def test_update_preserves_extras(self):
        """Test that extras are preserved during update."""
        content = "pyhc-core[tests]==0.0.6\n"
        path = self._write_packages(content)
        try:
            update_packages_txt_with_pins(path, {"pyhc-core": "0.0.7"})
            with open(path) as f:
                result = f.read()
            self.assertIn("pyhc-core[tests]==0.0.7", result)
        finally:
            os.unlink(path)

    def test_update_preserves_inline_comments(self):
        """Test that inline comments are preserved during update."""
        content = "sciqlop==0.10.3  # blocked version\n"
        path = self._write_packages(content)
        try:
            update_packages_txt_with_pins(path, {"sciqlop": "0.10.5"})
            with open(path) as f:
                result = f.read()
            self.assertIn("sciqlop==0.10.5", result)
            self.assertIn("# blocked version", result)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
