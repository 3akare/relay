import os
import sys
import toml
import json
import platform
from pathlib import Path

try:
    from constants import (
        MANIFEST_FILE, VCPKG_MANIFEST_FILE, CMAKE_DEPENDENCY_MAPPING,
        CMAKE_FIND_END_MARKER, CMAKE_FIND_START_MARKER,
        CMAKE_LINK_END_MARKER, CMAKE_LINK_START_MARKER
    )
except ModuleNotFoundError:
    from relay.constants import (
        MANIFEST_FILE, VCPKG_MANIFEST_FILE, CMAKE_DEPENDENCY_MAPPING,
        CMAKE_FIND_END_MARKER, CMAKE_FIND_START_MARKER,
        CMAKE_LINK_END_MARKER, CMAKE_LINK_START_MARKER
    )

def find_project_root(verbose):
    current_dir = Path.cwd()
    for parent in [current_dir] + list(current_dir.parents):
        manifest_path = parent / MANIFEST_FILE
        cmakelists_path = parent / "CMakeLists.txt"
        if manifest_path.exists() and cmakelists_path.exists():
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
    sys.exit(1) # Exit if VCPKG_ROOT is not found or invalid

def get_vcpkg_triplet(toolchain_arg, verbose):
    if toolchain_arg:
        return toolchain_arg.lower()
    else:
        default_triplet = os.environ.get("VCPKG_DEFAULT_TRIPLET")
        if default_triplet:
            verbose and print(f"Using VCPKG_DEFAULT_TRIPLET environment variable: {default_triplet}")
            return default_triplet.lower()
    
    print("Warning: No --toolchain specified and VCPKG_DEFAULT_TRIPLET is not set.", file=sys.stderr)
    system = platform.system()
    machine = platform.machine()

    guessed_triplet = None
    if system == "Windows":
        guessed_triplet = "x64-windows" if machine in ('AMD64', 'x86_64') else "x86-windows"
    elif system == "Linux":
        guessed_triplet = "x64-linux" if machine in ('x86_64',) else f"{machine}-linux"
    elif system == "Darwin":
        guessed_triplet = "x64-osx" if machine in ('x86_64',) else f"{machine}-osx"
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
        dep_entry = {"name": name.lower()}
        if isinstance(details, dict) and "features" in details:
             if isinstance(details["features"], list):
                 dep_entry["features"] = [f.lower() for f in details["features"]]
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

def generate_vcpkg_json_from_relay_toml(project_root: Path):
    relay_toml_path = project_root / MANIFEST_FILE
    vcpkg_json_path = project_root / VCPKG_MANIFEST_FILE

    if not relay_toml_path.exists():
        print(f"Error: {MANIFEST_FILE} not found at {relay_toml_path}.")
        return False

    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        print(f"Error reading {MANIFEST_FILE}: {e}")
        return False
    
    dependencies = relay_config.get("dependencies", {})
    vcpkg_dependencies_list = []
    for dep_name, dep_version in dependencies.items():
        vcpkg_dependencies_list.append(dep_name)

    vcpkg_json_content = {
        "dependencies": sorted(vcpkg_dependencies_list)
    }
    
    if vcpkg_json_path.exists():
        try:
            with open(vcpkg_json_path, 'r') as f:
                existing_vcpkg_config = json.load(f)
            if "builtin-baseline" in existing_vcpkg_config:
                vcpkg_json_content["builtin-baseline"] = existing_vcpkg_config["builtin-baseline"]
            if "name" in existing_vcpkg_config:
                vcpkg_json_content["name"] = existing_vcpkg_config["name"]
        except json.JSONDecodeError:
            print(f"Warning: Existing {VCPKG_MANIFEST_FILE} is malformed. Creating new one.")
        except Exception as e:
            print(f"Warning: Could not read existing {VCPKG_MANIFEST_FILE} for baseline: {e}")
    try:
        with open(vcpkg_json_path, 'w') as f:
            json.dump(vcpkg_json_content, f, indent=4)
        print(f"Generated/Updated {VCPKG_MANIFEST_FILE} based on {MANIFEST_FILE}.")
        return True
    except IOError as e:
        print(f"Error writing to {VCPKG_MANIFEST_FILE}: {e}")
        return False

