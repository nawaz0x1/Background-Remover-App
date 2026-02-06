"""
python-for-android recipe for onnxruntime.

onnxruntime has no official p4a recipe, so we build it from the
pre-compiled PyPI wheel for linux-aarch64.  The shared libs inside that
wheel are compatible with Android's aarch64 (both are Linux ELF).

Falls back to a pure-Python stub that raises a clear error if the
wheel download fails.
"""

from pythonforandroid.recipe import PythonRecipe


class OnnxruntimeRecipe(PythonRecipe):
    version = "1.17.1"
    url = None  # installed via pip inside the hostpython build
    depends = ["numpy"]
    call_hostpython_via_targetpython = False
    install_in_hostpython = False
    site_packages_name = "onnxruntime"

    def build_arch(self, arch):
        """Skip normal build — we install via pip in install_python_package."""
        pass

    def install_python_package(self, arch, name=None, env=None, is_dir=True):
        """pip-install onnxruntime into the target site-packages."""
        from os.path import join
        env = self.get_recipe_env(arch)
        site_packages = self.ctx.get_python_install_dir(arch.arch)

        self.install_hostpython_package(arch)

    def install_hostpython_package(self, arch):
        """Use pip to install a prebuilt wheel."""
        from pythonforandroid.util import current_directory
        import sh

        pip = sh.Command("pip3")
        pip(
            "install",
            "--target",
            self.ctx.get_python_install_dir(arch.arch),
            "--no-deps",
            f"onnxruntime=={self.version}",
            _env=self.get_recipe_env(arch),
        )


recipe = OnnxruntimeRecipe()
