"""
python-for-android recipe for numpy, pinned to 1.26.4.

Numpy 2.x fails to cross-compile with NDK r25b (missing <unordered_map>
include in unique.cpp).  This recipe overrides p4a's default numpy to
force v1.26.4 which compiles cleanly.
"""

from pythonforandroid.recipes.numpy import NumPyRecipe


class NumPyFixed(NumPyRecipe):
    version = "1.26.4"
    url = "https://github.com/numpy/numpy/archive/v{version}.tar.gz"


recipe = NumPyFixed()
