#! /usr/bin/env python
"""
Script to generate table of PyHC package dependency conflicts.

__authors__ = ["Shawn Polson"]
"""


import openpyxl
from openpyxl.styles import PatternFill
from packaging.specifiers import SpecifierSet
from packaging.specifiers import Specifier
from packaging.version import Version
from packaging.version import InvalidVersion
import pandas as pd

import re
import subprocess


# TODO: get fisspy pipdeptree via conda (get-dep-tree-for-fisspy-w-conda.sh)
# TODO: sort final spreadsheet by lowercased names.

# TODO: Versions with wildcards * break everything.
#   Note: String comparison basically works if one version has * in it.
#   Idea: Can I just remove the * from the version when I encounter it? e.g. 5.0.* -> 5.0 (and still keep * in the eventual output?)
#   What I'm doing currently: just removing * from versions for now; pretending like they don't exist

# TODO: Naming consideration: "project" = a (PyHC) package that gets its own table column,
#                             "package" = a (dependency) package that gets its own table row
#                             "dependency" = a combination of a "package" and a "version range"
#                             "version range" = a range like ">=1.5,2.0,!=1.6.*"
#                             vs
#                             "package" = any Python package
#                             "dependency" = a (dependency) package that gets its own table row
#                             "version range" = a range like ">=1.5,2.0,!=1.6.*"


def generate_requirements_file():
    package_names = get_core_pyhc_packages() + get_other_pyhc_packages()
    exclude = ["fisspy", "geopack", "ncarglow", "hwm93", "madrigalWeb", "maidenhead", "mgsutils", "pymap3d", "pysatCDF", "SkyWinder", "SkyWinder-Analysis", "TomograPy"]

    requirements = [name for name in package_names if name not in exclude]
    for package in requirements:
        print(package)
    return requirements


def get_core_pyhc_packages():
    """
    TODO: consider scraping this from projects_core.yml online?
    :return: A list of the core PyHC package names.
    """
    return ["hapiclient", "kamodo", "plasmapy", "pysat", "pyspedas", "spacepy", "sunpy"]


def get_other_pyhc_packages():
    """
    TODO: consider scraping this from projects.yml online? Would have to account for unpublished packages.
    Note, the following packages are missing because they are not in PyPI:
    ACEmag, AFINO, Auroral Electrojet (AEindex), fisspy, geodata, GIMAmag (gima-magnetometer), hwm93 (archived 2022),
    iri90 (archived 2022), POLAN (archived 2022), MGSutils (archived 2022), ncarglow, PyGemini, pyglow, PyGS,
    python-magnetosphere, sami2py, scanning-doppler-interferometer (archived 2022), TomograPy.

    :return: A list of the other non-core PyHC package names.

    TODO: Missing one new package (because python-casacore is challenging):
    lofarSun

    TODO:
    heliopy is hardcoded to 0.15.4 because 1.0.0 is deprecated.
    pysatCDF has been removed due to installation failures.
    OMMBV has been removed due to installation failures.
    pyrfu has not been added yet because its cdflib and numpy versions are too high for other packages.
    """
    return ["aacgmv2", "aiapy", "aidapy", "amisrsynthdata", "apexpy", "astrometry-azel", "ccsdspy", "cdflib", "cloudcatalog", "dascutils", "dbprocessing", "dmsp", "enlilviz", "fiasco", "geopack", "georinex", "geospacelab", "goesutils", "heliopy==0.15.4", "hissw", "igrf", "iri2016", "irispy-lmsal", "lowtran", "madrigalWeb", "maidenhead", "mcalf", "msise00", "ndcube", "nexradutils", "ocbpy", "pyaurorax", "pycdfpp", "pydarn", "pyflct", "pymap3d", "pytplot", "pytplot-mpl-temp", "pyzenodo3", "reesaurora", "regularizepsf", "savic", "sciencedates", "SciQLop", "SkyWinder", "solarmach", "solo-epd-loader", "space-packet-parser", "speasy", "spiceypy", "sunkit-image", "sunkit-instruments", "sunraster", "themisasi", "viresclient", "wmm2015", "wmm2020"]


def get_supplementary_packages():
    """
    :return: A list of supplementary packages, including optional dependencies not found by pipdeptree
             and those used for unit tests.
    """
    return ["deepdiff", "hypothesis", "pytest-arraydiff", "pytest-doctestplus", "pytest-xdist", "setuptools-scm"]


# def spreadsheet_to_requirements_file_orig(spreadsheet):
#     # Extract PyHC package names (from the top row, excluding the first two columns)
#     # Remove '==' only if it appears at the end and is not followed by a version number
#     pyhc_packages = []
#     for pkg in spreadsheet.columns[2:]:
#         if pkg.endswith("=="):
#             pkg = pkg.replace("==", "")  # Remove '==' if no version number follows
#         pyhc_packages.append(pkg)
#
#     # Extract package names and their allowed version ranges
#     requirements = []
#     for index, row in spreadsheet.iterrows():
#         package = row['Package']
#         version_range = row['Allowed Version Range']
#         if pd.notna(version_range):
#             # Handle "Any" version specifier
#             if version_range.strip().lower() == 'any':
#                 requirement = package  # No version specifier for 'Any'
#             else:
#                 # Ensure no whitespace before '=='
#                 version_range = version_range.replace(" ", "")
#                 requirement = f"{package}{version_range}"
#             requirements.append(requirement)
#
#         # Remove duplicates: if a package from pyhc_packages is already in requirements, remove its version range
#         for pyhc_package in pyhc_packages:
#             # Extract package name from PyHC package, considering potential version specifier
#             pyhc_package_name = pyhc_package.split("==")[0] if "==" in pyhc_package else pyhc_package
#
#             # Find and remove any existing version of this package in requirements
#             requirements = [req for req in requirements if not req.startswith(pyhc_package_name)]
#
#     # Add PyHC packages to the requirements
#     requirements.extend(pyhc_packages)
#
#     # Alphabetize the list of requirements
#     requirements.sort(key=str.lower)
#
#     # Format as a requirements.txt content
#     requirements_txt = "\n".join(requirements)
#     return requirements_txt


