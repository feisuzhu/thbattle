# -*- coding: utf-8 -*-

# -- stdlib --
from typing import Tuple
import os
import shutil
import sys

# -- third party --
# -- own --
from .dep import download_dep
from .misc import banner, get_cache_home, info
from .tinysh import Command, environ, sh


# -- code --
def setup_miniforge(prefix):
    url = "https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh"
    download_dep(url, prefix, args=["-bfp", str(prefix)])


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

    prefix = get_cache_home() / "miniforge3"
    setup_miniforge(prefix)

    conda_path = prefix / "bin" / "conda"

    if not conda_path.exists():
        shutil.rmtree(prefix, ignore_errors=True)
        setup_miniforge(prefix)
        if not conda_path.exists():
            raise RuntimeError(f"Failed to setup miniforge at {prefix}")

    conda = sh.bake(str(conda_path))

    env = prefix / "envs" / version
    exe = env / "bin" / "python"

    if not exe.exists():
        with environ({'PATH': f'{prefix}/bin:{prefix}/condabin:{os.environ["PATH"]}'}):
            conda.create("-y", "-n", version, f"python={version}")

    python = sh.bake(str(exe))
    pip = python.bake("-m", "pip")

    return python, pip
