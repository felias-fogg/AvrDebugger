#!/usr/bin/env python3
"""
Check AvrDebugger for the kinds of mistake that only show up when someone else uses it.

    python3 extras/check_core.py              # check the core this file belongs to
    python3 extras/check_core.py --tag v1.0.0 # and that it is ready to be released

AvrDebugger has neither core nor variants of its own: its visible boards take both
from arduino:avr, and all other boards of Arduino AVR Boards are only carried along,
hidden. So the checks are about that arrangement and about the debug configuration,
not about variants. Same interface as XMiniCore's check_core.py, and the helpers
that check_hooks.py, compile_all.py and changelog_entry.py import from it are the
same, except that board_ids() returns only the boards a user can choose.

Needs nothing but the files themselves and the standard library. Errors make it
exit non-zero; warnings are printed and do not.
"""

import argparse
import contextlib
import os
import re
import sys
import tempfile

PROBLEMS: list = []
WARNINGS: list = []

# What every board name ends in: a connected board matches arduino:avr as well, and
# the IDE lists both by name only.
MARKER = " (debug)"


@contextlib.contextmanager
def working_directory(given: str):
    """The directory to work in: the one that was asked for, or a temporary one."""
    if given:
        os.makedirs(given, exist_ok=True)
        yield given
    else:
        with tempfile.TemporaryDirectory() as folder:
            yield folder


def base_version(tag: str) -> str:
    """
    The version a tag belongs to. A pre-release such as v1.0.0-rc4 belongs to
    1.0.0 and has neither a version of its own in platform.txt nor an entry of
    its own in the changelog; that is the point of trying one out.
    """
    return tag.lstrip("v").split("-", 1)[0]


def problem(text: str) -> None:
    """Record something that must be fixed before a release."""
    PROBLEMS.append(text)


def warn(text: str) -> None:
    """Record something worth a look that does not stop a release."""
    WARNINGS.append(text)


def properties(path: str) -> dict:
    """
    Read an Arduino properties file. Keys repeat the board id, values may contain
    anything, comments start with # at the beginning of a line.
    """
    found = {}
    if not os.path.exists(path):
        problem(f"{os.path.basename(path)} is missing")
        return found
    with open(path, encoding="utf-8", errors="replace") as src:
        for line in src:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            found[key.strip()] = value.strip()
    return found


def all_board_ids(boards: dict) -> list:
    """Every id that has a name is a board; menu declarations and the like are not."""
    return sorted(key[:-len(".name")] for key in boards
                  if key.endswith(".name") and key.count(".") == 1)


def board_ids(boards: dict) -> list:
    """
    The boards a user can choose, which are what compile_all.py builds and what the
    index lists. The hidden ones compile as well, but are not offered.
    """
    return [b for b in all_board_ids(boards) if boards.get(f"{b}.hide") != "true"]


def check_boards(boards: dict) -> None:
    """Visible boards borrow from arduino:avr, hidden ones are hidden for real."""
    visible = board_ids(boards)
    if not visible:
        problem("no board is visible")
    for board in all_board_ids(boards):
        name = boards[f"{board}.name"]
        if not name.endswith(MARKER):
            problem(f"board '{board}' is called '{name}', without '{MARKER.strip()}'")
        hide = boards.get(f"{board}.hide")
        if hide is not None and hide != "true":
            # arduino-cli tests for exactly 'true', whatever the specification says
            problem(f"board '{board}' has hide={hide}, which arduino-cli does not take "
                    "for hidden; it has to be 'true'")
    # The hidden boards as well: a single 'hide=false' in boards.local.txt is all a
    # user should need to get one back.
    for board in all_board_ids(boards):
        core = boards.get(f"{board}.build.core", "")
        if core != "arduino:arduino":
            problem(f"board '{board}' has build.core={core}, not arduino:arduino")
        variants = [v for k, v in boards.items()
                    if k == f"{board}.build.variant"
                    or (k.startswith(f"{board}.menu.") and k.endswith(".build.variant"))]
        if not variants:
            problem(f"board '{board}' has no build.variant")
        for variant in variants:
            if not variant.startswith("arduino:"):
                problem(f"board '{board}' uses variant '{variant}', which is looked for "
                        "here rather than in arduino:avr")


def check_server_args(name: str, props: dict) -> None:
    """
    The serverArgs keys are compared as numbers by arduino-cli, but the simavr
    programmer replaces serverArgs.01 by its key. A key spelled differently ('1')
    would add an argument instead of replacing one, so all of them are two digits
    and they leave no gap.
    """
    prefix = "debug.cortex-debug.custom.serverArgs."
    keys = [k[len(prefix):] for k in props if k.startswith(prefix)]
    keys += [k.split(prefix, 1)[1] for k in props if f".{prefix}" in k]
    for key in keys:
        if not re.fullmatch(r"\d\d", key):
            problem(f"{name}: serverArgs.{key} is not a two-digit key")
    if name == "platform.txt":
        numbers = sorted(int(k) for k in keys if k.isdigit())
        if numbers != list(range(len(numbers))):
            problem(f"platform.txt: the serverArgs keys have a gap: {numbers}")


