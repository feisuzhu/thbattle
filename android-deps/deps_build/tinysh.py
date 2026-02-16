# -*- coding: utf-8 -*-

# -- stdlib --
import os
import shlex
import shutil
import subprocess
import sys
from contextlib import contextmanager
from typing import Any, Mapping

# -- third party --
# -- own --
from .escapes import escape_codes


# -- code --
class CommandFailed(Exception):
    def __init__(self, cmd, code):
        self.cmd = cmd
        self.code = code

    def __str__(self):
        return f"Command {self.cmd} failed with code {self.code}"


ENVIRON_STACK = []

P = escape_codes["bold_purple"]
N = escape_codes["reset"]

pr = lambda *args: print(*args, file=sys.stderr, flush=True)


class Command:
    def __init__(self, *args: Any):
        self.args = list((map(str, args)))

    def __getattribute__(self, name: str) -> Any:
        if name in ("args", "bake") or name.startswith("__"):
            return object.__getattribute__(self, name)

        return self.bake(name)

    def bake(self, *moreargs: Any) -> "Command":
        args = object.__getattribute__(self, "args")
        cls = object.__getattribute__(self, "__class__")
        return cls(*args, *moreargs)

    def __call__(self, *moreargs: Any) -> None:
        args = object.__getattribute__(self, "args")
        args = args + list(map(str, moreargs))

        overlay = {}
        for v in ENVIRON_STACK:
            overlay.update(v)
        cmd = " ".join([shlex.quote(v) for v in args])

        pr(f"{P}:: RUN {cmd}{N}")
        if overlay:
            pr(f"{P}>> WITH ADDITIONAL ENVS:{N}")
            for k, v in overlay.items():
                pr(f"{P}       {k}={v}{N}")

        env = os.environ.copy()
        env.update(overlay)

        exe = shutil.which(args[0])
        assert exe, f"Cannot find executable {args[0]}"

        proc = subprocess.Popen(args, executable=exe, env=env)
        code = proc.wait()
        if code:
            raise CommandFailed(cmd, code)

    def __repr__(self) -> str:
        return f"<Command '{shlex.join(self.args)}'>"


@contextmanager
def environ(*envs: Mapping[str, str]):
    """
    Set command environment variables.
    """
    global ENVIRON_STACK

    this = {}
    for env in envs:
        this.update(env)

    try:
        ENVIRON_STACK.append(this)
        yield
    finally:
        assert ENVIRON_STACK[-1] is this
        ENVIRON_STACK.pop()


@contextmanager
def chdir(dir):
    try:
        old = os.getcwd()
        os.chdir(str(dir))
        yield
    finally:
        os.chdir(old)


sh = Command()
git = sh.git
tar = sh.tar
bash = sh.bash
make = sh.make.bake('-j', os.cpu_count())
