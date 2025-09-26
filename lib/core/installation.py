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
    
    def __init__(self, requirement=None):
        if requirement is None:
            self.requirement = None
            self.args = ()
        elif isinstance(requirement, str):
            # Handle string input (package name or error message)
            self.requirement = requirement
            self.args = (requirement,)
            super().__init__(requirement)
        else:
            # Handle Requirement object
            self.requirement = requirement
            self.args = (requirement,)
            super().__init__(f"The '{requirement.name}' distribution was not found")
    
    def __str__(self):
        if isinstance(self.requirement, str):
            return self.requirement
        elif self.requirement is not None:
            return f"The '{self.requirement.name}' distribution was not found"
        else:
            return "Distribution not found"


class VersionConflict(Exception):
    """Exception raised when there's a version conflict."""
    
    def __init__(self, dist=None, requirement=None):
        self.dist = dist
        self.requirement = requirement
        
        if isinstance(dist, str) and requirement is None:
            # Handle simple string message
            message = dist
        else:
            # Extract project name and version information
            if dist is not None:
                if hasattr(dist, 'project_name'):
                    project_name = getattr(dist, 'project_name')
                    installed_version = getattr(dist, 'version', 'unknown')
                elif isinstance(dist, str):
                    # Parse string format "package_name version" or just use as project name
                    parts = dist.split()
                    if len(parts) >= 2:
                        project_name = parts[0]
                        installed_version = parts[1]
                    else:
                        project_name = dist
                        installed_version = "unknown"
                else:
                    project_name = str(dist)
                    installed_version = "unknown"
            else:
                project_name = "unknown"
                installed_version = "unknown"
            
            # Format the requirement information
            if requirement is not None:
                if hasattr(requirement, 'name'):
                    req_name = requirement.name
                    req_spec = str(requirement.specifier) if hasattr(requirement, 'specifier') else ''
                elif hasattr(requirement, 'project_name'):
                    req_name = getattr(requirement, 'project_name')
                    req_spec = str(requirement.specifier) if hasattr(requirement, 'specifier') else str(requirement)
                else:
                    req_name = str(requirement)
                    req_spec = ''
                
                message = f"{project_name} {installed_version} is installed but {req_name}{req_spec} is required"
            else:
                message = f"Version conflict: {project_name} {installed_version}"
        
        self.args = (message,)
        super().__init__(message)
    
    def __str__(self):
        return self.args[0] if self.args else "Version conflict"
    
    @property
    def report(self):
        """Generate a detailed report of the version conflict."""
        return str(self)


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
        dependency = dependency.strip()
        if not dependency or dependency.startswith('#'):
            # Skip empty lines and comments
            continue
            
        try:
            requirement = Requirement(dependency)
            # Check if the package is installed
            try:
                installed_version = version(requirement.name)
                # Check if the installed version satisfies the requirement
                if requirement.specifier and not requirement.specifier.contains(installed_version):
                    # Create a mock distribution object for better error reporting
                    class MockDist:
                        def __init__(self, name, version):
                            self.project_name = name
                            self.version = version
                    
                    mock_dist = MockDist(requirement.name, installed_version)
                    raise VersionConflict(mock_dist, requirement)
            except PackageNotFoundError:
                raise DistributionNotFound(requirement)
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