def spreadsheet_to_requirements_file(spreadsheet_path):
    spreadsheet = pd.read_excel(spreadsheet_path, sheet_name=0)

    # Extract package names and their allowed version ranges
    requirements = []
    for index, row in spreadsheet.iterrows():
        package = row['Package']
        version_range = row['Allowed Version Range']

        # Check for "N/A" or NaN which indicates a conflict
        if pd.isna(version_range) or version_range.strip().lower() == 'n/a':
            raise ValueError(f"Cannot create a requirements file from the spreadsheet because there is a dependency conflict (with package `{package}`).")

        # Handle "Any" version specifier
        if version_range.strip().lower() == 'any':
            requirement = package  # No version specifier for 'Any'
        else:
            # Ensure no whitespace before version specifiers
            version_range = version_range.replace(" ", "")
            requirement = f"{package}{version_range}"
        requirements.append(requirement)

    # Alphabetize the list of requirements
    requirements.sort(key=str.lower)

    # Format as a requirements.txt content
    requirements_txt = "\n".join(requirements)
    return requirements_txt


def get_packages_installed_in_environment():
    """
    :return: A lowercased list of the package names output by `pip list`.
    """
    def parse_package_name(line):
        return line.strip().split(" ")[0].lower()

    pip_list_output = subprocess.check_output('pip list', shell=True).decode('utf-8')
    package_lines = pip_list_output.split("\n")[2:]
    return list(map(parse_package_name, package_lines))


def test_combine_ranges():
    r1 = combine_ranges(">=1.1.1", "any")
    r2 = combine_ranges("any", ">=1.1.2")
    r3 = combine_ranges(">=1.5", ">1.5,<2")
    r4 = combine_ranges(">1.1.1", "==1.2.3")
    r5 = combine_ranges("<1.1.1", ">=1.2.3,<2.0")
    r6 = combine_ranges(">=1.1.1", ">=1.2.3,<2.0")
    r7 = combine_ranges(">=1.2.3,<2", ">=1.1.1")
    r8 = combine_ranges("==1.1.2", ">=0.9")
    r9 = combine_ranges("==1.1.2", "<2")
    r10= combine_ranges(">=1.9", ">=1.21.0")
    r11= combine_ranges(">=1.9", ">=1.19.5,<1.27.0")
    r12= combine_ranges(">=1.21.0", ">=1.19.5,<1.27.0")
    r13= combine_ranges(">=4.9.2", ">=4.12,!=5.0.*")  # TODO: how should I handle * wildcards?
    pass


def combine_ranges(current_range, new_range):
    """
    Combine the given ranges if they're compatible, otherwise raise a RuntimeError.
    :param current_range: String like ">=1.5.0,<2.0,!=1.6"
    :param new_range: String ">=1.5.0,<1.9"
    :return: String like ">=1.5.0,<1.9,!=1.6" or RuntimeError
    """
    if str(current_range).lower() == "any":
        return new_range
    if str(new_range).lower() == "any":
        return current_range

    temp_rules = SpecifierSet(current_range)
    new_rules = SpecifierSet(new_range)

    for new_rule in new_rules:
        if rule_is_compatible(temp_rules, new_rule):
            temp_rules = update_range(temp_rules, new_rule)
        else:
            raise RuntimeError(f"Found incompatibility: {new_range}")
    return str(temp_rules)


def update_range(current_range, new_rule):
    """
    Assuming new_rule is compatible with current_range, update current_range if new_rule requires it.
    Note: "any" rules are not supported (they should've been handled in `combine_ranges` by the time we reach here).
    :param current_range: SpecifierSet representing the currently-allowed version ranges for a given package.
    :param new_rule: A Specifier representing a new version requirement rule for the same package.
    :return: A SpecifierSet of the possibly-updated current_range.
    """
    op = new_rule.operator
    v = Version(new_rule.version)

    if op == "==":
        if v in current_range:
            return SpecifierSet(str(new_rule))  # current_range becomes '==v'
        else:
            return current_range
    elif op == "!=":
        for spec in current_range:
            if spec == Specifier(f"=={v}"):
                return current_range
        return update_exclusions(current_range, new_rule)  # Add exclusion '!=v' if it's not already there
    elif op == "~=":
        if compatible_release_is_compatible(current_range, v):
            return enforce_compatible_release(current_range, new_rule)  # TODO: v might update current_range's lower/upper bounds
        else:
            return current_range
    elif op == ">" or op == ">=":
        if lower_bound_is_compatible(current_range, new_rule):
            return update_lower_bound(current_range, new_rule)  # new_rule might update/become current_range's lower bound
        else:
            return current_range
    elif op == "<" or op == "<=":
        if upper_bound_is_compatible(current_range, new_rule):
            return update_upper_bound(current_range, new_rule)  # new_rule might update/become current_range's upper bound
        else:
            return current_range


def rule_is_compatible(current_range, new_rule):
    """
    :param current_range: e.g. SpecifierSet(">=1.6,<2.0")
    :param new_rule: Specifier("==1.7")
    :return: Boolean for whether new_rule is compatible with current_range
    """
    op = new_rule.operator
    v = Version(new_rule.version)

    # TODO: clean up if/else/return logic?
    if op == "==":
        if v in current_range:
            return True  # POSSIBLE UPDATE: current_range becomes '==v'
        else:
            return False
    elif op == "!=":
        for spec in current_range:
            if spec == Specifier(f"=={v}"):
                return False
        return True  # POSSIBLE UPDATE: Add exclusion '!=v' (don't add a 2nd time if it's already in current_range)
    elif op == "~=":
        if compatible_release_is_compatible(current_range, v):
            return True  # POSSIBLE UPDATE: v might update current_range's lower/upper bounds
        else:
            return False
    elif op == ">" or op == ">=":
        if lower_bound_is_compatible(current_range, new_rule):
            return True  # POSSIBLE UPDATE: new_rule might update/become current_range's lower bound
        else:
            return False
    elif op == "<" or op == "<=":
        if upper_bound_is_compatible(current_range, new_rule):
            return True  # POSSIBLE UPDATE: new_rule might update/become current_range's upper bound
        else:
            return False


