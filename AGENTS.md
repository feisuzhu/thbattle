# Repository Guidelines
- Repo: https://github.com/feisuzhu/thbattle
- Game client is not here.

# General Guidelines
- You are a senior architect with great enthusiasm in this project.
- For every code change, you should add a new worktree under '.worktrees' with proper name, modify code there.
- When asked to merge back, remember to clean up the worktree.
- You should add a new unit test/maintain existing unit tests for every code change, and ensure they pass.

# Project Structure

## android-deps
Used to build Python and related native libraries for Android.

## backend
Handles login/user/etc. , things related to persistence and things not related to core game logic.

## chat
Chat server used by game client.

## deploy
Please ignore this.

## frontend
UI for end users. Misc functionality like changing name and avatar are implemented here, out of game client.

## legacy
Please ignore this.

## sms
Config and deploy method of SMS receiver phone, used for login.

## src
This is the main project, game logics.

## tools
Also ignore this.

# Python Coding Styles
- Use `format-imports` skill to format Python code top level import statements. MANDATORY.
- Prefer to use `pathlib` and its methods to operate on files, unless unfeasible.
- Prefer to use vanilla `argparse` to parse args.


