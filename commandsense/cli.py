# entry point
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter
import subprocess
import traceback


def main():
    commands = [
        "git status",
        "git checkout main",
        "docker ps",
        "ls -la",
    ]

    trace_mode = True

    completer = WordCompleter(commands, ignore_case=True)

    text = prompt("> ", completer=completer)

    # ! 127 = command not found
    # * eventually we will have to modify the storage mechanism of commands to rank values based on usage. keep this in mind
    try:
        result = subprocess.run(text, shell=True, check=True, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").lower()
        if is_unknown_command(e.returncode, stderr):
            print(f"Error in running command [{text}]: invalid or unknown command.")
        else:
            print(f"Command failed: {text} (exit {e.returncode})")
        if trace_mode:
            print("\nTraceback:")
            print(traceback.format_exc())

            if e.stderr:
                print("\n--- stderr ---")
                print(e.stderr.strip())

    except Exception as e:
        print(f"Unexpected runtime error: {e}")

def is_unknown_command(ret_code: int, stderr: str) -> bool:
    """
    Returns a bool indicating if a ran command is known or not
    based off a return code and/or stderr print.

    Args:
        ret_code (int): exception return code
        stderr (str): stderr text
    
    Returns:
        _: True if unknown, false otherwise
    """
    return ret_code == 127 or "not found" in stderr or "not recognized" in stderr

if __name__ == "__main__":
    main()