def enforce_compatible_release(current_range, compatible_release_rule):
    """
    TODO: finish me. Consider the case of >=0.5,<=2.0,!=1.0  and ~=1.0
    :param current_range: e.g. SpecifierSet(">=1.6,<2.0")
    :param compatible_release_rule: A Specifier compatible release rule e.g. Specifier("~=1.5")
    :return: A SpecifierSet that's the result of combining current_range with compatible_release_rule
    """
    if len(current_range) == 1 and str(current_range) == str(compatible_release_rule):
        return current_range  # they're both ~=v for the same v so no change

    v_list = list(Version(compatible_release_rule.version).release)
    v_list[-1] = "*"
    v_compatible = ".".join(str(e) for e in v_list)
    v_lower = Version(v_compatible.replace("*", "0"))
    v_upper = Version(v_compatible.replace("*", "999"))
    temp_range = update_lower_bound(current_range, Specifier(f"~={str(v_lower)}"))  # TODO: make Specifier from v_lower
    temp_range = update_upper_bound(temp_range, Specifier(f"~={str(v_upper)}"))     # TODO: make Specifier from v_upper
    return temp_range  #TODO: this doesn't handle every case... like just replacing the upper/lower bounds with the ~=version rule


def update_upper_bound(current_range, upper_bound):
    """
    :param current_range: e.g. SpecifierSet(">=1.6,<2.0")
    :param upper_bound: A Specifier upper bound e.g. Specifier("<1.9")
    :return: A SpecifierSet of the possibly-updated current_range, e.g. SpecifierSet(">=1.6,<1.9")
    """
    rules = str(current_range).split(",")
    current_range_has_upper_bound = False
    for i, rule in enumerate(rules):
        if "<=" in rule:
            current_range_has_upper_bound = True
            if upper_bound.operator == "<" and Version(upper_bound.version) <= Version(Specifier(rule).version):
                rules[i] = str(upper_bound)
            elif upper_bound.operator == "<=" and Version(upper_bound.version) < Version(Specifier(rule).version):
                rules[i] = str(upper_bound)
        elif "<" in rule:
            current_range_has_upper_bound = True
            if Version(upper_bound.version) < Version(Specifier(rule).version):
                rules[i] = str(upper_bound)
        elif "==" in rule:
            return current_range  # '==version' will always trump upper_bound
        elif "~=" in rule:
            # we might separate '~=version' into lower and upper bounds
            if Version(upper_bound.version) < Version(rule.version):
                v_list = list(Version(rule.version).release)
                v_list[-1] = "*"
                v_compatible = ".".join(str(e) for e in v_list)
                v_lower = Version(v_compatible.replace("*", "0"))
                v_upper = Version(v_compatible.replace("*", "999"))
                if v_upper >= Version(upper_bound.version) >= v_lower:
                    current_range_has_upper_bound = True
                    rules[i] = str(upper_bound)
                    rules = str(update_lower_bound(SpecifierSet(",".join(rules)), v_lower)).split(",")
    if not current_range_has_upper_bound:
        rules.append(str(upper_bound))
    return SpecifierSet(",".join(rules))


def update_lower_bound(current_range, lower_bound):
    """
    TODO: handle when current_range is "!=5.0.*,>=4.9.2"?
    :param current_range: e.g. SpecifierSet(">=1.5,<2.0")
    :param lower_bound: A Specifier lower bound e.g. Specifier(">=1.6")
    :return: A SpecifierSet of the possibly-updated current_range, e.g. SpecifierSet(">=1.6,<2.0")
    """
    rules = str(current_range).split(",")
    current_range_has_lower_bound = False
    for i, rule in enumerate(rules):
        if ">=" in rule:
            current_range_has_lower_bound = True
            if lower_bound.operator == ">" and Version(lower_bound.version) >= Version(Specifier(rule).version):
                rules[i] = str(lower_bound)
            elif lower_bound.operator == ">=" and Version(lower_bound.version) > Version(Specifier(rule).version):
                rules[i] = str(lower_bound)
        elif ">" in rule:
            current_range_has_lower_bound = True
            if Version(lower_bound.version) > Version(Specifier(rule).version):
                rules[i] = str(lower_bound)
        elif "==" in rule:
            return current_range  # '==version' will always trump lower_bound
        elif "~=" in rule:
            # we might separate '~=version' into lower and upper bounds
            if Version(lower_bound.version) > Version(rule.version):
                v_list = list(rule.version.release)
                v_list[-1] = "*"
                v_compatible = ".".join(str(e) for e in v_list)
                v_lower = Version(v_compatible.replace("*", "0"))
                v_upper = Version(v_compatible.replace("*", "999"))
                if v_lower <= Version(lower_bound.version) <= v_upper:
                    current_range_has_lower_bound = True
                    rules[i] = str(lower_bound)
                    rules = str(update_upper_bound(SpecifierSet(",".join(rules)), v_upper)).split(",")
    if not current_range_has_lower_bound:
        rules.append(str(lower_bound))
    return SpecifierSet(",".join(rules))


def update_exclusions(current_range, exclusion):
    """
    :param current_range: e.g. SpecifierSet(">=1.6,<2.0")
    :param exclusion: Specifier exclusion e.g. Specifier("!=1.6.0")
    :return: SpecifierSet with exclusion added if it wasn't already in there
    """
    rules = str(current_range).split(",")
    if str(exclusion) in rules:
        return current_range  # exclusion is already in current_range
    else:
        return SpecifierSet(str(current_range) + "," + str(exclusion))  # add exclusion to current_range


def compatible_release_is_compatible(current_range, compatible_release_version):
    """
    :param current_range: e.g. SpecifierSet(">=1.6,<2.0")
    :param compatible_release_version: Version object from a compatible release rule (i.e. Version(v) from '~=v')
    :return: Boolean for whether compatible_release_version is compatible with current_range
    """
    v_list = list(compatible_release_version.release)
    v_list[-1] = "*"
    v_compatible = ".".join(str(e) for e in v_list)
    v_lower = Version(v_compatible.replace("*", "0"))
    v_upper = Version(v_compatible.replace("*", "999"))
    return v_lower in current_range or v_upper in current_range


