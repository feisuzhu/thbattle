#!/usr/bin/env -S uv run
# /// script
# dependencies = ["requests"]
# ///

import sys

import deps_build.entry

if __name__ == "__main__":
    sys.exit(deps_build.entry.main())
