import os
import sys
import toml;
import json
from pathlib import Path

try:
    from constants import MANIFEST_FILE, VCPKG_MANIFEST_FILE
except ModuleNotFoundError:
    from relay.constants import MANIFEST_FILE, VCPKG_MANIFEST_FILE
except Exception:
    pass


def find_project_root(verbose):
    current_dir = Path.cwd()
    for parent in [current_dir] + list(current_dir.parents):
        mainfest_path = parent / MANIFEST_FILE
        cmakelists_path = parent / "CMakeLists.txt"
        if mainfest_path.exists() and cmakelists_path.exists():
            verbose and print(f"Found project root: {parent}")
            return parent
    print(f"Error: Could not find project root. '{MANIFEST_FILE}' and 'CMakeLists.txt' not found in current directory or any parent directory.", file=sys.stderr)
    sys.exit(1)

def find_vcpkg_root(verbose):
    vcpkg_root = os.environ.get("VCPKG_ROOT")
    if vcpkg_root:
        vcpkg_root_path = Path(vcpkg_root)
        toolchain_file_standard = vcpkg_root_path / "scripts" / "buildsystems" / "vcpkg.cmake"
        if toolchain_file_standard.exists():
            verbose and print(f"Found VCPKG_ROOT from environment variable (standard layout): {vcpkg_root_path}")
            return vcpkg_root_path
        toolchain_file_homebrew = vcpkg_root_path / "share" / "vcpkg" / "vcpkg.cmake"
        if toolchain_file_homebrew.exists():
            verbose and print(f"Found VCPKG_ROOT from environment variable (Homebrew layout): {vcpkg_root_path}")
            return vcpkg_root_path
        print(f"Warning: VCPKG_ROOT environment variable is set to '{vcpkg_root}', but a valid vcpkg.cmake was not found in expected locations.", file=sys.stderr)
    print("Error: VCPKG_ROOT environment variable not set or invalid.", file=sys.stderr)
    print("Please set the VCPKG_ROOT environment variable to your vcpkg installation path (usually the Git clone directory).", file=sys.stderr)

def get_vcpkg_triplet(toolchain_arg, verbose):
    if toolchain_arg:
        return toolchain_arg.lower()
    else:
        default_triplet = os.environ.get("VCPKG_DEFAULT_TRIPLET")
        if default_triplet:
            verbose and print(f"Using VCPKG_DEFAULT_TRIPLET environment variable: {default_triplet}")
            return default_triplet.lower()
    print("Warning: No --toolchain specified and VCPKG_DEFAULT_TRIPLET is not set.", file=sys.stderr)
    import platform
    system = platform.system() # Windows, Linux, Darwin
    machine = platform.machine() # x86_64, aarch64, AMD64

    guessed_triplet = None
    if system == "Windows":
        guessed_triplet = "x64-windows" if machine in ('AMD64', 'x86_64') else "x86-windows"
    elif system == "Linux":
        guessed_triplet = "x64-linux" if machine in ('x86_64',) else f"{machine}-linux" # rudimentary guess
    elif system == "Darwin": # macOS
        guessed_triplet = "x64-osx" if machine in ('x86_64',) else f"{machine}-osx" # rudimentary guess
    else:
        print(f"Error: Cannot guess default triplet for unknown system '{system}'. Please specify --toolchain or set VCPKG_DEFAULT_TRIPLET.", file=sys.stderr)
        sys.exit(1)
    verbose and print(f"Guessing default triplet based on OS/architecture: {guessed_triplet}. Consider setting VCPKG_DEFAULT_TRIPLET or using --toolchain.", file=sys.stderr)
    return guessed_triplet

def get_build_dir(project_root, triplet):
    sanitized_triplet = triplet.replace('-', '_')
    build_dir = project_root / "build" / sanitized_triplet
    return build_dir

def generate_vcpkg_json(project_root, build_dir, verbose):
    relay_toml_path = project_root / MANIFEST_FILE
    vcpkg_json_path = project_root / VCPKG_MANIFEST_FILE

    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except FileNotFoundError:
        print(f"Error: Manifest file '{relay_toml_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except toml.TomlDecodeError as e:
        print(f"Error: Could not parse '{relay_toml_path}': {e}", file=sys.stderr)
        sys.exit(1)
    
    vcpkg_config = {
        "name": relay_config.get("project", {}).get("name", "unknown-project").lower(),
        "version": relay_config.get("project", {}).get("version", "0.0.0"),
        "dependencies": []
    }
    dependencies = relay_config.get("dependencies", {})
    if not isinstance(dependencies, dict):
        print(f"Warning: 'dependencies' section in {MANIFEST_FILE} is not a dictionary. Skipping dependency translation.", file=sys.stderr)
        dependencies = {}
    for name, details in dependencies.items():
        dep_entry = {"name": name.lower()} # vcpkg names are lowercase
        if isinstance(details, dict) and "features" in details:
             if isinstance(details["features"], list):
                 dep_entry["features"] = [f.lower() for f in details["features"]] # vcpkg features lowercase
             else:
                 print(f"Warning: Features for dependency '{name}' in {MANIFEST_FILE} is not a list. Skipping features.", file=sys.stderr)

        vcpkg_config["dependencies"].append(dep_entry)
    try:
        build_dir.mkdir(parents=True, exist_ok=True)
        vcpkg_json_path.write_text(json.dumps(vcpkg_config, indent=2))
        verbose and print(f"Generated {VCPKG_MANIFEST_FILE} at {vcpkg_json_path}")
    except OSError as e:
        print(f"Error writing {VCPKG_MANIFEST_FILE} to '{vcpkg_json_path}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
         print(f"An unexpected error occurred during {VCPKG_MANIFEST_FILE} generation: {e}", file=sys.stderr)
         sys.exit(1)