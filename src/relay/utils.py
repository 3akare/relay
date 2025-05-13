import sys
import subprocess

def run_command(command, cwd=None, verbose=None):
    command_str = ' '.join(map(str, command))
    verbose and print(f"\nRunning command: {command_str}")
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        if result.stdout:
            verbose and print("--- RELAY OUTPUT ---")
            print(result.stdout, end="")
            verbose and print("--------------------")
        if result.stderr:
            print("--- RELAY ERROR ---", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            print("-------------------", file=sys.stderr)
        return True
    except FileNotFoundError:
        print(f"Error: Command not found. Make sure '{command[0]}' is installed and in your PATH.", file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(f"Error executing command: '{' '.join(e.cmd)}' exited with code {e.returncode}", file=sys.stderr)
        if e.stdout:
            print("--- RELAY OUTPUT ---", file=sys.stderr)
            print(e.stdout, file=sys.stderr)
            print("--------------------", file=sys.stderr)
        if e.stderr:
            print("--- RELAY ERROR ---", file=sys.stderr)
            print(e.stderr, file=sys.stderr)
            print("-------------------", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred while running command: {e}", file=sys.stderr)
        return False