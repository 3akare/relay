import sys
import toml
import json
import platform
from pathlib import Path

try:
    from utils import run_command
    from constants import MANIFEST_FILE, RELAY_VERSION, VCPKG_MANIFEST_FILE
    from templates import MAIN_C_TEMPLATE, MAIN_H_TEMPLATE, CMAKELISTS_TEMPLATE, RELAY_TOML_TEMPLATE, CLANG_FORMAT_TEMPLATE, GITIGNORE
    from helpers import find_project_root, find_vcpkg_root, get_vcpkg_triplet, get_build_dir, generate_vcpkg_json, generate_vcpkg_json_from_relay_toml
except ModuleNotFoundError:
    from relay.utils import run_command
    from relay.constants import MANIFEST_FILE, RELAY_VERSION, VCPKG_MANIFEST_FILE
    from relay.templates import MAIN_C_TEMPLATE, MAIN_H_TEMPLATE, CMAKELISTS_TEMPLATE, RELAY_TOML_TEMPLATE, CLANG_FORMAT_TEMPLATE, GITIGNORE
    from relay.helpers import find_project_root, find_vcpkg_root, get_vcpkg_triplet, get_build_dir, generate_vcpkg_json, generate_vcpkg_json_from_relay_toml
except Exception:
    pass

def run_new(args):
    verbose = args.verbose
    project_name = args.project_name
    project_path = Path(project_name)

    # Ensure directory doesn't exist
    if (project_path.exists()):
        print(f"Error: Directory '{project_name}' already exists", file=sys.stderr)
        sys.exit(1)
    print(f"Creating binary (application) `{project_name}` package...")

    # Create sub-directories
    try:
        project_path.mkdir()
        (project_path / "src").mkdir()
        (project_path / "include").mkdir()

        # main.c
        main_c_content = MAIN_C_TEMPLATE.format(project_name=project_name)
        (project_path / "src" / "main.c").write_text(main_c_content)
        verbose and print("Created src/main.c")

        # main.h
        include_guard = f"{project_name.upper().replace('-', '_').replace('.', '_')}_H"
        main_h_content = MAIN_H_TEMPLATE.format(include_guard=include_guard)
        (project_path / "include" / f"{project_name}.h").write_text(main_h_content)
        verbose and print(f"Created include/{project_name}.h")

        # CmakeLists.txt
        cmakelist_content = CMAKELISTS_TEMPLATE.format(project_name=project_name)
        (project_path / "CmakeLists.txt").write_text(cmakelist_content)
        verbose and print(f"Created CmakeLists.txt")

        # .clang-format
        (project_path / ".clang-format").write_text(CLANG_FORMAT_TEMPLATE)
        verbose and print(f"Created .clang-format")

        # .gitignore
        (project_path / ".gitignore").write_text(GITIGNORE)
        git_init_command = ["git", "init", str(project_path)]
        run_command(git_init_command, verbose=verbose)
        verbose and print(f"Created .gitignore")
        
        # Relay.toml (mainfest file)
        relay_toml_content = RELAY_TOML_TEMPLATE.format(project_name=project_name)
        (project_path / MANIFEST_FILE).write_text(relay_toml_content)
        verbose and print(f"Created {MANIFEST_FILE}")


        print(f"\nSuccessfully created project '{project_name}'.")
        print(f"Next steps:")
        print(f"  cd {project_name}")
        print(f"  # Add dependencies to {MANIFEST_FILE} (e.g., under [dependencies])")
        print(f"  # Update CMakeLists.txt to find and link added dependencies")
        print(f"  # Set VCPKG_ROOT environment variable to your vcpkg directory")
        print(f"  relay [--toolchain <triplet>] build")

    except OSError as e:
        print(f"Error creating project directories or files: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occured: {e}")
        sys.exit(1)

