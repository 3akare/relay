#!/usr/bin/env python3
from commands import run_new, run_build, run_run
import argparse

# consts
RELAY_VERSION = "0.1.0"

def main():
    parser = argparse.ArgumentParser(
        description="C/C++ package manager",
    )

    # GLOBAL OPTIONS
    # version
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"relay {RELAY_VERSION}",
        help="Print version info and exit"
    )

    # toolchain
    parser.add_argument(
        "--toolchain",
        help="Specify the build toolchain triplet (e.g., x64-windows, x64-linux). Defaults to VCPKG_DEFAULT_TRIPLET environment variable or guesses based on OS."
    )

    # COMMANDS
    # new
    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands"
    )
    new_parser = subparsers.add_parser(
        "new",
        help="Create a new relay package"
    )
    new_parser.add_argument(
        "project_name",
        help="Name of the project directory to create"
    )
    new_parser.set_defaults(func=run_new)

    # build
    build_parser = subparsers.add_parser(
        "build",
         aliases=["b"],
        help="Compile the current package"
    )
    build_parser.set_defaults(func=run_build)

    # run
    run_parser = subparsers.add_parser(
        "run",
        aliases=["r"],
        help="Run a binary or example of the local package (make then run)"
    )
    run_parser.set_defaults(func=run_run)

    # TODO: clean, add, remove, update

    args = parser.parse_args()
    if (hasattr(args, 'func')):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()