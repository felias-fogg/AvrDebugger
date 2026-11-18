#!/usr/bin/env python3
"""
Add one platform of a release of AvrDebugger to the board manager index, together
with the tools it depends on. The package has a platform per architecture (avr,
megaavr), one folder each; a release calls this once per platform:

    python3 extras/update_index.py --index pages/package_felias-fogg_AvrDebugger_index.json \\
        --root avr --name AvrDebugger --version 1.0.0 --archive AvrDebugger-1.0.0.tar.bz2 \\
        --url https://github.com/felias-fogg/AvrDebugger/releases/download/v1.0.0/AvrDebugger-1.0.0.tar.bz2

Every platform depends on two tools of its own packager: avr-debugger (PyAvrOCD,
avr-gdb and simavr, from the PyAvrOCD release) and avrdude (from the avrdude
release). The avr platform does not name the compiler: it comes from arduino:avr,
whose core the boards use anyway. The others name arduino's avr-gcc (AVR_GCC), so
that the toolchain does not depend on what else is installed. Each tool is added to
the index once, when that version is not there yet; size and checksum come from the GitHub API, which reports a
SHA-256 for every release asset, so nothing has to be downloaded for them.

Running it twice for the same version changes nothing. A version that is in the
index with a different archive is refused: what people have installed under a
version number must not change behind their back.

Standard library only. GITHUB_TOKEN or GH_TOKEN is used when set, which the API's
rate limit for anonymous calls makes advisable on a shared runner.
"""

import argparse
import hashlib
import json
import os
import re
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from check_core import properties, board_ids    # pylint: disable=wrong-import-position

PACKAGER = "AvrDebugger"
OWNER = "felias-fogg"
AVR_GCC = "7.3.0-atmel3.6.1-arduino7"     # the one arduino:avr 1.8.x depends on

# avrdude's own archive names and the hosts arduino-cli knows them by. There is no
# arm64 macOS and no 64-bit Windows archive in this form: arduino-cli then takes
# the x86_64 macOS one (Rosetta) and the 32-bit Windows one, as for XMiniCore.
AVRDUDE_HOSTS = {
    "Linux_ARMv6": "arm-linux-gnueabihf",
    "Linux_ARM64": "aarch64-linux-gnu",
    "macOS_64bit": "x86_64-apple-darwin12",
    "Linux_64bit": "x86_64-linux-gnu",
    "Linux_32bit": "i686-linux-gnu",
    "Windows_32bit": "i686-mingw32",
}


def api(path: str):
    """One call to the GitHub API."""
    request = urllib.request.Request(f"https://api.github.com/{path}",
                                     headers={"Accept": "application/vnd.github+json"})
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request, timeout=60) as answer:
        return json.load(answer)


def release(repo: str, tag: str) -> dict:
    """
    A release by tag. 'latest' is the newest one that is not a pre-release, which
    is what the API itself means by it; 'newest' includes pre-releases, which a
    release candidate of this core may need to depend on.
    """
    if tag == "latest":
        return api(f"repos/{repo}/releases/latest")
    if tag == "newest":
        found = [r for r in api(f"repos/{repo}/releases?per_page=20") if not r["draft"]]
        if not found:
            sys.exit(f"{repo} has no release at all")
        return found[0]
    return api(f"repos/{repo}/releases/tags/{tag}")


def checksum(asset: dict) -> str:
    """The SHA-256 of an asset; downloaded and computed only if the API has none."""
    digest = asset.get("digest") or ""
    if digest.startswith("sha256:"):
        return "SHA-256:" + digest.split(":", 1)[1]
    print(f"  no digest for {asset['name']}, downloading it")
    sha = hashlib.sha256()
    with urllib.request.urlopen(asset["browser_download_url"], timeout=300) as data:
        for chunk in iter(lambda: data.read(1 << 20), b""):
            sha.update(chunk)
    return "SHA-256:" + sha.hexdigest()


def system(asset: dict, host: str) -> dict:
    """One entry of a tool's 'systems' list."""
    return {"size": str(asset["size"]), "checksum": checksum(asset), "host": host,
            "archiveFileName": asset["name"], "url": asset["browser_download_url"]}


def avr_debugger_tool(tag: str) -> dict:
    """The avr-debugger tool, out of the assets of a PyAvrOCD release."""
    rel = release(f"{OWNER}/PyAvrOCD", tag)
    pattern = re.compile(r"^avr-debugger-(?P<version>[^-]+)-(?P<host>.+)\.tar\.gz$")
    systems, versions = [], set()
    for asset in rel["assets"]:
        found = pattern.match(asset["name"])
        if found:
            versions.add(found["version"])
            systems.append(system(asset, found["host"]))
    if not systems:
        sys.exit(f"PyAvrOCD {rel['tag_name']} has no avr-debugger archives; it was "
                 "packed before the tools were called that")
    if len(versions) != 1:
        sys.exit(f"PyAvrOCD {rel['tag_name']} has avr-debugger archives of several "
                 f"versions: {sorted(versions)}")
    return {"name": "avr-debugger", "version": versions.pop(),
            "systems": sorted(systems, key=lambda s: s["host"])}


