from pathlib import Path
from utils import run_command
from constants import MANIFEST_FILE
from templates import MAIN_C_TEMPLATE, MAIN_H_TEMPLATE, CMAKELISTS_TEMPLATE, RELAY_TOML_TEMPLATE
from helpers import find_project_root, find_vcpkg_root, get_vcpkg_triplet, get_build_dir, generate_vcpkg_json
import sys


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
    print("run")