def update_cmake_lists_txt(project_root: Path):
    cmake_lists_path = project_root / "CMakeLists.txt"
    relay_toml_path = project_root / MANIFEST_FILE

    if not cmake_lists_path.exists():
        print(f"Error: CMakeLists.txt not found at {cmake_lists_path}. Cannot update.")
        return False
    if not relay_toml_path.exists():
        print(f"Error: {MANIFEST_FILE} not found at {relay_toml_path}. Cannot update CMakeLists.txt.")
        return False

    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        print(f"Error reading {MANIFEST_FILE} for CMake update: {e}")
        return False
    project_name = relay_config.get("project", {}).get("name")
    if not project_name:
        print(f"Error: 'project.name' not found in {MANIFEST_FILE}. Cannot update CMakeLists.txt.")
        return False

    dependencies = relay_config.get("dependencies", {})

    find_package_lines = []
    target_link_lines = []
    for dep_name in dependencies.keys():
        mapping = CMAKE_DEPENDENCY_MAPPING.get(dep_name)
        if mapping:
            find_package_lines.append(mapping["find_package"])
            target_link_lines.append(mapping["target_link"])
        else:
            print(f"Warning: No CMake mapping found for dependency '{dep_name}'. "
                  f"Please add it to CMAKE_DEPENDENCY_MAPPING in constants.py if needed, "
                  f"or handle it manually in CMakeLists.txt.")

    find_package_lines.sort()
    target_link_lines.sort()

    if target_link_lines:
        combined_target_link_line = f"target_link_libraries({project_name} PRIVATE " + " ".join(target_link_lines) + ")"
    else:
        combined_target_link_line = ""

    try:
        with open(cmake_lists_path, 'r') as f:
            lines = f.readlines()
    except IOError as e:
        print(f"Error reading CMakeLists.txt at {cmake_lists_path}: {e}")
        return False

    new_lines = []
    in_find_section = False
    in_link_section = False
    find_marker_found = False
    link_marker_found = False

    for line in lines:
        if CMAKE_FIND_START_MARKER in line:
            find_marker_found = True
            new_lines.append(line)
            in_find_section = True
            for fp_line in find_package_lines:
                new_lines.append(f"  {fp_line}\n")
            continue

        if CMAKE_FIND_END_MARKER in line:
            new_lines.append(line)
            in_find_section = False
            continue

        if CMAKE_LINK_START_MARKER in line:
            link_marker_found = True
            new_lines.append(line)
            in_link_section = True
            if combined_target_link_line:
                new_lines.append(f"  {combined_target_link_line}\n")
            continue

        if CMAKE_LINK_END_MARKER in line:
            new_lines.append(line)
            in_link_section = False
            continue

        if in_find_section or in_link_section:
            continue

        new_lines.append(line)

    if not find_marker_found:
        print(f"Warning: {CMAKE_FIND_START_MARKER} and {CMAKE_FIND_END_MARKER} not found in CMakeLists.txt.")
        print("Please add these markers to your CMakeLists.txt for automatic dependency discovery.")
    if not link_marker_found:
        print(f"Warning: {CMAKE_LINK_START_MARKER} and {CMAKE_LINK_END_MARKER} not found in CMakeLists.txt.")
        print("Please add these markers to your CMakeLists.txt for automatic dependency linking.")

    try:
        with open(cmake_lists_path, 'w') as f:
            f.writelines(new_lines)
        print(f"Successfully updated CMakeLists.txt at {cmake_lists_path}.")
        return True
    except IOError as e:
        print(f"Error writing to CMakeLists.txt: {e}")
        return False