import argparse
import sys

try:
    from relay.constants import RELAY_VERSION
    from relay.commands import (
        run_new, run_build, run_run, run_clean,
        run_install_command, run_list_dependencies,
        run_remove_dependency, add_dependency_to_manifest
    )
    from relay.colours import colored, CYAN, BOLD, RED 
except ModuleNotFoundError:
    from constants import RELAY_VERSION
    from commands import (
        run_new, run_build, run_run, run_clean,
        run_install_command, run_list_dependencies,
        run_remove_dependency, add_dependency_to_manifest
    )
    from colours import colored, CYAN, BOLD, RED
except Exception:
    pass

def main():
    parser = argparse.ArgumentParser(
        description=colored("A C/C++ package manager", CYAN),
    )

    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"relay {colored(RELAY_VERSION, BOLD)}",
        help="Print version info and exit"
    )
    parser.add_argument(
        "--toolchain",
        help="Specify the build toolchain triplet (e.g., x64-windows, x64-linux). Defaults to VCPKG_DEFAULT_TRIPLET environment variable or guesses based on OS."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Use verbose output"
    )

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

    build_parser = subparsers.add_parser(
        "build",
        aliases=["b"],
        help="Compile the current package"
    )
    build_parser.set_defaults(func=run_build)

    run_parser = subparsers.add_parser(
        "run",
        aliases=["r"],
        help="Run a binary or example of the local package (make then run)"
    )
    run_parser.set_defaults(func=run_run)

    install_parser = subparsers.add_parser(
        "install",
        aliases=["i"],
        help="Install dependencies listed in Relay.toml via vcpkg"
    )
    install_parser.set_defaults(func=run_install_command)

    add_parser = subparsers.add_parser(
        "add",
        help="Add a dependency to Relay.toml (e.g., 'fmt', 'zlib')"
    )
    add_parser.add_argument(
        "dependency_name",
        help="Name of the dependency to add"
    )
    add_parser.set_defaults(func=add_dependency_to_manifest)

    remove_parser = subparsers.add_parser(
        "remove",
        aliases=["rm"],
        help="Remove a dependency from the project"
    )
    remove_parser.add_argument(
        "dependency_name",
        help="Name of the dependency to remove"
    )
    remove_parser.set_defaults(func=run_remove_dependency)

    list_parser = subparsers.add_parser(
        "list",
        aliases=["l"],
        help="List project dependencies"
    )
    list_parser.set_defaults(func=run_list_dependencies)

    clean_parser = subparsers.add_parser(
        "clean",
        help="Remove build artifacts and cached files"
    )
    clean_parser.set_defaults(func=run_clean)

    args = parser.parse_args()
    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        print(colored("\nError: No command specified.", RED), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()