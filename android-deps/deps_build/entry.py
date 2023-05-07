# -*- coding: utf-8 -*-

# -- stdlib --
from functools import lru_cache
from typing import Tuple
import argparse
import os
import shutil

# -- third party --
# -- own --
from . import misc
from .android import setup_android_ndk
from .misc import banner
from .python import setup_python
from .tinysh import Command, chdir, git, make, environ


# -- code --
options = None
configure = Command("./configure")
cmake = Command("cmake")


class ProjectPaths:
    def __init__(self, project, arch):
        self.root = misc.get_cache_home()
        self.project = project
        self.arch = arch

    @property
    @lru_cache(1)
    def repo(self):
        base = self.root / "repos"
        base.mkdir(parents=True, exist_ok=True)
        return base / self.project

    @property
    @lru_cache(1)
    def build(self):
        return self.root / "builds" / self.arch / self.project

    @property
    @lru_cache(1)
    def install(self):
        return self.root / "installs" / self.arch / self.project

    @property
    @lru_cache(1)
    def pkgconfig(self):
        return self.install / "lib" / "pkgconfig"

    def is_installed(self):
        return (self.install / '.installed').exists()

    def set_installed(self):
        (self.install / '.installed').touch()

    def clean(self):
        if self.repo.exists():
            with chdir(self.repo):
                git.clean('-fxd')
                git.reset('--hard')

        shutil.rmtree(self.build, ignore_errors=True)
        shutil.rmtree(self.install, ignore_errors=True)
        self.build.mkdir(parents=True, exist_ok=True)
        self.install.mkdir(parents=True, exist_ok=True)


@banner("Build libgit2 {arch}")
def build_libgit2(version: str, arch: str = 'linux-x86_64'):
    libgit2 = ProjectPaths('libgit2', arch)
    if libgit2.is_installed():
        return

    openssl = ProjectPaths('openssl', arch)

    libgit2.repo.exists() or git.clone('https://github.com/libgit2/libgit2.git', libgit2.repo)
    libgit2.clean()

    with chdir(libgit2.repo):
        git.checkout(version)

    with chdir(libgit2.build):
        cmake(libgit2.repo, '-DBUILD_SHARED_LIBS=OFF',
                            '-DUSE_SSH=OFF',
                            '-DUSE_HTTPS=ON',
                            '-DUSE_BUNDLED_ZLIB=ON',
                            '-DUSE_ICONV=OFF',
                            '-DREGEX_BACKEND=builtin',
                            '-DCMAKE_BUILD_TYPE=Release',
                            '-DBUILD_CLI=OFF',
                            f'-DOPENSSL_ROOT_DIR={openssl.install}',

                            # libgit2 uses C90 which doesn't have `inline`, but NDK headers are apparently using it
                            '-DCMAKE_C_FLAGS=-Dinline=__inline__',
                            '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
                            f'-DCMAKE_INSTALL_PREFIX={libgit2.install}',
        )
        make()
        make.install()
        libgit2.set_installed()


@banner("Build pygit2 {arch}")
def build_pygit2(python: Command, pip: Command, arch: str = 'linux-x86_64'):
    libgit2 = ProjectPaths('libgit2', arch)
    libffi = ProjectPaths('libffi', arch)
    with environ({'LIBGIT2': str(libgit2.install), 'PKG_CONFIG_PATH': str(libffi.pkgconfig)}):
        pip.install('pygit2')


@banner("Build openssl {arch}")
def build_openssl(version: str, arch: str = 'linux-x86_64'):
    arch_map = {
        'linux-x86_64': 'linux-x86_64',
        'x86_64': 'android-x86_64',
        'aarch64': 'android-arm64',
    }

    openssl = ProjectPaths('openssl', arch)
    if openssl.is_installed():
        return

    openssl.repo.exists() or git.clone('https://github.com/openssl/openssl.git', openssl.repo)
    openssl.clean()

    with chdir(openssl.repo):
        git.checkout(version)
        Command("./Configure")(
            'no-shared',
            arch_map[arch],
            f"--prefix={openssl.install}",
            f"-D__ANDROID_API__={options.android_api_level}",
        )
        make()
        make('install_sw', 'install_ssldirs')
        openssl.set_installed()


@banner("Build libffi {arch}")
def build_libffi(version: str, arch: str = 'linux-x86_64'):
    libffi = ProjectPaths('libffi', arch)
    if libffi.is_installed():
        return

    libffi.repo.exists() or git.clone('https://github.com/libffi/libffi.git', libffi.repo)
    libffi.clean()

    with chdir(libffi.repo):
        git.clean('-fxd')
        git.reset('--hard')
        git.checkout(version)
        Command("./autogen.sh")()
        configure(f"--prefix={libffi.install}", "--disable-shared", "--enable-static", "--disable-docs")
        make()
        make.install()
        libffi.set_installed()