def lower_bound_is_compatible(current_range, new_lower_bound):
    """
    :param current_range: e.g. SpecifierSet(">=1.6,<2.0")
    :param new_lower_bound: Specifier lower bound e.g. Specifier(">=1.5")
    :return: Boolean for whether new_lower_bound is compatible with current_range
    """
    inclusive = "=" in new_lower_bound.operator
    compatible = True
    for spec in current_range:
        curr_op = spec.operator
        curr_v = Version(spec.version)

        if curr_op == ">" or curr_op == ">=":
            pass
        elif curr_op == "<" or curr_op == "<=":
            if inclusive:
                compatible = Version(new_lower_bound.version) <= curr_v
            else:
                compatible = Version(new_lower_bound.version) < curr_v
            # Additional check to prevent empty intersection:
            if compatible and Version(new_lower_bound.version) == curr_v and new_lower_bound.operator.startswith('>=') and curr_op.startswith('<'):
                compatible = False
        elif curr_op == "==":
            compatible = (Version(new_lower_bound.version) <= curr_v and inclusive) or (Version(new_lower_bound.version) < curr_v)
        elif curr_op == "!=":
            pass
        elif curr_op == "~=":
            v_list = list(curr_v.release)
            v_list[-1] = "*"
            v_compatible = ".".join(str(e) for e in v_list)
            v_lower = Version(v_compatible.replace("*", "0"))
            compatible = Version(new_lower_bound.version) >= v_lower

        if not compatible:
            return False
    return compatible


def upper_bound_is_compatible(current_range, new_upper_bound):
    """
    :param current_range: e.g. SpecifierSet(">=1.6,<2.0")
    :param new_upper_bound: Specifier upper bound e.g. Specifier("<1.9")
    :return: Boolean for whether new_upper_bound is compatible with current_range
    """
    inclusive = "=" in new_upper_bound.operator
    compatible = True
    for spec in current_range:
        curr_op = spec.operator
        curr_v = Version(spec.version)

        if curr_op == "<" or curr_op == "<=":
            pass
        elif curr_op == ">" or curr_op == ">=":
            if inclusive:
                compatible = Version(new_upper_bound.version) >= curr_v
            else:
                compatible = Version(new_upper_bound.version) > curr_v
            # Additional check for empty intersection:
            if compatible and Version(new_upper_bound.version) == curr_v and new_upper_bound.operator.startswith('<=') and curr_op.startswith('>'):
                compatible = False
        elif curr_op == "==":
            compatible = (Version(new_upper_bound.version) >= curr_v and inclusive) or (Version(new_upper_bound.version) > curr_v)
        elif curr_op == "!=":
            pass
        elif curr_op == "~=":
            v_list = list(curr_v.release)
            v_list[-1] = "*"
            v_compatible = ".".join(str(e) for e in v_list)
            v_upper = Version(v_compatible.replace("*", "999"))
            compatible = Version(new_upper_bound.version) <= v_upper

        if not compatible:
            return False
    return compatible


def remove_wildcards(version_range_str):
    """
    Removes any * wildcards from the given versions by removing any occurrences of '.*' from their ends.
    :param version_range_str: String like ">=1.5.0,<2.0,!=1.6.*"
    :return: String like ">=1.5.0,<2.0,!=1.6"
    """
    def remove_wildcard(version_str):
        release = version_str.split(".")
        if release[-1] == "*":
            release.pop()
            return ".".join(release)
        else:
            # raise Exception("remove_wildcard() did not find a * at the end of '" + version_str + "' to remove.")
            return version_str

    versions = version_range_str.split(",")
    return ",".join(list(map(remove_wildcard, versions)))


def determine_version_range(dependencies, package, requirement):
    """
    :param dependencies: Dict like {'package1': '>=1.0', 'package2': '<23.0', ...}
    :param package: String name of a package like 'package1'
    :param requirement: String range like ">=1.5,<2.0"
    :return: A String range like ">=1.5,<2.0" that's either requirement or the (possibly-updated) dependencies[package]
    """
    if package not in dependencies:
        return requirement
    else:
        current_range = dependencies[package]
        new_range = reorder_requirements(combine_ranges(current_range, requirement))
        return new_range


def get_dependency_ranges_by_package(packages, use_installed=False):
    """
    TODO: rename func to "get_dependency_ranges/requirements_for_packages()"?
    TODO: go back to "by project" wording?
    Gets each package's dependency requirements by creating temporary python environments to ensure pip installs work.
    Pre-installed package versions get used when use_installed is True, otherwise the latest package versions get used.
    :param packages: List of packages like ['hapiclient', 'sunpy'] that may not be compatible together
    :param use_installed A Boolean for whether to try to use pre-installed package versions
    :return: Dict like {'hapiclient': {'package1': '>=1.0'}, 'sunpy': {...}} (dependencies sorted alphabetically)
    """
    installed_packages = get_packages_installed_in_environment()
    all_dependencies = {}
    for package in packages:
        if use_installed and package.lower() in installed_packages:
            script_command = f"pipdeptree -p {package}"
        else:
            if package == "pysatCDF":
                # script_command = f"./get-dep-tree-for-pysatCDF-w-numpy.sh {package}"
                # script_command = f"../get-dep-tree-for-pysatCDF-w-numpy.sh {package}"
                script_command = f"./utils/get-dep-tree-for-pysatCDF-w-numpy.sh {package}"
            elif package == "OMMBV":
                script_command = f"./utils/get-dep-tree-for-ommbv.sh {package}"
            elif package == "spacepy":
                script_command = f"./utils/get-dep-tree-for-spacepy.sh {package}"
            # elif package == "fisspy":
            #     script_command = f"./get-dep-tree-for-fisspy-w-conda.sh {package}"
            else:
                # script_command = f"./get-dep-tree-for-package.sh {package}"
                # script_command = f"../get-dep-tree-for-package.sh {package}"
                script_command = f"./utils/get-dep-tree-for-package.sh {package}"
        output = subprocess.check_output(script_command, shell=True)
        output_str = output.decode('utf-8')
        try:
            package_version = output_str.split('\n', 1)[0].split('==')[1]
        except IndexError:
            package_version = ""
        dependencies = {}
        for line in output_str.split("\n"):
            # match = re.match("^\s*-\s*(\S+)\s+\[required:\s+(.+),\s+installed:.+\]", line)
            match = re.match(r"\s*.*?(\S+)\s+\[required:\s+(.+?),\s+installed:.+?\]", line)
            if match:
                name, version_range = match.groups()
                name = name.lower()
                version_range = remove_wildcards(version_range)  # TODO: BEWARE: We pretend wildcards don't exist.
                dependencies[name] = determine_version_range(dependencies, name, version_range)
        dependencies[package.split('==')[0]] = f"=={package_version}"  # each top row package lists itself as dependency
        sorted_dependencies = {key: value for key, value in sorted(dependencies.items())}
        package_w_version = f"{package}=={package_version}" if "==" not in package else package
        all_dependencies[package_w_version] = sorted_dependencies  # If I include the package version here it'll end up in the spreadsheet
    return all_dependencies


