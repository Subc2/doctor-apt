#!/usr/bin/python
# -*- coding: utf-8 -*-

"""doctor-apt - shows system-wide packages information"""

from __future__ import print_function

__author__ = "Paweł Zacharek"
__copyright__ = "Copyright (C) 2016-2017 Paweł Zacharek"
__date__ = "2017-03-30"
__license__ = "GPLv2+"
__version__ = "0.3.6"

DEFAULT_DEPENDENCY_TYPES = ("Depends", "PreDepends", "Recommends")

import argparse

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("-c", "--config", action="store_true", help="list residual packages (removed, config remains)")
parser.add_argument("-d", "--diagnosis", action="store_true", help="find unmet dependencies and unneeded packages (default)")
parser.add_argument("-i", "--installed", action="store_true", help="list installed packages")
parser.add_argument("-l", "--large", action="store_true", help="list large (>10MiB) packages installed manually")
parser.add_argument("-u", "--uncommon", action="store_true", help="show packages with uncommon state")
args = parser.parse_args()

if args.config:
	from subprocess import call
	call("dpkg -l | awk 'NR > 6 && /^rc/ {print $2}'", shell=True)
	parser.exit()

if args.installed:
	from subprocess import call
	call("dpkg -l | awk 'NR > 6 && /^.i/ {print $2}'", shell=True)
	parser.exit()

if args.uncommon:
	from subprocess import call
	call("dpkg -l | awk 'NR > 6 && !/^ii/'", shell=True)
	parser.exit()

import apt_pkg
apt_pkg.init()

cache = apt_pkg.Cache(None)
depcache = apt_pkg.DepCache(cache)
is_installed = lambda package: package.current_ver != None

if args.large:
	large = set()
	for pkg in cache.packages:
		if is_installed(pkg) and not depcache.is_auto_installed(pkg) and pkg.current_ver.installed_size > 10 * 1024 * 1024:
			large.add(pkg.name)
	print("\n".join(sorted(large)))
	parser.exit()

# diagnosis
installed = set()
needed = set()
unmet_dependencies = []

dependencies_short = {
	"Depends":    "dep",
	"PreDepends": "pre",
	"Recommends": "rec",
	"Suggests":   "sug",

	"Breaks":     "bre",
	"Conflicts":  "con",
	"Enhances":   "enh",
	"Replaces":   "rep"
}

def package_providing_functionality(package):
	if is_installed(package):
		return package
	if package.has_provides:
		# search for already installed packages providing the same functionality
		for _, _, version in package.provides_list:
			pkg = version.parent_pkg
			if is_installed(pkg):
				return pkg
		if not package.has_versions:
			# package is virtual and there is no installed package providing it,
			# so we choose the first provider on the list
			return package.provides_list[0][2].parent_pkg
	return package

def add_recursive_dependencies(package):
	if package.id in needed:
		return
	needed.add(package.id)
	ver = package.current_ver
	for dependency_type in DEFAULT_DEPENDENCY_TYPES:
		for or_group in ver.depends_list.get(dependency_type, []):
			found = False
			targets = [dependency.target_pkg for dependency in or_group]

			# at least one package has to be installed to meet the dependencies
			for pkg in targets:
				pkg2 = package_providing_functionality(pkg)
				if is_installed(pkg2):
					add_recursive_dependencies(pkg2)
					found = True
					break
			if not found:
				unmet_dependencies.append((
					package.name,
					dependencies_short[dependency_type],
					" | ".join([pkg.name for pkg in targets])
				))

for pkg in cache.packages:

	# find installed packages
	if is_installed(pkg):
		installed.add(pkg.id)

		# find needed packages
		if not depcache.is_auto_installed(pkg):
			add_recursive_dependencies(pkg)

unneeded = installed.difference(needed)

if unmet_dependencies:
	align_pkg = max(max(len(pkg) for pkg, _, _ in unmet_dependencies), 32)
	align_dep = max(max(len(dep) for _, _, dep in unmet_dependencies), 8)
	print("Packages with unmet dependencies%s  Type  Requires\n%s=-=====-%s" % (
		(align_pkg-32) * " ", align_pkg * "=", align_dep * "="
	))
	previous_pkg  = ""
	for pkg, type, dep in sorted(unmet_dependencies, key = lambda pkg_type_dep: pkg_type_dep[0]):
		print("%-*s  %s   %s" % (align_pkg, pkg if pkg != previous_pkg else "", type, dep))
		previous_pkg = pkg

if unneeded:
	packages_info = sorted(
		[(pkg.name, pkg.current_ver.size) for pkg in cache.packages if pkg.id in unneeded],
		key = lambda name_size: name_size[0]
	)
	align_name = max(max(len(name) for name, _, in packages_info), 17)
	print("\nUnneeded packages%s        Size\n%s=-==========" % (
		(align_name-17) * " ", align_name * "="
	))
	for name, size in packages_info:
		print("%-*s  %10d" % (align_name, name, size))
