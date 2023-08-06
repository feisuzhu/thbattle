# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Tuple
import os
import platform
import re
import shutil
import sys

# -- third party --
# -- own --
from . import misc
from .dep import download_dep
from .misc import banner, get_cache_home, info
from .tinysh import Command, environ, sh


# -- code --
def setup_mambaforge(prefix):
    u = platform.uname()
    url = "https://github.com/conda-forge/miniforge/releases/download/23.1.0-1/Mambaforge-23.1.0-1-Linux-x86_64.sh"
    download_dep(url, prefix, args=["-bfp", str(prefix)])


def get_desired_python_version() -> str:
    version = misc.options.python
    version = version or os.environ.get("PY", None)
    v = sys.version_info
    this_version = f"{v.major}.{v.minor}"

    if version in ("3.x", "3", None):
        assert v.major == 3
        return this_version
    elif version and re.match(r"^3\.\d+$", version):
        return version
    elif version in ("native", "Native"):
        return "(Native)"
    else:
        raise RuntimeError(f"Unsupported Python version: {version}")


@banner("Setup Python {version}")
def setup_python(version: str) -> Tuple[Command, Command]:
    """
    Find the required Python environment and return the `python` and `pip` commands.
    """
    if version == "(Native)":
        info("Using your current Python interpreter as requested.")
        python = sh.bake(sys.executable)
        pip = python.bake("-m", "pip")
        return python, pip

    prefix = get_cache_home() / "mambaforge"
    setup_mambaforge(prefix)

    conda_path = prefix / "bin" / "conda"

    if not conda_path.exists():
        shutil.rmtree(prefix, ignore_errors=True)
        setup_mambaforge(prefix)
        if not conda_path.exists():
            raise RuntimeError(f"Failed to setup mambaforge at {prefix}")

    conda = sh.bake(str(conda_path))

    env = prefix / "envs" / version
    exe = env / "bin" / "python"

    if not exe.exists():
        with environ({'PATH': f'{prefix}/bin:{prefix}/condabin:{os.environ["PATH"]}'}):
            conda.create("-y", "-n", version, f"python={version}")

    python = sh.bake(str(exe))
    pip = python.bake("-m", "pip")

    return python, pip