def get_dependency_ranges_for_environment(env_packages, full_path_to_pipdeptree=None):
    """
    TODO: rename func to "find_common_environment_dependency_ranges/requirements()"
    :param env_packages: List of packages like ['hapiclient', 'sunpy'] expected to already be installed in the env
    :param full_path_to_pipdeptree: E.g. "/Users/shpo9723/opt/anaconda3/envs/pyhc-deps-1/bin/pipdeptree"
    :return: Dict like {'package1': '>=1.0', 'package2': '<23.0', ...} (sorted alphabetically)
    """
    pipdeptree_path = full_path_to_pipdeptree if full_path_to_pipdeptree else "pipdeptree"
    dependencies = {}
    for package in env_packages:
        command = f"{pipdeptree_path} -p {package}"
        output = subprocess.check_output(command, shell=True)
        output_str = output.decode('utf-8')
        for line in output_str.split("\n"):
            match = re.match("^\s*-\s*(\S+)\s+\[required:\s+(.+),\s+installed:.+\]", line)
            if match:
                name, version_range = match.groups()
                name = name.lower()
                version_range = remove_wildcards(version_range)  # TODO: BEWARE: We pretend wildcards don't exist.
                dependencies[name] = determine_version_range(dependencies, name, version_range)
    sorted_dependencies = {k: v for k, v in sorted(dependencies.items())}
    return sorted_dependencies


def reduce_environment_requirements(project_dependencies, allow_conflicts=True):
    """
    :param project_dependencies: Dict like {'PyHC Package 1': {'package1': '>=1.0'}, 'PyHC Package 2': {...}}.
    :param allow_conflicts: Boolean that, when False, will raise an exception the moment a conflict is found.
    :return: Dict like {'package1': '>=1.0,<2.0', 'package2': 'None', ...} made by combining all package requirements (sorted alphabetically).
             Note: if dependency conflicts exist for a package and allow_conflicts=True, its allowed range will be None.
    """
    all_dependencies = {}
    for project, project_dependencies in project_dependencies.items():
        for package_name, v_range in project_dependencies.items():
            if package_name in all_dependencies:
                current_range = all_dependencies[package_name]
                if current_range is None:
                    pass  # at least one dependency conflict exists for this package so no valid range exists
                else:
                    if are_compatible(current_range, v_range):
                        all_dependencies[package_name] = reorder_requirements(combine_ranges(current_range, v_range))
                    else:
                        if allow_conflicts:
                            all_dependencies[package_name] = None  # found a dependency conflict for this package
                        else:
                            raise RuntimeError(f"Found conflict in '{project}': {package_name} {v_range}")
            else:
                all_dependencies[package_name] = v_range
    sorted_dependencies = {key: value for key, value in sorted(all_dependencies.items())}
    return sorted_dependencies


def are_compatible(allowed_range, package_range):
    """
    :param allowed_range: String like ">=1.5.0,<2.0,!=1.6"
    :param package_range: String ">=1.5.0,<1.9"
    :return: Boolean of whether package_range is compatible with allowed_range
    """
    try:
        r = combine_ranges(allowed_range, package_range)
        return True
    except RuntimeError:
        return False


def clean_dependencies(dependencies):
    """
    Given a dependencies dict, add a space before version ranges that start with '=',
    and reorder version ranges as: lower bound, upper bound, then exclusions/remaining.
    :param dependencies: Dict like {'package1': '<2,>=1.0', 'package2': '==23.0', ...}
    :return: Dict like {'package1': '>=1.0,<2', 'package2': ' ==23.0', ...}
    """
    if dependencies:
        cleaned_deps = {}
        for package, range_str in dependencies.items():
            range_str = clean_range_str(range_str)
            cleaned_deps[package] = range_str
        return cleaned_deps
    else:
        return dependencies


def clean_range_str(range_str):
    """
    Given a version range string, add a space before version ranges that start with '=',
    and reorder version ranges as: lower bound, upper bound, then exclusions/remaining.
    :param range_str: String like "<2.0,!=1.6,>=1.5.0"
    :return: Cleaned version range string like ">=1.5.0,<2.0,!=1.6"
    """
    if range_str:
        range_str = reorder_requirements(range_str)
        if range_str.startswith("="):
            range_str = " " + range_str
    return range_str


