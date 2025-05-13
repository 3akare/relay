from pathlib import Path
from templates import MAIN_C_TEMPLATE, MAIN_H_TEMPLATE, CMAKELISTS_TEMPLATE, RELAY_TOML_TEMPLATE
import sys

# consts
MANIFEST_FILE = "Relay.toml"

def run_new(args):
    project_name = args.project_name
    project_path = Path(project_name)

    # Ensure directory doesn't exist
    if (project_path.exists()):
        print(f"Error: Directory '{project_name}' already exists", file=sys.stderr)
        sys.exit(1)
    print(f"Creating binary (application) `{project_name}` package")

    # Create sub-directories
    try:
        project_path.mkdir()
        (project_path / "src").mkdir()
        (project_path / "include").mkdir()

        # main.c
        main_c_content = MAIN_C_TEMPLATE.format(project_name=project_name)
        (project_path / "src" / "main.c").write_text(main_c_content)
        print("Created src/main.c")

        # main.h
        include_guard = f"{project_name.upper().replace('-', '_').replace('.', '_')}_H"
        main_h_content = MAIN_H_TEMPLATE.format(include_guard=include_guard)
        (project_path / "include" / f"{project_name}.h").write_text(main_h_content)
        print(f"Created include/{project_name}.h")

        # CmakeLists.txt
        cmakelist_content = CMAKELISTS_TEMPLATE.format(project_name=project_name)
        (project_path / "CmakeLists.txt").write_text(cmakelist_content)
        print(f"Created CmakeLists.txt")

        # Relay.toml (mainfest file)
        relay_toml_content = RELAY_TOML_TEMPLATE.format(project_name=project_name)
        (project_path / MANIFEST_FILE).write_text(relay_toml_content)
        print(f"Created {MANIFEST_FILE}")

        print(f"\nSuccessfully created project '{project_name}'.")
        print(f"Next steps:")
        print(f"  cd {project_name}")
        print(f"  # Add dependencies to {MANIFEST_FILE} (e.g., under [dependencies])")
        print(f"  # Update CMakeLists.txt to find and link added dependencies")
        print(f"  # Set VCPKG_ROOT environment variable to your vcpkg directory")
        print(f"  relay build [--toolchain <triplet>]")

    except OSError as e:
        print(f"Error creating project directories or files: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"An unexpected error occured: {e}")
        sys.exit(1)

def run_build(args):
    print("build")

def run_run(args):
    print("run")