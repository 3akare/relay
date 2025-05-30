import sys
import toml
import platform
from pathlib import Path

try:
    from utils import run_command
    from constants import MANIFEST_FILE, RELAY_VERSION, VCPKG_MANIFEST_FILE
    from templates import MAIN_C_TEMPLATE, MAIN_H_TEMPLATE, CMAKELISTS_TEMPLATE, RELAY_TOML_TEMPLATE, CLANG_FORMAT_TEMPLATE, GITIGNORE
    from helpers import find_project_root, find_vcpkg_root, get_vcpkg_triplet, get_build_dir, generate_vcpkg_json, generate_vcpkg_json_from_relay_toml, update_cmake_lists_txt
except ModuleNotFoundError:
    from relay.utils import run_command
    from relay.constants import MANIFEST_FILE, RELAY_VERSION, VCPKG_MANIFEST_FILE
    from relay.templates import MAIN_C_TEMPLATE, MAIN_H_TEMPLATE, CMAKELISTS_TEMPLATE, RELAY_TOML_TEMPLATE, CLANG_FORMAT_TEMPLATE, GITIGNORE
    from relay.helpers import find_project_root, find_vcpkg_root, get_vcpkg_triplet, get_build_dir, generate_vcpkg_json, generate_vcpkg_json_from_relay_toml, update_cmake_lists_txt
except Exception:
    pass

def run_new(args):
    verbose = args.verbose
    project_name = args.project_name
    project_path = Path(project_name)

    if project_path.exists():
        print(f"Error: Directory '{project_name}' already exists", file=sys.stderr)
        sys.exit(1)
    print(f"Creating binary (application) `{project_name}` package...")

    try:
        project_path.mkdir()
        (project_path / "src").mkdir()
        (project_path / "include").mkdir()

        main_c_content = MAIN_C_TEMPLATE.format(project_name=project_name)
        (project_path / "src" / "main.c").write_text(main_c_content)
        verbose and print("Created src/main.c")

        include_guard = f"{project_name.upper().replace('-', '_').replace('.', '_')}_H"
        main_h_content = MAIN_H_TEMPLATE.format(include_guard=include_guard)
        (project_path / "include" / f"{project_name}.h").write_text(main_h_content)
        verbose and print(f"Created include/{project_name}.h")

        cmakelist_content = CMAKELISTS_TEMPLATE.format(project_name=project_name)
        (project_path / "CmakeLists.txt").write_text(cmakelist_content)
        verbose and print("Created CmakeLists.txt")

        (project_path / ".clang-format").write_text(CLANG_FORMAT_TEMPLATE)
        verbose and print("Created .clang-format")

        (project_path / ".gitignore").write_text(GITIGNORE)
        git_init_command = ["git", "init", str(project_path)]
        run_command(git_init_command, verbose=verbose)
        verbose and print("Created .gitignore")
        
        relay_toml_content = RELAY_TOML_TEMPLATE.format(project_name=project_name)
        (project_path / MANIFEST_FILE).write_text(relay_toml_content)
        verbose and print(f"Created {MANIFEST_FILE}")

        print(f"\nSuccessfully created project '{project_name}'.")
        print("Next steps:")
        print(f"  cd {project_name}")
        print(f"  # Add dependencies to {MANIFEST_FILE} (e.g., under [dependencies])")
        print(f"  # Update CMakeLists.txt to find and link added dependencies")
        print(f"  # Set VCPKG_ROOT environment variable to your vcpkg directory")
        print(f"  relay [--toolchain <triplet>] build")

    except OSError as e:
        print(f"Error creating project directories or files: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occured: {e}", file=sys.stderr)
        sys.exit(1)

def run_build(args):
    verbose = args.verbose
    toolchain = args.toolchain

    print("Building project...")
    project_root = find_project_root(verbose)
    vcpkg_root = find_vcpkg_root(verbose)

    vcpkg_toolchain_file = vcpkg_root / "scripts" / "buildsystems" / "vcpkg.cmake"
    if not vcpkg_toolchain_file.exists():
         vcpkg_toolchain_file = vcpkg_root / "share" / "vcpkg" / "vcpkg.cmake"
         if not vcpkg_toolchain_file.exists():
            print(f"Error: vcpkg toolchain file not found at expected locations relative to VCPKG_ROOT: {vcpkg_root}", file=sys.stderr)
            print("Looked for:",
                  vcpkg_root / "scripts" / "buildsystems" / "vcpkg.cmake", "and",
                  vcpkg_root / "share" / "vcpkg" / "vcpkg.cmake", file=sys.stderr)
            print("Please ensure VCPKG_ROOT is set correctly and vcpkg is installed properly (usually requires cloning the Git repository).", file=sys.stderr)
            sys.exit(1)

    triplet = get_vcpkg_triplet(toolchain, verbose)
    verbose and print(f"Using vcpkg triplet: {triplet}")

    build_dir = get_build_dir(project_root, triplet)
    verbose and print(f"Build directory: {build_dir}")

    generate_vcpkg_json(project_root, build_dir, verbose)

    verbose and print("\n--- Configuring CMake ---")
    cmake_configure_command = [
        "cmake",
        str(project_root), 
        "-B", str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={vcpkg_toolchain_file}",
        f"-DVCPKG_TARGET_TRIPLET={triplet}",
    ]
    if not run_command(cmake_configure_command, verbose=verbose):
        print("\nCMake configuration failed.", file=sys.stderr)
        sys.exit(1)

    verbose and print("\n--- Building Project ---")
    cmake_build_command = [
        "cmake",
        "--build", str(build_dir),
    ]
    if not run_command(cmake_build_command, verbose=verbose):
        print("\nProject build failed.", file=sys.stderr)
        sys.exit(1)
    print("Build successful!")

