# -*- coding: utf-8 -*-

# -- stdlib --
from dataclasses import dataclass
from pathlib import Path
import os

# -- third party --
# -- own --
from .misc import banner, path_prepend


# -- code --
@dataclass
class AndroidNDKEnviron:
    cmake_defines: list[str]
    autoconf_cross_args: list[str]
    host: str
    target: str


NATIVE_LINUX = AndroidNDKEnviron(
    cmake_defines=[],
    autoconf_cross_args=[],
    host="x86_64-pc-linux-gnu",
    target="x86_64-pc-linux-gnu",
)


@banner("Setup Android NDK")
def setup_android_ndk(arch: str = 'linux-x86_64', api_level: int = 21) -> AndroidNDKEnviron:
    arch_abi_map = {
        'x86_64': 'x86_64',
        'aarch64': 'arm64-v8a',
    }

    arch_triplet_map = {
        'x86_64': 'x86_64-linux-android',
        'aarch64': 'aarch64-linux-android',
    }

    abi = arch_abi_map[arch]
    triplet = arch_triplet_map[arch]

    ndkroot = Path(os.environ["ANDROID_NDK_HOME"])
    toolchain = ndkroot / "build/cmake/android.toolchain.cmake"
    if not toolchain.exists():
        raise RuntimeError(f"ANDROID_NDK_HOME is set to {ndkroot}, but the path does not exist.")

    p = ndkroot.resolve()
    defines = [
        f"-DCMAKE_TOOLCHAIN_FILE={toolchain}",
        f"-DANDROID_NATIVE_API_LEVEL={api_level}",
        f"-DANDROID_ABI={abi}",
    ]

    os.environ['TARGET'] = triplet
    bin = p / "toolchains/llvm/prebuilt/linux-x86_64/bin"

    os.environ['CC']      = str(bin / f"{triplet}{api_level}-clang")
    os.environ['CXX']     = str(bin / f"{triplet}{api_level}-clang++")
    os.environ['AR']      = str(bin / "llvm-ar")
    os.environ['RANLIB']  = str(bin / "llvm-ranlib")
    os.environ['STRIP']   = str(bin / "llvm-strip")
    os.environ['READELF'] = str(bin / "llvm-readelf")
    os.environ['LD']      = str(bin / "ld")
    os.environ['AS']      = str(bin / "llvm-as")

    path_prepend("PATH", p / "toolchains/llvm/prebuilt/linux-x86_64/bin")

    return AndroidNDKEnviron(
        cmake_defines=defines,
        autoconf_cross_args=[f"--host={triplet}", "--build=x86_64-linux-gnu"],
        host=triplet,
        target=triplet,
    )