def reorder_requirements(range_str):
    """
    Reorder version ranges: lower bound, upper bound, then exclusions.
    :param range_str: String like "<2.0,!=1.6,>=1.5.0,"
    :return: Reordered String like ">=1.5.0,<2.0,!=1.6"
    """
    if range_str:
        rules = range_str.split(",")
        lower_bound = None
        upper_bound = None
        remaining = []
        for rule in rules:
            if rule.startswith(">"):
                lower_bound = rule
            elif rule.startswith("<"):
                upper_bound = rule
            else:
                remaining.append(rule)

        reordered_range_str = ""
        if lower_bound:
            reordered_range_str += lower_bound
        if upper_bound:
            reordered_range_str += upper_bound if not reordered_range_str else f',{upper_bound}'
        if remaining:
            reordered_range_str += ",".join(remaining) if not reordered_range_str else f',{",".join(remaining)}'
        return reordered_range_str
    else:
        return range_str


def compare_requirements(env_dependencies, package_dependencies):  # TODO: delete me?
    """
    TODO: Should probably delete this func...
    TODO: handle "found incompatibility" exceptions: Idea: try/catch, rather than let "Found incompatibility" string become current_range, store the incompatibility in a list of them such that all_deps[package] = tuple(deps, incompatible_rules)? Well... actually, I think that'd have to happen in `are_compatible()` because these ranges are just for individual projects so there won't be conflicts... `are_compatible()` is where we compare a project's range to the env's allowed range...
    :param env_dependencies: Dict like {'package1': '>=1.0', 'package2': '<23.0', ...}
    :param package_dependencies: Dict like {'PyHC Package 1': {'package1': '>=1.0'}, 'PyHC Package 2': {...}}
    :return compatibility: Dict like {'PyHC Package 1': {'package1': (True,'>=1.0'), 'package2': (False,'<23.0')}, ...}
             TODO: {'Env Dependencies': env_dependencies, 'Package Dependencies': compatibility}
    """
    compatibility = {}
    for package, package_deps in package_dependencies.items():
        package_deps = clean_dependencies(package_deps)
        compatibility[package] = {}
        for dep, allowed_range in env_dependencies.items():  # TODO: BUG: this misses any new dependencies in the non-core packages!! Need to loop through `package_deps` instead somehow...
            if dep in package_deps:
                package_range = package_deps[dep]
                package_is_compatible = are_compatible(allowed_range, package_range)
                compatibility[package][dep] = (package_is_compatible, package_range)
            else:
                compatibility[package][dep] = (None, None)
    return compatibility


def generate_first_two_cols_of_dependency_spreadsheet(env_dependencies):  # TODO: delete me...?
    """
    :param env_dependencies: Dict like {'package1': '>=1.0', 'package2': '<23.0', ...}
    :return: Excel workbook of the first two columns of the dependency conflict table
    """
    if not isinstance(env_dependencies, dict) or not env_dependencies:
        raise ValueError('Invalid dependencies input')

    # Prepare data for Excel
    env_dependencies = clean_dependencies(env_dependencies)

    # Create a new workbook
    workbook = openpyxl.Workbook()

    # Select the active worksheet
    worksheet = workbook.active

    # Write headers to the worksheet
    worksheet['A1'] = 'Package'
    worksheet['B1'] = 'Allowed Version Range'

    # Write data to the worksheet
    for package, version_range in env_dependencies.items():
        row = [package, version_range]
        worksheet.append(row)

    return workbook


def generate_dependency_spreadsheet(env_dependencies, package_dependencies):  # TODO: delete me...?
    """
    :param env_dependencies: Dict like {'package1': '>=1.0', 'package2': '<23.0', ...}
    :param package_dependencies: Dict like {'PyHC Package 1': {'package1': '>=1.0'}, 'PyHC Package 2': {...}}
    :return: Excel workbook of the dependency conflict table
    """
    if not isinstance(env_dependencies, dict) or not env_dependencies:
        raise ValueError('Invalid env_dependencies input')
    if not isinstance(package_dependencies, dict) or not package_dependencies:
        raise ValueError('Invalid package_dependencies input')

    # Create a new workbook populated with our environment's dependency requirements
    workbook = generate_first_two_cols_of_dependency_spreadsheet(env_dependencies)

    # Use a data structure of compatibilities to fill remaining columns for our package dependencies
    compatibility = compare_requirements(env_dependencies, package_dependencies)

    # Get the worksheet from our workbook
    worksheet = workbook[workbook.sheetnames[0]]

    # Add a column for each PyHC package to the worksheet
    for i, project in enumerate(compatibility.keys(), start=3):  # TODO: use "package" rather than "project"?
        worksheet.cell(row=1, column=i, value=project)

        # Check each row in the column for compatibility with the project's dependency requirements
        for j, (dep, (dep_compatibility, dep_range)) in enumerate(compatibility[project].items(), start=2):
            cell = worksheet.cell(row=j, column=i)
            if dep_compatibility is not None:
                cell.value = dep_range
                if dep_compatibility:
                    cell.fill = PatternFill(start_color="00ff00", end_color="00ff00", fill_type="solid")
                else:
                    cell.fill = PatternFill(start_color="ff0000", end_color="ff0000", fill_type="solid")

    return workbook


def merge_dependencies(core_dependencies, other_dependencies):
    """
    Merges two dependency dicts such that non-conflicting keys in other_dependencies are directly appended
    to core_dependencies (in order).
    :param core_dependencies: Dict of core dependencies like {'package1': '>=1.0', 'package2': '<23.0', ...}
    :param other_dependencies: Dict of other dependencies like {'package2': '>=24.0', 'package3': '<1.0', ...}
    :return: Combined dict like {'package1': '>=1.0', 'package2': '<23.0', 'package3': '<1.0', ...}
    """
    merged_dict = {**core_dependencies, **other_dependencies}
    for key, value in merged_dict.items():
        if key in core_dependencies:
            merged_dict[key] = core_dependencies[key]
    return merged_dict


# TODO: Need func table_data_to_2D_array(table_data) that flattens table_data
#       (biggest change: lots of {'package': (None, None)} cells where projects don't use that dependency).