def run_run(args):
    verbose = args.verbose
    verbose and print("Running project...")

    project_root = find_project_root(verbose)
    
    if not project_root:
        run_build(args)

    triplet = get_vcpkg_triplet(args.toolchain, verbose)
    build_dir = get_build_dir(project_root, triplet)
    relay_toml_path = project_root / MANIFEST_FILE

    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
        project_name = relay_config.get("project", {}).get("name", project_root.name)
        executable_name = relay_config.get("project", {}).get("main_executable", project_name)
    except FileNotFoundError:
        print(f"Error: Manifest file '{relay_toml_path}' not found.", file=sys.stderr)
        sys.exit(1)
    except toml.TomlDecodeError as e:
        print(f"Error: Could not parse '{relay_toml_path}': {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
         print(f"An unexpected error occurred while reading project name from {MANIFEST_FILE}: {e}", file=sys.stderr)
         sys.exit(1)

    exe_extension = ".exe" if platform.system() == "Windows" else ""
    executable_path = build_dir / f"{executable_name}{exe_extension}"

    if not executable_path.exists():
        print(f"Error: Executable not found at expected path: {executable_path}", file=sys.stderr)
        print("Please ensure the project built successfully and check your CMakeLists.txt for the executable target name.", file=sys.stderr)
        sys.exit(1)

    if not run_command(command=[str(executable_path)], cwd=build_dir, verbose=verbose):
        print("\nProject run failed.", file=sys.stderr)
        sys.exit(1)

def run_install_command(args):
    verbose = args.verbose
    print("\nStarting dependency installation process...")

    project_root = find_project_root(verbose)
    if not project_root:
        print("Error: Could not find project root. Are you in a Relay project?")
        return

    if not generate_vcpkg_json_from_relay_toml(project_root):
        print("Installation aborted: Failed to generate vcpkg.json.")
        return

    vcpkg_root = find_vcpkg_root(verbose)
    if not vcpkg_root:
        print("Error: Could not find VCPKG_ROOT environment variable or vcpkg executable.")
        print("Please ensure vcpkg is installed and VCPKG_ROOT is set correctly, or it's in your system's PATH.")
        return

    vcpkg_executable = vcpkg_root / "vcpkg"
    if platform.system() == "Windows":
        vcpkg_executable = vcpkg_root / "vcpkg.exe"

    if not vcpkg_executable.is_file():
        print(f"Error: vcpkg executable not found at '{vcpkg_executable}'.")
        return

    print(f"Running vcpkg install in {project_root}...")
    vcpkg_command = [str(vcpkg_executable), "install"]

    if hasattr(args, 'toolchain') and args.toolchain:
        vcpkg_command.append(f"--triplet={args.toolchain}")
        print(f"Using toolchain: {args.toolchain}")

    result = run_command(vcpkg_command, cwd=project_root)

    if result:
        print("\nDependencies installed successfully via vcpkg.")
        print("Attempting to update CMakeLists.txt automatically...")
        if update_cmake_lists_txt(project_root):
            print("CMakeLists.txt updated successfully.")
        else:
            print("Failed to automatically update CMakeLists.txt. Please check for errors.")
            print("You might need to manually add dependency calls to your CMakeLists.txt.")
    else:
        print(f"\nError: Vcpkg install failed with exit code {result}.", file=sys.stderr)
        print("Vcpkg output:", file=sys.stderr)
        print(result, file=sys.stderr)
        return 
    print("\nDependency installation process complete.")

def add_dependency_to_manifest(args):
    verbose = args.verbose
    dependency_name = args.dependency_name
    print(f"\nAdding dependency '{dependency_name}' to {MANIFEST_FILE}...")

    project_root = find_project_root(verbose)
    if not project_root:
        print("Error: Could not find project root. Are you in a Relay project (missing Relay.toml or vcpkg.json)?")
        return

    relay_toml_path = project_root / MANIFEST_FILE

    if not relay_toml_path.exists():
        print(f"Warning: {MANIFEST_FILE} not found. Creating a minimal one.")
        try:
            with open(relay_toml_path, 'w') as f:
                toml.dump({"project": {"name": project_root.name, "version": "0.1.0", "type": "executable"}}, f)
        except IOError as e:
            print(f"Error creating {MANIFEST_FILE}: {e}", file=sys.stderr)
            return

    relay_config = {}
    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        print(f"Error reading {MANIFEST_FILE}: {e}", file=sys.stderr)
        return

    if "dependencies" not in relay_config:
        relay_config["dependencies"] = {}

    if dependency_name in relay_config["dependencies"]:
        print(f"Dependency '{dependency_name}' already exists in {MANIFEST_FILE}.")
    else:
        relay_config["dependencies"][dependency_name] = "*"
        print(f"Added '{dependency_name}' to {MANIFEST_FILE}.")

    try:
        with open(relay_toml_path, 'w') as f:
            toml.dump(relay_config, f)
        print(f"Successfully updated {MANIFEST_FILE}.")
    except IOError as e:
        print(f"Error writing to {MANIFEST_FILE}: {e}", file=sys.stderr)
        return

    if not generate_vcpkg_json_from_relay_toml(project_root):
        print("Error: Failed to generate vcpkg.json after updating Relay.toml.", file=sys.stderr)
        return
    print(f"\nUse 'relay install' to download and build the dependencies.")

def run_remove_dependency(args):
    dependency_name = args.dependency_name
    verbose = args.verbose
    verbose and print(f"\nAttempting to remove dependency: '{dependency_name}'...")

    project_root = find_project_root(verbose)
    if not project_root:
        print("Error: Could not find project root. Are you in a Relay project?")
        return

    relay_toml_path = project_root / MANIFEST_FILE
    if not relay_toml_path.exists():
        print(f"Error: {MANIFEST_FILE} not found at {relay_toml_path}. Cannot remove dependency.", file=sys.stderr)
        return

    relay_config = {}
    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        print(f"Error reading {MANIFEST_FILE}: {e}", file=sys.stderr)
        return

    dependencies = relay_config.get("dependencies", {})
    if dependency_name in dependencies:
        del dependencies[dependency_name]
        relay_config["dependencies"] = dependencies
        print(f"Removed '{dependency_name}' from {MANIFEST_FILE}.")
    else:
        print(f"Dependency '{dependency_name}' not found in {MANIFEST_FILE}. Nothing to remove.")
        return

    try:
        with open(relay_toml_path, 'w') as f:
            toml.dump(relay_config, f)
        print(f"Successfully updated {MANIFEST_FILE}.")
    except IOError as e:
        print(f"Error writing to {MANIFEST_FILE}: {e}", file=sys.stderr)
        return

    if not generate_vcpkg_json_from_relay_toml(project_root):
        print("Error: Failed to regenerate vcpkg.json after removing dependency.", file=sys.stderr)
        return

    print("Updating CMakeLists.txt to reflect dependency changes...")
    if update_cmake_lists_txt(project_root):
        print("CMakeLists.txt updated successfully.")
    else:
        print("Failed to automatically update CMakeLists.txt. Please check for errors.", file=sys.stderr)
        print("You might need to manually remove dependency calls from your CMakeLists.txt.", file=sys.stderr)

    print("\nDependency removal process complete.")
    print(f"Run 'relay install' to re-sync your vcpkg installations, then 'relay build' to rebuild your project.")
    print(f"You might also want to run 'relay clean' before rebuilding.")

def run_list_dependencies(args):
    verbose = args.verbose
    print("\nListing Project Dependencies...")
    print("================================")

    project_root = find_project_root(verbose)
    if not project_root:
        print("Error: Could not determine project root.", file=sys.stderr)
        return

    relay_toml_path = project_root / MANIFEST_FILE

    if not relay_toml_path.exists():
        print(f"Error: {MANIFEST_FILE} not found at {relay_toml_path}. Is this a Relay project?", file=sys.stderr)
        sys.exit(1)

    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except toml.TomlDecodeError as e:
        print(f"Error: Could not parse {MANIFEST_FILE} at {relay_toml_path}: {e}", file=sys.stderr)
        sys.exit(1)

    dependencies = relay_config.get("dependencies")

    if not dependencies:
        print("No dependencies found in Relay.toml.")
    elif not isinstance(dependencies, dict):
        print(f"Warning: 'dependencies' section in {MANIFEST_FILE} is not a valid dictionary.", file=sys.stderr)
        print("Please check your Relay.toml format.", file=sys.stderr)
    else:
        sorted_deps = sorted(dependencies.items())
        for dep_name, dep_version in sorted_deps:
            if dep_version == "*":
                print(f"  {dep_name} (any compatible version)")
            else:
                print(f"  {dep_name} == {dep_version}")

    print("\nDependency listing complete.")

def run_clean(args):
    verbose = args.verbose
    toolchain = args.toolchain
    print("Cleaning build artifacts...")

    project_root = find_project_root(verbose)
    triplet = get_vcpkg_triplet(toolchain, verbose)
    build_dir = get_build_dir(project_root, triplet=triplet)
    if build_dir.exists():
        print(f"Removing build directory: {build_dir}")
        import shutil
        shutil.rmtree(Path(build_dir).parent)
    else:
        print("No build directory found to clean.")