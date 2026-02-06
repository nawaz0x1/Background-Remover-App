"""
python-for-android recipe for numpy.

Patches numpy 2.x's unique.cpp which is missing ``#include <unordered_map>``
— this compiles fine on desktop (glibc implicitly includes it) but fails
with NDK r25b's strict libc++.
"""

import os
from pythonforandroid.recipes.numpy import NumpyRecipe


class NumpyFixedRecipe(NumpyRecipe):
    """Override that patches the missing include before building."""

    def build_arch(self, arch):
        # Locate unique.cpp in the unpacked source tree
        src_dir = self.get_build_dir(arch.arch)
        unique_cpp = os.path.join(
            src_dir, "numpy", "_core", "src", "multiarray", "unique.cpp"
        )
        if os.path.isfile(unique_cpp):
            with open(unique_cpp, "r") as fh:
                content = fh.read()
            if "#include <unordered_map>" not in content:
                print(f"  *** Patching {unique_cpp}: adding #include <unordered_map>")
                content = "#include <unordered_map>\n" + content
                with open(unique_cpp, "w") as fh:
                    fh.write(content)
        else:
            print(f"  *** unique.cpp not found at {unique_cpp} (numpy <2.1?) — skipping patch")

        super().build_arch(arch)


recipe = NumpyFixedRecipe()