def generate_dependency_table_data(packages, core_env_packages=[]):
    """
    Generates a data structure that can populate a dependency conflict table.
    :param packages: A list of PyHC packages ["package1", "package2", ...] that may have dependency conflicts
    :param core_env_packages: A list of PyHC packages ["package1", "package2", ...] that DON'T have dependency conflicts (assumed to already be installed in env)
    :return: A dict like {
                          'core_dependencies':
                              {'package1': (2, '>=1.0'), 'package2': (3, '<23.0'), ...},
                          'other_dependencies':
                              {'package3': (5, 'None'), 'package4': (6, '>=1.5,<2'), ...},
                          'project_data':
                              {
                               'PyHC Package 1':
                                  {'package1': (True,'>=1.0'), 'package2': (False,'<23.0')},
                               'PyHC Package 2': ...
                              }
                         }
             with version range data cleaned for Excel.
    """
    core_deps_by_project = get_dependency_ranges_by_package(core_env_packages, use_installed=True)
    other_deps_by_project = get_dependency_ranges_by_package(packages)
    all_deps_by_project = {**core_deps_by_project, **other_deps_by_project}

    # import pickle  # TODO: delete pickling
    # with open('core_deps_by_project3.pkl', 'wb') as f:
    #     pickle.dump(core_deps_by_project, f)
    # with open('other_deps_by_project3.pkl', 'wb') as f:
    #     pickle.dump(other_deps_by_project, f)
    # with open('all_deps_by_project3.pkl', 'wb') as f:
    #     pickle.dump(all_deps_by_project, f)

    # import pickle
    # with open('core_deps_by_project8.pkl', 'rb') as f:
    #     core_deps_by_project = pickle.load(f)
    # with open('other_deps_by_project8.pkl', 'rb') as f:
    #     other_deps_by_project = pickle.load(f)
    # # with open('all_deps_by_project8.pkl', 'rb') as f:
    # #     all_deps_by_project = pickle.load(f)
    # all_deps_by_project = {**core_deps_by_project, **other_deps_by_project}
    #
    # other_deps_by_project['enlilviz']['numpy'] = "<1.0.0"
    # other_deps_by_project['geospacelab']['pandas'] = "<1.0.0"

    core_dependencies = reduce_environment_requirements(core_deps_by_project, allow_conflicts=False)
    other_dependencies = reduce_environment_requirements(other_deps_by_project)
    other_dependencies = {k: v for k, v in other_dependencies.items() if k not in core_dependencies}  # make unique
    all_dependencies = merge_dependencies(core_dependencies, other_dependencies)

    table_data = {'core_dependencies': core_dependencies, 'other_dependencies': other_dependencies, 'project_data': {}}
    for project, project_dependencies in all_deps_by_project.items():
        table_data['project_data'][project] = {}
        for package_name, version_range in project_dependencies.items():
            allowed_range = all_dependencies[package_name]
            if allowed_range is not None:
                compatible = are_compatible(allowed_range, version_range)
                table_data['project_data'][project][package_name] = (compatible, clean_range_str(version_range))
            else:
                table_data['project_data'][project][package_name] = (False, clean_range_str(version_range))

    # Clean data and add row numbers
    core_dependencies = clean_dependencies(table_data['core_dependencies'])
    core_dependencies = {k: (i, v) for i, (k, v) in enumerate(core_dependencies.items(), start=2)}
    table_data['core_dependencies'] = core_dependencies

    start = len(table_data['core_dependencies']) + 3 if core_dependencies else 2
    other_dependencies = clean_dependencies(table_data['other_dependencies'])
    other_dependencies = {k: (i, v) for i, (k, v) in enumerate(other_dependencies.items(), start=start)}
    table_data['other_dependencies'] = other_dependencies

    return table_data


def pad_table_project_data(table_data):
    """
    TODO: consider using collections.OrderedDict if order becomes a problem.
    TODO: put a bunk "N/A" -> (None, None) <unlikely-separator-val> entry in project_data between core and other deps, if there are core deps
    :param table_data: The data structure returned from `generate_dependency_table_data()`
    :return: table_data but with its project_data padded with None data for dependencies that projects don't use.
    """
    core_dependencies = table_data['core_dependencies']
    other_dependencies = table_data['other_dependencies']
    project_data = table_data['project_data']
    temp_data = project_data

    for project, dependency_data in project_data.items():
        if core_dependencies:
            # pad cells for core_dependencies,
            # add {"N/A": (None, None)} as separator
            for package_name in core_dependencies.keys():
                if package_name not in dependency_data:
                    temp_data[project][package_name] = (None, None)
            sorted_data = {k: v for k, v in sorted(temp_data[project].items())}
            temp_data[project] = sorted_data
            temp_data[project]["N/A"] = (None, None)  # separator between core and other dependencies

        # pad for other_dependencies
        other_temp_data = {}
        for package_name in other_dependencies.keys():
            if package_name not in dependency_data:
                #temp_data[project][package_name] = (None, None)
                other_temp_data[package_name] = (None, None)
            else:
                other_temp_data[package_name] = dependency_data[package_name]

        temp_data[project] = merge_dependencies(temp_data[project], other_temp_data)

    table_data['project_data'] = temp_data
    return table_data