def run_build(args):
    verbose = args.verbose
    toolchain = args.toolchain

    print(f"Building project...")
    project_root = find_project_root(verbose)
    vcpkg_root = find_vcpkg_root(verbose)

    vcpkg_toolchain_file = vcpkg_root / "scripts" / "buildsystems" / "vcpkg.cmake"
    if not vcpkg_toolchain_file.exists():
         vcpkg_toolchain_file = vcpkg_root / "share" / "vcpkg" / "vcpkg.cmake" # Check Homebrew path
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

    # CMake configure
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

    # CMake build
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
    verbose and print(f"Running project...")

    project_root = find_project_root(verbose)
    
    # build binary
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

    # file extension
    exe_extension = ".exe" if platform.system() == "Windows" else ""
    executable_path = build_dir / f"{executable_name}{exe_extension}"

    # Check if the executable exists
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

    if result == True:
        print("\nDependencies installed successfully via vcpkg.")
    else:
        print(f"\nError: Vcpkg install failed with exit code {result.returncode}.")
        print("Vcpkg output:")
        print(result.stdout)
        if result.stderr:
            print(result.stderr)
        return 
    # TODO: Update Cmakefile.txt... Be like say dev go dey do am by themselves
    print("\nDependency installation process complete.")

def add_dependency_to_manifest(args):
    verbose = args.verbose
    dependency_name = args.dependency_name
    dependency_version = None # Will be None if not specified

    print(f"\nAdding dependency '{dependency_name}' to {MANIFEST_FILE}...")

    project_root = find_project_root(verbose)
    if not project_root:
        print("Error: Could not find project root. Are you in a Relay project (missing Relay.toml or vcpkg.json)?")
        return

    relay_toml_path = project_root / MANIFEST_FILE

    # Ensure Relay.toml exists, or create a minimal one if not
    if not relay_toml_path.exists():
        print(f"Warning: {MANIFEST_FILE} not found. Creating a minimal one.")
        try:
            with open(relay_toml_path, 'w') as f:
                toml.dump({"project": {"name": project_root.name, "version": "0.1.0", "type": "executable"}}, f)
        except IOError as e:
            print(f"Error creating {MANIFEST_FILE}: {e}")
            return

    # Read Relay.toml
    relay_config = {}
    try:
        with open(relay_toml_path, 'r') as f:
            relay_config = toml.load(f)
    except (FileNotFoundError, toml.TomlDecodeError) as e:
        print(f"Error reading {MANIFEST_FILE}: {e}")
        return

    # Add dependency to [dependencies] table
    if "dependencies" not in relay_config:
        relay_config["dependencies"] = {}

    if dependency_name in relay_config["dependencies"]:
        print(f"Dependency '{dependency_name}' already exists in {MANIFEST_FILE}.")
    else:
        # For simplicity, we add "*" for any compatible version from vcpkg
        relay_config["dependencies"][dependency_name] = "*"
        print(f"Added '{dependency_name}' to {MANIFEST_FILE}.")

    # Write Relay.toml
    try:
        with open(relay_toml_path, 'w') as f:
            toml.dump(relay_config, f)
        print(f"Successfully updated {MANIFEST_FILE}.")
    except IOError as e:
        print(f"Error writing to {MANIFEST_FILE}: {e}")
        return

    # Now, generate vcpkg.json based on the updated Relay.toml
    if not generate_vcpkg_json_from_relay_toml(project_root):
        print("Error: Failed to generate vcpkg.json after updating Relay.toml.")
        return
    print(f"\nUse 'relay install' to download and build the dependencies.")

def run_remove(args):
    print(f"Deleting dependency: {args.dependency_name}")

def run_update(args):
     print("Updating dependencies...")

def run_clean(args):
    verbose = args.verbose
    toolchain = args.toolchain
    print("Cleaning build artifacts...")
    # Remove the 'build' directory at the project root
    project_root = find_project_root(verbose)
    triplet = get_vcpkg_triplet(toolchain, verbose)
    build_dir = get_build_dir(project_root, triplet=triplet)
    if build_dir.exists():
        print(f"Removing build directory: {build_dir}")
        import shutil
        shutil.rmtree(Path(build_dir).parent)
    else:
        print("No build directory found to clean.")