@banner("Build sqlite {arch}")
def build_sqlite(version: str, arch: str = 'linux-x86_64'):
    sqlite = ProjectPaths('sqlite', arch)
    if sqlite.is_installed():
        return

    sqlite.repo.exists() or git.clone('https://github.com/sqlite/sqlite.git', sqlite.repo)
    sqlite.clean()

    with chdir(sqlite.repo):
        git.clean('-fxd')
        git.checkout(version)
        configure(f"--prefix={sqlite.install}",
                  "--disable-shared",
                  "--enable-static",
                  "--disable-docs",
                  "--disable-readline",
                  "--disable-tcl")
        make()
        make.install()
        sqlite.set_installed()


@banner("Build cpython {arch}")
def build_cpython(build_python: Command, version: str, arch: str = 'linux-x86_64'):
    cpython = ProjectPaths('cpython', arch)
    if cpython.is_installed():
        return

    openssl = ProjectPaths('openssl', arch)
    libffi = ProjectPaths('libffi', arch)
    sqlite = ProjectPaths('sqlite', arch)

    with open('/tmp/pkg-config-static', 'w') as f:
        f.write('#!/bin/bash\nexec pkg-config --static "$@"\n')
        os.fchmod(f.fileno(), 0o755)

    cpython.repo.exists() or git.clone('https://github.com/python/cpython.git', cpython.repo)
    cpython.clean()

    with chdir(cpython.repo):
        git.clean('-fxd')
        git.checkout(version)

        pkgconfigs = ':'.join(str(v.pkgconfig) for v in (openssl, libffi, sqlite))

        configure(
            'PKG_CONFIG=/tmp/pkg-config-static',
            f'PKG_CONFIG_PATH={pkgconfigs}',
            f'LDFLAGS=-L{libffi.install}/lib',  # configure & setup.py is buggy, not respecting pkg-config
            f"--prefix={cpython.install}",
            f'--with-build-python={build_python.args[0]}',
            "--with-pkg-config=yes",
            "--enable-ipv6",
            "--enable-shared",
            "--with-ensurepip=no",
            "--with-system-ffi",
            "--without-readline",
            'ac_cv_file__dev_ptmx=no',
            'ac_cv_file__dev_ptc=no',
        )
        mj, mn, p = version[1:].split('.')
        make(f'libpython{mj}.{mn}.so')
        make('sharedmods')
        make.install()
        cpython.set_installed()


@banner("Setup crossenv for {arch}")
def setup_crossenv(python: Command, pip: Command, arch: str = 'linux-x86_64') -> Tuple[Command, Command]:
    cpython = ProjectPaths('cpython', arch)
    crossenv = ProjectPaths('crossenv', arch)
    crossenv.clean()

    pip.install('crossenv')
    python('-m', 'crossenv', cpython.install / 'bin' / 'python3', crossenv.build)

    build_pip = crossenv.build / 'build' / 'bin' / 'pip'
    Command(build_pip).install('cffi')

    base = crossenv.build / 'cross' / 'bin'
    python = Command(base / 'python3')
    pip = Command(base / 'pip3')
    return python, pip


def main() -> int:
    global configure, cmake, options
    parser = argparse.ArgumentParser()
    parser.add_argument('--arch', default='linux-x86_64', choices=['linux-x86_64', 'x86_64', 'aarch64'])
    parser.add_argument('--python', default='3.11')
    parser.add_argument('--android-api-level', type=int, default=21)
    options = parser.parse_args()

    python, pip = setup_python(options.python)

    os.environ['CFLAGS'] = '-fPIC'
    os.environ['CXXFLAGS'] = '-fPIC'

    if options.arch != 'linux-x86_64':
        env = setup_android_ndk(options.arch, api_level=options.android_api_level)
        configure = configure.bake(*env.autoconf_cross_args)
        # cmake = cmake.bake(*env.cmake_defines)


    build_sqlite('version-3.41.2', options.arch)
    build_libffi('v3.4.4', options.arch)
    build_openssl('OpenSSL_1_1_1t', options.arch)
    build_libgit2('v1.6.4', options.arch)
    build_cpython(python, 'v3.11.3', options.arch)

    if options.arch == 'linux-x86_64':
        host_python, host_pip = python, pip
    else:
        host_python, host_pip = setup_crossenv(python, pip, options.arch)

    build_pygit2(host_python, host_pip, options.arch)
