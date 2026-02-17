---
name: format-imports
description: Rewrite Python script's top level import statements to comply coding standard
---

# Format Imports

Rewrite Python script's top level import statements to comply coding standard

## Usage

Run the deployment script: `scripts/format-imports.py --files <target>`. The script have shebang and executable bit set, run it directly.
The script will rewrite the target inplace.
The script will only modify top level import statements, other code will be left untouched.
