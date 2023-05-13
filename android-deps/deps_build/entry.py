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
from .tinysh import Command, chdir, git, make, environ, sh


# -- code --
options = None
configure = Command("./configure")
cmake = Command("cmake")


class ProjectPaths:
    ROOT = misc.get_cache_home()
    INSTALLS = ROOT / "installs"
    BUILDS = ROOT / "builds"
    REPOS = ROOT / "repos"

    def __init__(self, project, arch):
        self.project = project
        self.arch = arch

    @property
    @lru_cache(1)
    def repo(self):
        self.REPOS.mkdir(parents=True, exist_ok=True)
        return self.REPOS / self.project

    @property
    @lru_cache(1)
    def build(self):
        return self.BUILDS / self.arch / self.project

    @property
    @lru_cache(1)
    def install(self):
        return self.INSTALLS / self.arch / self.project

    @property
    @lru_cache(1)
    def lib(self):
        return self.install / "lib"

    @property
    @lru_cache(1)
    def include(self):
        return self.install / "include"

    @property
    @lru_cache(1)
    def pkgconfig(self):
        return self.lib / "pkgconfig"

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


class PkgConfig:
    def __init__(self):
        self.paths = []

    def add(self, proj: ProjectPaths):
        p = proj.pkgconfig
        if p not in self.paths:
            self.paths.append(p)
            os.environ['PKG_CONFIG_PATH'] = ':'.join(map(str, reversed(self.paths)))


pkgconfig = PkgConfig()


@banner("Build libgit2 {arch}")
def build_libgit2(version: str, arch: str = 'linux-x86_64'):
    libgit2 = ProjectPaths('libgit2', arch)
    pkgconfig.add(libgit2)
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
    with environ({'LIBGIT2': str(libgit2.install)}):
        pip.install('pygit2')


@banner("Build trivial python packages {arch}")
def build_trivial_packages(python: Command, pip: Command, arch: str = 'linux-x86_64'):
    pip.install('msgpack')


@banner("Build gevent {arch}")
def build_gevent(python: Command, pip: Command, version: str, arch: str = 'linux-x86_64'):
    gevent = ProjectPaths('gevent', arch)

    libev = ProjectPaths('libev', arch)

    gevent.repo.exists() or git.clone('https://github.com/gevent/gevent.git', gevent.repo)
    gevent.clean()
    envs = {
        'GEVENTSETUP_EMBED_LIBEV': '0',
        'GEVENTSETUP_EMBED_CARES': '0',
        'CFLAGS': f'{os.environ.get("CFLAGS", "")} -I{libev.include}',
        'LDFLAGS': f'{os.environ.get("LDFLAGS", "")} -L{libev.lib}',
    }

    with chdir(gevent.repo):
        git.checkout(version)
        sh.sed('-i', '/LIBUV_CFFI_MODULE/d', 'setup.py')
        with environ(envs):
            pip.install('.')


@banner("Build openssl {arch}")
def build_openssl(version: str, arch: str = 'linux-x86_64'):
    arch_map = {
        'linux-x86_64': 'linux-x86_64',
        'x86_64': 'android-x86_64',
        'aarch64': 'android-arm64',
    }

    openssl = ProjectPaths('openssl', arch)
    pkgconfig.add(openssl)
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
    pkgconfig.add(libffi)
    if libffi.is_installed():
        return

    libffi.repo.exists() or git.clone('https://github.com/libffi/libffi.git', libffi.repo)
    libffi.clean()

    with chdir(libffi.repo):
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
    pkgconfig.add(sqlite)
    if sqlite.is_installed():
        return

    sqlite.repo.exists() or git.clone('https://github.com/sqlite/sqlite.git', sqlite.repo)
    sqlite.clean()

    with chdir(sqlite.repo):
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
    pkgconfig.add(cpython)
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
    python('-m', 'crossenv', cpython.install / 'bin' / 'python3', crossenv.install)

    build_pip = crossenv.install / 'build' / 'bin' / 'pip'
    Command(build_pip).install('cffi')

    base = crossenv.install / 'cross' / 'bin'
    python = Command(base / 'python3')
    pip = Command(base / 'pip3')
    return python, pip


@banner("Build libev {arch}")
def build_libev(version: str, arch: str = 'linux-x86_64'):
    libev = ProjectPaths('libev', arch)
    if libev.is_installed():
        return

    libev.repo.exists() or git.clone('https://github.com/xorangekiller/libev-git.git', libev.repo)
    libev.clean()

    with chdir(libev.repo):
        git.checkout(version)

    with chdir(libev.build):
        cmake(libev.repo, '-DBUILD_SHARED_LIBS=OFF',
                          '-DCMAKE_BUILD_TYPE=Release',
                          '-DCMAKE_POSITION_INDEPENDENT_CODE=ON',
                          f'-DCMAKE_INSTALL_PREFIX={libev.install}')
        make()
        make.install()
        libev.set_installed()



@banner("Build c-ares {arch}")
def build_c_ares(version: str, arch: str = 'linux-x86_64'):
    c_ares = ProjectPaths('c-ares', arch)
    pkgconfig.add(c_ares)
    if c_ares.is_installed():
        return

    c_ares.repo.exists() or git.clone('https://github.com/c-ares/c-ares.git', c_ares.repo)
    c_ares.clean()

    with chdir(c_ares.repo):
        git.checkout(version)
        sh.aclocal()
        sh.autoheader()
        sh.libtoolize()
        sh.automake('--add-missing')
        sh.autoconf()
        configure(f"--prefix={c_ares.install}", "--disable-shared", "--enable-static")
        make()
        make.install()
        c_ares.set_installed()


@banner("Strip binaries {arch}")
def strip_binaries(arch: str = 'linux-x86_64'):
    strip = Command('llvm-strip')

    for p in ProjectPaths.INSTALLS.glob(f'{arch}/**/*.so'):
        strip(p)


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
    os.environ['MAKEFLAGS'] = f'-j {os.cpu_count()}'

    if options.arch != 'linux-x86_64':
        env = setup_android_ndk(options.arch, api_level=options.android_api_level)
        configure = configure.bake(*env.autoconf_cross_args)
        # cmake = cmake.bake(*env.cmake_defines)

    build_sqlite('version-3.41.2', options.arch)
    build_libffi('v3.4.4', options.arch)
    build_openssl('OpenSSL_1_1_1t', options.arch)
    build_libgit2('v1.6.4', options.arch)
    build_libev('master', options.arch)
    build_c_ares('cares-1_19_0', options.arch)
    build_cpython(python, 'v3.11.3', options.arch)

    if options.arch == 'linux-x86_64':
        host_python, host_pip = python, pip
    else:
        host_python, host_pip = setup_crossenv(python, pip, options.arch)

    build_trivial_packages(host_python, host_pip, options.arch)
    build_gevent(host_python, host_pip, '22.10.2', options.arch)
    build_pygit2(host_python, host_pip, options.arch)

    strip_binaries(options.arch)
