# doctor-apt #
shows system-wide packages information

The tool consists of some useful APT/dpkg commands,
along with more complex Python scripts.

## Diagnosis mode ##
Diagnosis finds unmet dependencies and unneeded packages.
Needed packages are those, which were installed manually or
as a dependency to such (by default only *Depends*, *PreDepends* and *Recommends*).
This approach allows system to easily return to previous state after
[uninstalling certain packages](http://unix.stackexchange.com/questions/140468/package-installed-as-dependency-is-not-removed-with-apt-get-autoremove).

## Known flaws ##
There is currently no versions checking - if a package is installed,
it is considered to match.
Affects **<**, **<=** and **=** dependencies.
