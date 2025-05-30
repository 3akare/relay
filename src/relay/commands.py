import sys
import toml
import platform
from pathlib import Path

try:
    from utils import run_command
    from constants import MANIFEST_FILE
    from templates import MAIN_C_TEMPLATE, MAIN_H_TEMPLATE, CMAKELISTS_TEMPLATE, RELAY_TOML_TEMPLATE, CLANG_FORMAT_TEMPLATE, GITIGNORE
    from helpers import find_project_root, find_vcpkg_root, get_vcpkg_triplet, get_build_dir, generate_vcpkg_json, generate_vcpkg_json_from_relay_toml, update_cmake_lists_txt
    from colours import colored, GREEN, YELLOW, RED, CYAN, BOLD, RESET, BRIGHT_BLACK
except ModuleNotFoundError:
    from relay.utils import run_command
    from relay.constants import MANIFEST_FILE
    from relay.templates import MAIN_C_TEMPLATE, MAIN_H_TEMPLATE, CMAKELISTS_TEMPLATE, RELAY_TOML_TEMPLATE, CLANG_FORMAT_TEMPLATE, GITIGNORE
    from relay.helpers import find_project_root, find_vcpkg_root, get_vcpkg_triplet, get_build_dir, generate_vcpkg_json, generate_vcpkg_json_from_relay_toml, update_cmake_lists_txt
    from relay.colours import colored, GREEN, YELLOW, RED, CYAN, BOLD, RESET, BRIGHT_BLACK
except Exception:
    pass

