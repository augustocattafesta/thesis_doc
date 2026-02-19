import argparse
import os
import subprocess
import sys
import datetime
from enum import Enum
from packaging.version import Version, parse



class BumpMode(str, Enum):

    """Small enum class describing the bump mode.
    """

    MAJOR = "major"
    MINOR = "minor"
    PATCH = "patch"

def _cleanup() -> None:
    """Delete all auxiliary files generated during the build process.
    """
    _cmd("git", "clean", "-fdX")

def _compile() -> None:
    """Compile the TeX source code.
    """
    _cmd("latexmk", "-pdf", "-interaction=nonstopmode", "main.tex")

def _cmd(*args, verbose=False) -> subprocess.CompletedProcess:
    """Run a command in a subprocess.
    """
    # print(f"Executing command \"{' '.join(args)}\"...")
    result = subprocess.run(args, capture_output=True, text=True, check=True)
    if verbose:
        print(result.stdout)
    return result

def _get_latest_tag() -> Version:
    try:
        subprocess.run(['git', 'fetch', '--tags'], capture_output=True, check=True)
        tag = subprocess.run(
            ['git', 'describe', '--tags', '--abbrev=0'],
            capture_output=True, text=True, check=True
        )
        tag_str = tag.stdout.strip()
        return parse(tag_str)
    except (subprocess.CalledProcessError, ValueError):
        return parse("0.0.0")

def _bump_version(version: Version, mode: BumpMode) -> Version:
    """Bump the version string.
    """
    print(f'Bumping version (mode = {mode})...')
    major, minor, micro = version.release
    if mode == BumpMode.MAJOR:
        version_string = f"{major + 1}.0.0"
    elif mode == BumpMode.MINOR:
        version_string = f"{major}.{minor + 1}.0"
    elif mode == BumpMode.PATCH:
        version_string = f"{major}.{minor}.{micro + 1}"
    else:
        raise ValueError(f"Invalid bump mode {mode}")
    return Version(version_string)

def release(mode: BumpMode) -> None:
    print("Cleaning up the build directory...\n")
    _cleanup()
    print("Compiling the TeX source code...\n")
    _compile()

    latest_tag = _get_latest_tag()
    new_tag = _bump_version(latest_tag, mode)
    # Push the code to GitHub.    
    msg = F"Prepare for tag release {new_tag}.\n"
    _cmd("git", "add", ".")
    _cmd("git", "commit", "-m", msg)
    _cmd("git", "push")
    # Create the tag and push it.
    # _cmd("gh", "release", "create", f"{new_tag}", "main.pdf",
    #      "--title", f"Release {new_tag}", "--generate-notes")
    print(f"Release {new_tag} created successfully.")
    print("Cleaning up the build directory again...")
    _cleanup()



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Release a new version of the PDF.")
    parser.add_argument("mode",
                        choices=[mode.value for mode in BumpMode],
                        help="The bump mode to use.")
    args = parser.parse_args()
    release(args.mode)