def avrdude_tool(tag: str) -> dict:
    """avrdude, out of the assets of an avrdude release."""
    rel = release("avrdudes/avrdude", tag)
    version = rel["tag_name"].lstrip("v")
    by_name = {a["name"]: a for a in rel["assets"]}
    systems = []
    for platform, host in AVRDUDE_HOSTS.items():
        name = f"avrdude_v{version}_{platform}.tar.gz"
        if name not in by_name:
            sys.exit(f"avrdude {version} does not ship {name} any more")
        systems.append(system(by_name[name], host))
    return {"name": "avrdude", "version": version, "systems": systems}


def package(index: dict) -> dict:
    """This core's package in the index, created on first use."""
    for pkg in index["packages"]:
        if pkg["name"] == PACKAGER:
            return pkg
    pkg = {"name": PACKAGER, "maintainer": OWNER,
           "websiteURL": f"https://github.com/{OWNER}/AvrDebugger", "email": "",
           "help": {"online": f"https://github.com/{OWNER}/AvrDebugger"},
           "platforms": [], "tools": []}
    index["packages"].append(pkg)
    return pkg


def add_tool(pkg: dict, tool: dict) -> None:
    """Add a tool version unless the index has it already."""
    for known in pkg["tools"]:
        if known["name"] == tool["name"] and known["version"] == tool["version"]:
            print(f"{tool['name']} {tool['version']} is in the index already")
            return
    pkg["tools"].append(tool)
    print(f"added {tool['name']} {tool['version']} for {len(tool['systems'])} hosts")


def add_platform(pkg: dict, entry: dict) -> None:
    """
    Add the platform version; the same one again is fine, a different one is not. A
    platform is known by its architecture and version: avr and megaavr of one release
    share the version.
    """
    for known in pkg["platforms"]:
        if known["architecture"] == entry["architecture"] and known["version"] == entry["version"]:
            if known["checksum"] == entry["checksum"]:
                print(f"{entry['name']} {entry['version']} is in the index already")
                return
            sys.exit(f"{entry['name']} {entry['version']} ({entry['architecture']}) is in the "
                     "index already, with a different archive. A published version is not "
                     "replaced; release a new one.")
    pkg["platforms"].append(entry)
    print(f"added {entry['name']} {entry['version']} ({entry['architecture']})")


def main() -> int:
    """Read the index, add what is missing, write it back."""
    parser = argparse.ArgumentParser(description="add a release to the board manager index")
    parser.add_argument("--index", required=True, help="the index file, created if missing")
    parser.add_argument("--version", required=True, help="the platform version, e.g. 1.0.0")
    parser.add_argument("--archive", required=True, help="the platform archive, for size and checksum")
    parser.add_argument("--url", required=True, help="where the archive is downloaded from")
    parser.add_argument("--pyavrocd", default="latest",
                        help="PyAvrOCD release tag, 'latest' (default) or 'newest'")
    parser.add_argument("--avrdude", default="latest", help="avrdude release tag or 'latest'")
    parser.add_argument("--root", required=True,
                        help="the platform folder (avr or megaavr), whose name is the architecture")
    parser.add_argument("--name", required=True, help="the name in the board manager")
    args = parser.parse_args()

    root = os.path.abspath(args.root)
    architecture = os.path.basename(root)
    boards = properties(os.path.join(root, "boards.txt"))

    if os.path.exists(args.index):
        with open(args.index, encoding="utf-8") as src:
            index = json.load(src)
    else:
        index = {"packages": []}
    pkg = package(index)

    debugger = avr_debugger_tool(args.pyavrocd)
    avrdude = avrdude_tool(args.avrdude)
    add_tool(pkg, debugger)
    add_tool(pkg, avrdude)

    dependencies = [
        {"packager": PACKAGER, "name": "avrdude", "version": avrdude["version"]},
        {"packager": PACKAGER, "name": "avr-debugger", "version": debugger["version"]},
    ]
    if architecture != "avr":
        # avr gets the compiler of arduino:avr, which its boards use anyway; the others
        # name the same one, so that the toolchain does not depend on what else is
        # installed (without it, arduino:megaavr would bring the older arduino5)
        dependencies.insert(0, {"packager": "arduino", "name": "avr-gcc",
                                "version": AVR_GCC})

    with open(args.archive, "rb") as src:
        data = src.read()
    add_platform(pkg, {
        "name": args.name,
        "architecture": architecture,
        "version": args.version,
        "category": "Contributed",
        "url": args.url,
        "archiveFileName": os.path.basename(args.archive),
        "checksum": "SHA-256:" + hashlib.sha256(data).hexdigest(),
        "size": str(len(data)),
        "boards": [{"name": boards[f"{b}.name"]} for b in board_ids(boards)],
        "toolsDependencies": dependencies,
    })

    with open(args.index, "w", encoding="utf-8") as out:
        json.dump(index, out, indent=2)
        out.write("\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
