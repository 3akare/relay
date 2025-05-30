import sys
import subprocess

try:
    from colours import colored, RED, CYAN, BOLD
except ModuleNotFoundError:
    from relay.colours import colored, RED, CYAN, BOLD
except Exception:
    pass


def run_command(command, cwd=None, verbose=None):
    command_str = ' '.join(map(str, command))
    verbose and print(colored(f"\nRunning command: {command_str}", CYAN))
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
            verbose and print(colored("--- RELAY OUTPUT ---", BOLD))
            print(result.stdout, end="")
            verbose and print(colored("--------------------", BOLD))
        if result.stderr:
            print(colored("--- RELAY ERROR ---", BOLD), file=sys.stderr)
            print(colored(result.stderr, RED), file=sys.stderr)
            print(colored("-------------------", BOLD), file=sys.stderr)
        return True
    except FileNotFoundError:
        print(colored(f"Error: Command not found. Make sure '{command[0]}' is installed and in your PATH.", RED), file=sys.stderr)
        return False
    except subprocess.CalledProcessError as e:
        print(colored(f"Error executing command: '{' '.join(e.cmd)}' exited with code {e.returncode}", RED), file=sys.stderr)
        if e.stdout:
            print(colored("--- RELAY OUTPUT ---", BOLD), file=sys.stderr)
            print(colored(e.stdout, RED), file=sys.stderr)
            print(colored("--------------------", BOLD), file=sys.stderr)
        if e.stderr:
            print(colored("--- RELAY ERROR ---", BOLD), file=sys.stderr)
            print(colored(e.stderr, RED), file=sys.stderr)
            print(colored("-------------------", BOLD), file=sys.stderr)
        return False
    except Exception as e:
        print(colored(f"An unexpected error occurred while running command: {e}", RED), file=sys.stderr)
        return False