# def excel_spreadsheet_from_table_data(table_data):
#     """
#     :param table_data: The data structure returned from `generate_dependency_table_data()`
#     :return: The Excel workbook that is the dependency conflict table
#     """
#     if not isinstance(table_data, dict) or not table_data:
#         raise ValueError('Invalid table data.')
#     # TODO: assert: len of project data should be the length of core + other dependencies +1 (when there are core ones)
#
#     # Pad data for Excel extraction
#     # table_data = pad_table_project_data(table_data)  # TODO: consider renaming funcs because of this (work it into `generate_dependency_table_data()`?
#
#     # Extract data for Excel
#     core_dependencies = table_data['core_dependencies']
#     other_dependencies = table_data['other_dependencies']
#     project_data = table_data['project_data']
#
#     # Create a new workbook
#     workbook = openpyxl.Workbook()
#
#     # Select the active worksheet
#     worksheet = workbook.active
#
#     # Write headers to the worksheet
#     worksheet['A1'] = 'Package'
#     worksheet['B1'] = 'Allowed Version Range'
#
#     # Write data to the worksheet
#     if core_dependencies:
#         # Write core environment dependencies to the first two columns of the worksheet (shaded light gray)
#         for i, (package_name, version_range) in enumerate(core_dependencies.items(), start=2):
#             # Column 1 - Package
#             cell = worksheet.cell(row=i, column=1)
#             cell.value = package_name
#             cell.fill = PatternFill(start_color="aaaaaa", end_color="aaaaaa", fill_type="solid")
#
#             # Column 2 - Allowed Version Range
#             cell = worksheet.cell(row=i, column=2)
#             cell.value = version_range  # TODO: shouldn't ever be "N/A" but should I consider that case here anyway?
#             cell.fill = PatternFill(start_color="aaaaaa", end_color="aaaaaa", fill_type="solid")
#
#         # Add a dark gray separator before other dependencies
#         cell = worksheet.cell(row=i+1, column=1)
#         cell.fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")
#         cell = worksheet.cell(row=i+1, column=2)
#         cell.fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")
#
#     # Write other environment dependencies to the first two columns of the worksheet
#     for package_name, version_range in other_dependencies.items():
#         row = [package_name, version_range if version_range is not None else "N/A"]
#         worksheet.append(row)
#
#     # Write project data to the worksheet one column at a time
#     for j, (project, dependency_data) in enumerate(project_data.items(), start=3):
#         worksheet.cell(row=1, column=j, value=project)  # column header
#         for i, (package_name, (compatible, version_range)) in enumerate(dependency_data.items(), start=2):
#             cell = worksheet.cell(row=i, column=j)
#             if compatible is not None:
#                 cell.value = version_range
#                 if compatible:
#                     cell.fill = PatternFill(start_color="00ff00", end_color="00ff00", fill_type="solid")
#                 else:
#                     cell.fill = PatternFill(start_color="ff0000", end_color="ff0000", fill_type="solid")
#
#     return workbook


def excel_spreadsheet_from_table_data(table_data):
    """
    :param table_data: The data structure returned from `generate_dependency_table_data()`
    :return: The Excel workbook that is the dependency conflict table
    """
    if not isinstance(table_data, dict) or not table_data:
        raise ValueError('Invalid table data.')
    if not isinstance(table_data['core_dependencies'], dict):
        raise ValueError('Invalid core_dependencies in table data.')
    if not isinstance(table_data['other_dependencies'], dict):
        raise ValueError('Invalid other_dependencies in table data.')
    if not isinstance(table_data['project_data'], dict):
        raise ValueError('Invalid project_data in table data.')

    # Extract data for Excel
    core_dependencies = table_data['core_dependencies']
    other_dependencies = table_data['other_dependencies']
    all_dependencies = {**other_dependencies, **core_dependencies}  # shouldn't be overlap, but core values would win
    project_data = table_data['project_data']

    # Create a new workbook
    workbook = openpyxl.Workbook()

    # Select the active worksheet
    worksheet = workbook.active

    # Write headers to the worksheet
    worksheet['A1'] = 'Package'
    worksheet['B1'] = 'Allowed Version Range'

    # Write data to the worksheet
    if core_dependencies:
        # Write core environment dependencies to the first two columns of the worksheet (shaded light gray)
        for package_name, (row, version_range) in core_dependencies.items():
            # Column 1 - Package
            cell = worksheet.cell(row=row, column=1)
            cell.value = package_name
            cell.fill = PatternFill(start_color="aaaaaa", end_color="aaaaaa", fill_type="solid")

            # Column 2 - Allowed Version Range
            cell = worksheet.cell(row=row, column=2)
            cell.value = version_range  # TODO: shouldn't ever be "N/A" but should I consider that case here anyway?
            cell.fill = PatternFill(start_color="aaaaaa", end_color="aaaaaa", fill_type="solid")

        # Add a dark gray separator before other dependencies
        cell = worksheet.cell(row=row+1, column=1)
        cell.fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")
        cell = worksheet.cell(row=row+1, column=2)
        cell.fill = PatternFill(start_color="333333", end_color="333333", fill_type="solid")

    # Write other environment dependencies to the first two columns of the worksheet
    # TODO: consider doing this the cell-oriented way like we do for core_dependencies?
    for package_name, (_, version_range) in other_dependencies.items():
        row_data = [package_name, version_range if version_range is not None else "N/A"]
        worksheet.append(row_data)

    # Write project data to the worksheet one column at a time
    for j, (project, dependency_data) in enumerate(project_data.items(), start=3):
        worksheet.cell(row=1, column=j, value=project)  # column header
        for package_name, (compatible, version_range) in dependency_data.items():
            row_num = all_dependencies[package_name][0]
            cell = worksheet.cell(row=row_num, column=j)
            if compatible is not None:
                cell.value = version_range
                if compatible:
                    cell.fill = PatternFill(start_color="00ff00", end_color="00ff00", fill_type="solid")
                else:
                    cell.fill = PatternFill(start_color="ff0000", end_color="ff0000", fill_type="solid")

    return workbook


if __name__ == '__main__':
    # generate_requirements_file()
    core_packages = get_core_pyhc_packages()
    other_packages = get_other_pyhc_packages()
    supplementary_packages = get_supplementary_packages()
    # table_data = generate_dependency_table_data(other_packages, core_packages)  # segments spreadsheet (core/non-core)
    all_packages = core_packages + other_packages + supplementary_packages
    # all_packages = core_packages + supplementary_packages
    table_data = generate_dependency_table_data(all_packages)

    # Write table_data
    import pickle
    with open('PyHC-dependency-table-jan-4-2024(6).pkl', 'wb') as f:
        pickle.dump(table_data, f)

    # Read table_data
    # import pickle
    # with open('pyhc-dependency-table-jan-3-2024.pkl', 'rb') as f:
    #     table_data = pickle.load(f)

    # ----debug----
    # table_data['project_data']['enlilviz']['numpy'] = (False, 'fake,<1.0.0')
    # -------------

    table = excel_spreadsheet_from_table_data(table_data)
    table.save('PyHC-dependency-table-jan-4-2024(6).xlsx')
    print("done")