def check_debug(platform: dict) -> None:
    """The debug tools come from this platform's own tool."""
    path = platform.get("debug.toolchain.path", "")
    if "{runtime.tools.avr-debugger.path}" not in path:
        problem(f"debug.toolchain.path is '{path}', not the avr-debugger tool")
    if not platform.get("debug.cortex-debug.custom.overrideGDBServerStartedRegex"):
        problem("overrideGDBServerStartedRegex is missing, so the IDE would start "
                "the GDB client before the server listens")


def check_hook_scripts(root: str, platform: dict) -> None:
    """
    Every script a recipe calls has to be there, on every platform. This
    platform's own files are reached through {build.board.platform.path}, because
    {runtime.platform.path} points at arduino:avr.
    """
    pattern = re.compile(r"\{build\.board\.platform\.path\}[/\\]([\w/\\.-]+)")
    for key, value in platform.items():
        if not key.startswith("recipe."):
            continue
        if "{runtime.platform.path}" in value:
            problem(f"{key} uses {{runtime.platform.path}}, which is arduino:avr here")
        for relative in pattern.findall(value):
            path = os.path.join(root, relative.replace("\\", "/"))
            if not os.path.exists(path):
                problem(f"{key} calls '{relative}', which does not exist")


def check_line_endings(root: str) -> None:
    """Windows batch files need CRLF, and git only keeps it with a rule for it."""
    attributes = os.path.join(root, ".gitattributes")
    rule = ""
    if os.path.exists(attributes):
        with open(attributes, encoding="utf-8", errors="replace") as src:
            rule = src.read()
    if ".bat" in rule:
        return
    for folder, _, files in os.walk(root):
        if ".git" in folder:
            continue
        if any(f.endswith(".bat") for f in files):
            problem("there are .bat files but .gitattributes has no rule for them, "
                    "so their CRLF line endings depend on whoever clones the core")
            return


def check_release(repo: str, platforms: dict, tag: str) -> None:
    """
    Before a release the version has to be stated in the platform.txt of every
    platform and in the changelog. A pre-release tag such as v1.0.0-rc1 is checked
    against 1.0.0.
    """
    version = base_version(tag)
    for name, platform in platforms.items():
        stated = platform.get("version")
        if stated != version:
            problem(f"{name}/platform.txt says version={stated}, but the tag says {version}")
    changelog = os.path.join(repo, "CHANGELOG.md")
    if not os.path.exists(changelog):
        problem("there is no CHANGELOG.md, and the release notes come from there")
        return
    with open(changelog, encoding="utf-8", errors="replace") as src:
        text = src.read()
    if not re.search(rf"^#+\s*v?{re.escape(version)}\s*$", text, re.MULTILINE):
        problem(f"CHANGELOG.md has no entry for {version}")


def platform_folders(repo: str) -> list:
    """The platforms of the package: every folder of the repository with a platform.txt"""
    return sorted(entry for entry in os.listdir(repo)
                  if os.path.isfile(os.path.join(repo, entry, "platform.txt")))


def main() -> int:
    """Run every check and report what came out of it."""
    parser = argparse.ArgumentParser(description="check AvrDebugger for consistency")
    parser.add_argument("--root", help="the repository (default: the one above this); "
                        "a platform folder in it, as release.sh passes, means the same")
    parser.add_argument("--tag", help="also check that the core is ready for this tag")
    args = parser.parse_args()

    repo = os.path.abspath(args.root or os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if os.path.isfile(os.path.join(repo, "platform.txt")):
        repo = os.path.dirname(repo)        # release.sh names avr/, the platforms live beside it
    folders = platform_folders(repo)
    if not folders:
        problem(f"no platform folder (with a platform.txt) in {repo}")
    platforms = {}
    for name in folders:
        root = os.path.join(repo, name)
        boards = properties(os.path.join(root, "boards.txt"))
        platform = properties(os.path.join(root, "platform.txt"))
        programmers = properties(os.path.join(root, "programmers.txt"))
        platforms[name] = platform
        print(f"checking {name}")
        print(f"  {len(all_board_ids(boards))} boards, {len(board_ids(boards))} of them "
              f"visible, {len(platform)} platform properties")
        check_boards(boards)
        check_server_args(f"{name}/platform.txt", platform)
        check_server_args(f"{name}/programmers.txt", programmers)
        check_debug(platform)
        check_hook_scripts(root, platform)
    versions = {platform.get("version") for platform in platforms.values()}
    if len(versions) > 1:
        problem("the platforms state different versions: " +
                ", ".join(f"{n} {p.get('version')}" for n, p in platforms.items()))
    check_line_endings(repo)
    if args.tag:
        check_release(repo, platforms, args.tag)

    for text in WARNINGS:
        print(f"  warning: {text}")
    for text in PROBLEMS:
        print(f"  PROBLEM: {text}")
    if PROBLEMS:
        print(f"{len(PROBLEMS)} problem(s)")
        return 1
    print("no problems found")
    return 0

if __name__ == "__main__":
    sys.exit(main())