def run_new(args):
    verbose = args.verbose
    project_name = args.project_name
    project_path = Path(project_name)

    if project_path.exists():
        print(colored(f"Error: Directory '{project_name}' already exists", RED), file=sys.stderr)
        sys.exit(1)
    print(colored(f"Creating binary (application) `{project_name}` package...", CYAN))

    try:
        project_path.mkdir()
        (project_path / "src").mkdir()
        (project_path / "include").mkdir()

        main_c_content = MAIN_C_TEMPLATE.format(project_name=project_name)
        (project_path / "src" / "main.c").write_text(main_c_content)
        verbose and print(colored("Created src/main.c", GREEN))

        include_guard = f"{project_name.upper().replace('-', '_').replace('.', '_')}_H"
        main_h_content = MAIN_H_TEMPLATE.format(include_guard=include_guard)
        (project_path / "include" / f"{project_name}.h").write_text(main_h_content)
        verbose and print(colored(f"Created include/{project_name}.h", GREEN))

        cmakelist_content = CMAKELISTS_TEMPLATE.format(project_name=project_name)
        (project_path / "CmakeLists.txt").write_text(cmakelist_content)
        verbose and print(colored("Created CmakeLists.txt", GREEN))

        (project_path / ".clang-format").write_text(CLANG_FORMAT_TEMPLATE)
        verbose and print(colored("Created .clang-format", GREEN))

        (project_path / ".gitignore").write_text(GITIGNORE)
        git_init_command = ["git", "init", str(project_path)]
        run_command(git_init_command, verbose=verbose)
        verbose and print(colored("Created .gitignore", GREEN))

        relay_toml_content = RELAY_TOML_TEMPLATE.format(project_name=project_name)
        (project_path / MANIFEST_FILE).write_text(relay_toml_content)
        verbose and print(colored(f"Created {MANIFEST_FILE}", GREEN))

        print(colored(f"\nSuccessfully created project '{project_name}'.", GREEN))
        print(f"{CYAN}Next steps:{RESET}")
        print(f"  {CYAN}cd {project_name}{RESET}")
        print(f"  {CYAN}relay add <dependency>{RESET}")
        print(f"  {CYAN}relay install{RESET}")
        print(f"  {CYAN}relay build{RESET}")

    except OSError as e:
        print(colored(f"Error creating project directories or files: {e}", RED), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(colored(f"An unexpected error occurred: {e}", RED), file=sys.stderr)
        sys.exit(1)

def run_build(args):
    verbose = args.verbose

    print(colored("Building project...", CYAN))
    project_root = find_project_root(verbose)
    vcpkg_root = find_vcpkg_root(verbose)

    vcpkg_toolchain_file = vcpkg_root / "scripts" / "buildsystems" / "vcpkg.cmake"
    if not vcpkg_toolchain_file.exists():
         vcpkg_toolchain_file = vcpkg_root / "share" / "vcpkg" / "vcpkg.cmake"
         if not vcpkg_toolchain_file.exists():
            print(colored(f"Error: vcpkg toolchain file not found at expected locations relative to VCPKG_ROOT: {vcpkg_root}", RED), file=sys.stderr)
            print(colored("Looked for:", RED),
                  colored(vcpkg_root / "scripts" / "buildsystems" / "vcpkg.cmake", RED), "and",
                  colored(vcpkg_root / "share" / "vcpkg" / "vcpkg.cmake", RED), file=sys.stderr)
            print(colored("Please ensure VCPKG_ROOT is set correctly and vcpkg is installed properly (usually requires cloning the Git repository).", RED), file=sys.stderr)
            sys.exit(1)

    triplet = get_vcpkg_triplet(args.toolchain, verbose)
    verbose and print(colored(f"Using vcpkg triplet: {triplet}", CYAN))

    build_dir = get_build_dir(project_root, triplet)
    verbose and print(colored(f"Build directory: {build_dir}", CYAN))

    generate_vcpkg_json(project_root, build_dir, verbose)

    verbose and print(colored("\n--- Configuring CMake ---", CYAN))
    cmake_configure_command = [
        "cmake",
        str(project_root),
        "-B", str(build_dir),
        f"-DCMAKE_TOOLCHAIN_FILE={vcpkg_toolchain_file}",
        f"-DVCPKG_TARGET_TRIPLET={triplet}",
    ]
    if not run_command(cmake_configure_command, verbose=verbose):
        print(colored("\nCMake configuration failed.", RED), file=sys.stderr)
        sys.exit(1)

    verbose and print(colored("\n--- Building Project ---", CYAN))
    cmake_build_command = [
        "cmake",
        "--build", str(build_dir),
    ]
    if not run_command(cmake_build_command, verbose=verbose):
        print(colored("\nProject build failed.", RED), file=sys.stderr)
        sys.exit(1)
    print(colored("Build successful!", GREEN))

def run_run(args):
    verbose = args.verbose
    verbose and print(colored("Running project...", CYAN))

    project_root = find_project_root(verbose)

    if not project_root:
        # If find_project_root fails, it sys.exit(1) so this branch won't be hit usually
        print(colored("Error: Could not determine project root.", RED), file=sys.stderr)
        sys.exit(1)

    triplet = get_vcpkg_triplet(args.toolchain, verbose)
    build_dir = get_build_dir(project_root, triplet)
    relay_toml_path = project_root / MANIFEST_FILE

    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
        project_name = relay_config.get("project", {}).get("name", project_root.name)
        executable_name = relay_config.get("project", {}).get("main_executable", project_name)
    except FileNotFoundError:
        print(colored(f"Error: Manifest file '{relay_toml_path}' not found.", RED), file=sys.stderr)
        sys.exit(1)
    except toml.TomlDecodeError as e:
        print(colored(f"Error: Could not parse '{relay_toml_path}': {e}", RED), file=sys.stderr)
        sys.exit(1)
    except Exception as e:
         print(colored(f"An unexpected error occurred while reading project name from {MANIFEST_FILE}: {e}", RED), file=sys.stderr)
         sys.exit(1)

    exe_extension = ".exe" if platform.system() == "Windows" else ""
    executable_path = build_dir / f"{executable_name}{exe_extension}"

    if not executable_path.exists():
        print(colored(f"Error: Executable not found at expected path: {executable_path}", RED), file=sys.stderr)
        print(colored("Please ensure the project built successfully and check your CMakeLists.txt for the executable target name.", YELLOW), file=sys.stderr)
        sys.exit(1)

    if not run_command(command=[str(executable_path)], cwd=build_dir, verbose=verbose):
        print(colored("\nProject run failed.", RED), file=sys.stderr)
        sys.exit(1)

def run_install_command(args):
    verbose = args.verbose
    print(colored("\nStarting dependency installation process...", CYAN))

    project_root = find_project_root(verbose)
    if not project_root:
        print(colored("Error: Could not find project root. Are you in a Relay project?", RED), file=sys.stderr)
        return

    if not generate_vcpkg_json_from_relay_toml(project_root):
        print(colored("Installation aborted: Failed to generate vcpkg.json.", RED), file=sys.stderr)
        return

    vcpkg_root = find_vcpkg_root(verbose)
    if not vcpkg_root:
        print(colored("Error: Could not find VCPKG_ROOT environment variable or vcpkg executable.", RED), file=sys.stderr)
        print(colored("Please ensure vcpkg is installed and VCPKG_ROOT is set correctly, or it's in your system's PATH.", YELLOW), file=sys.stderr)
        return

    vcpkg_executable = vcpkg_root / "vcpkg"
    if platform.system() == "Windows":
        vcpkg_executable = vcpkg_root / "vcpkg.exe"

    if not vcpkg_executable.is_file():
        print(colored(f"Error: vcpkg executable not found at '{vcpkg_executable}'.", RED), file=sys.stderr)
        return

    print(colored(f"Running vcpkg install in {project_root}...", CYAN))
    vcpkg_command = [str(vcpkg_executable), "install"]

    if hasattr(args, 'toolchain') and args.toolchain:
        vcpkg_command.append(f"--triplet={args.toolchain}")
        print(colored(f"Using toolchain: {args.toolchain}", CYAN))

    result = run_command(vcpkg_command, cwd=project_root)

    if result: # run_command returns True on success, False on failure.
        print(colored("\nDependencies installed successfully via vcpkg.", GREEN))
        print(colored("Attempting to update CMakeLists.txt automatically...", CYAN))
        if update_cmake_lists_txt(project_root):
            print(colored("CMakeLists.txt updated successfully.", GREEN))
        else:
            print(colored("Failed to automatically update CMakeLists.txt. Please check for errors.", YELLOW), file=sys.stderr)
            print(colored("You might need to manually add dependency calls to your CMakeLists.txt.", YELLOW), file=sys.stderr)
    else:
        print(colored(f"\nError: Vcpkg install failed.", RED), file=sys.stderr)
        return
    print(colored("\nDependency installation process complete.", GREEN))

def add_dependency_to_manifest(args):
    verbose = args.verbose
    dependency_name = args.dependency_name
    print(colored(f"\nAdding dependency '{BOLD}{dependency_name}{RESET}{CYAN}' to {MANIFEST_FILE}...", CYAN))

    project_root = find_project_root(verbose)
    if not project_root:
        print(colored("Error: Could not find project root. Are you in a Relay project (missing Relay.toml or vcpkg.json)?", RED), file=sys.stderr)
        return

    relay_toml_path = project_root / MANIFEST_FILE

    if not relay_toml_path.exists():
        print(colored(f"Warning: {MANIFEST_FILE} not found. Creating a minimal one.", YELLOW))
        try:
            with open(relay_toml_path, 'w') as f:
                toml.dump({"project": {"name": project_root.name, "version": "0.1.0", "type": "executable"}}, f)
        except IOError as e:
            print(colored(f"Error creating {MANIFEST_FILE}: {e}", RED), file=sys.stderr)
            return

    relay_config = {}
    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        print(colored(f"Error reading {MANIFEST_FILE}: {e}", RED), file=sys.stderr)
        return

    if "dependencies" not in relay_config:
        relay_config["dependencies"] = {}

    if dependency_name in relay_config["dependencies"]:
        print(colored(f"Dependency '{dependency_name}' already exists in {MANIFEST_FILE}.", YELLOW))
    else:
        relay_config["dependencies"][dependency_name] = "*"
        print(colored(f"Added '{dependency_name}' to {MANIFEST_FILE}.", GREEN))

    try:
        with open(relay_toml_path, 'w') as f:
            toml.dump(relay_config, f)
        print(colored(f"Successfully updated {MANIFEST_FILE}.", GREEN))
    except IOError as e:
        print(colored(f"Error writing to {MANIFEST_FILE}: {e}", RED), file=sys.stderr)
        return

    if not generate_vcpkg_json_from_relay_toml(project_root):
        print(colored("Error: Failed to generate vcpkg.json after updating Relay.toml.", RED), file=sys.stderr)
        return
    print(colored(f"\nUse 'relay install' to download and build the dependencies.", CYAN))

def run_remove_dependency(args):
    dependency_name = args.dependency_name
    verbose = args.verbose
    verbose and print(colored(f"\nAttempting to remove dependency: '{BOLD}{dependency_name}{RESET}{CYAN}'...", CYAN))

    project_root = find_project_root(verbose)
    if not project_root:
        print(colored("Error: Could not find project root. Are you in a Relay project?", RED), file=sys.stderr)
        return

    relay_toml_path = project_root / MANIFEST_FILE
    if not relay_toml_path.exists():
        print(colored(f"Error: {MANIFEST_FILE} not found at {relay_toml_path}. Cannot remove dependency.", RED), file=sys.stderr)
        return

    relay_config = {}
    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        print(colored(f"Error reading {MANIFEST_FILE}: {e}", RED), file=sys.stderr)
        return

    dependencies = relay_config.get("dependencies", {})
    if dependency_name in dependencies:
        del dependencies[dependency_name]
        relay_config["dependencies"] = dependencies
        print(colored(f"Removed '{dependency_name}' from {MANIFEST_FILE}.", GREEN))
    else:
        print(colored(f"Dependency '{dependency_name}' not found in {MANIFEST_FILE}. Nothing to remove.", YELLOW))
        return

    try:
        with open(relay_toml_path, 'w') as f:
            toml.dump(relay_config, f)
        print(colored(f"Successfully updated {MANIFEST_FILE}.", GREEN))
    except IOError as e:
        print(colored(f"Error writing to {MANIFEST_FILE}: {e}", RED), file=sys.stderr)
        return

    if not generate_vcpkg_json_from_relay_toml(project_root):
        print(colored("Error: Failed to regenerate vcpkg.json after removing dependency.", RED), file=sys.stderr)
        return

    print(colored("Updating CMakeLists.txt to reflect dependency changes...", CYAN))
    if update_cmake_lists_txt(project_root):
        print(colored("CMakeLists.txt updated successfully.", GREEN))
    else:
        print(colored("Failed to automatically update CMakeLists.txt. Please check for errors.", YELLOW), file=sys.stderr)
        print(colored("You might need to manually remove dependency calls from your CMakeLists.txt.", YELLOW), file=sys.stderr)

    print(colored("\nDependency removal process complete.", GREEN))
    print(colored(f"Run 'relay install' to re-sync your vcpkg installations, then 'relay build' to rebuild your project.", CYAN))
    print(colored(f"You might also want to run 'relay clean' before rebuilding.", CYAN))

def run_list_dependencies(args):
    verbose = args.verbose
    print(colored("\nListing Project Dependencies...", CYAN))
    print(colored("================================", CYAN))

    project_root = find_project_root(verbose)
    if not project_root:
        print(colored("Error: Could not determine project root.", RED), file=sys.stderr)
        return

    relay_toml_path = project_root / MANIFEST_FILE

    if not relay_toml_path.exists():
        print(colored(f"Error: {MANIFEST_FILE} not found at {relay_toml_path}. Is this a Relay project?", RED), file=sys.stderr)
        sys.exit(1)

    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except toml.TomlDecodeError as e:
        print(colored(f"Error: Could not parse {MANIFEST_FILE} at {relay_toml_path}: {e}", RED), file=sys.stderr)
        sys.exit(1)

    dependencies = relay_config.get("dependencies")

    if not dependencies:
        print(colored("No dependencies found in Relay.toml.", YELLOW))
    elif not isinstance(dependencies, dict):
        print(colored(f"Warning: 'dependencies' section in {MANIFEST_FILE} is not a valid dictionary.", YELLOW), file=sys.stderr)
        print(colored("Please check your Relay.toml format.", YELLOW), file=sys.stderr)
    else:
        sorted_deps = sorted(dependencies.items())
        for dep_name, dep_version in sorted_deps:
            if dep_version == "*":
                print(f"  {colored(dep_name, BOLD)} {colored('(any compatible version)', BRIGHT_BLACK)}")
            else:
                print(f"  {colored(dep_name, BOLD)} {colored(f'== {dep_version}', BRIGHT_BLACK)}")

    print(colored("\nDependency listing complete.", GREEN))

def run_clean(args):
    verbose = args.verbose
    toolchain = args.toolchain
    print(colored("Cleaning build artifacts...", CYAN))

    project_root = find_project_root(verbose)
    if not project_root:
        print(colored("Error: Could not find project root.", RED), file=sys.stderr)
        return

    triplet = get_vcpkg_triplet(toolchain, verbose)
    build_dir = get_build_dir(project_root, triplet=triplet)
    if build_dir.exists():
        print(colored(f"Removing build directory: {build_dir}", CYAN))
        import shutil
        shutil.rmtree(Path(build_dir).parent)
        print(colored("Build directory cleaned successfully.", GREEN))
    else:
        print(colored("No build directory found to clean.", YELLOW))