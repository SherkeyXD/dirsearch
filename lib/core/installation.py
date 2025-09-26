#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#  Author: Mauro Soria

from __future__ import annotations

import subprocess
import sys
from importlib.metadata import version, PackageNotFoundError
from packaging.requirements import Requirement

from lib.core.exceptions import FailedDependenciesInstallation
from lib.core.settings import SCRIPT_PATH
from lib.utils.file import FileUtils

REQUIREMENTS_FILE = f"{SCRIPT_PATH}/requirements.txt"


class DistributionNotFound(Exception):
    """Exception raised when a distribution is not found."""
    pass


class VersionConflict(Exception):
    """Exception raised when there's a version conflict."""
    pass


def get_dependencies() -> list[str]:
    try:
        return FileUtils.get_lines(REQUIREMENTS_FILE)
    except FileNotFoundError:
        print("Can't find requirements.txt")
        exit(1)


# Check if all dependencies are satisfied
def check_dependencies() -> None:
    dependencies = get_dependencies()
    for dependency in dependencies:
        try:
            requirement = Requirement(dependency.strip())
            # Check if the package is installed
            try:
                installed_version = version(requirement.name)
                # Check if the installed version satisfies the requirement
                if not requirement.specifier.contains(installed_version):
                    raise VersionConflict(f"{requirement.name} version {installed_version} does not satisfy {requirement}")
            except PackageNotFoundError:
                raise DistributionNotFound(f"Package {requirement.name} is not installed")
        except Exception as e:
            # Handle any other parsing errors
            if not isinstance(e, (DistributionNotFound, VersionConflict)):
                raise DistributionNotFound(str(e))


def install_dependencies() -> None:
    try:
        subprocess.check_output(
            [sys.executable, "-m", "pip", "install", "-r", REQUIREMENTS_FILE],
            stderr=subprocess.STDOUT,
        )
    except subprocess.CalledProcessError:
        raise FailedDependenciesInstallation
