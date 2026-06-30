"""
cli.py
This file is the main driver of the cmdsense application.
"""

# std library
import subprocess
from sys import argv
from pathlib import Path
from traceback import format_exc
from platformdirs import PlatformDirs

# third-party
from prompt_toolkit import prompt
from prompt_toolkit.completion import WordCompleter

# first-party
from commandsense.db import SQLDatabase


def main():
    """
    Main function handles all entries into program.
    If command `cmdsense add ...` is called, branches to
    that logic, else it acts as program was ran normally.
    """
    if len(argv) > 1 and argv[1] == "add":
        command = " ".join(argv[2:]).strip()
        if not command or command.startswith("cmdsense"):
            return
        save_command(command)
    else:
        if len(argv) > 1:
            print("(Commandsense): Unidentified command.")
        else:
            cmdsense()


def cmdsense() -> None:
    """
    Main body of program. Is called if the 'add' argument isn't added to program.

    Args:
        _: None

    Returns:
        _: None
    """

    app_data_path = PlatformDirs("commandsense")

    db_init = SQLDatabase(app_data_path.user_data_path)

    commands = list(set(db_init.load_commands_v1()))

    trace_mode = True

    completer = WordCompleter(words=commands, ignore_case=True, match_middle=True)

    text = prompt(message="> ", completer=completer, complete_while_typing=True)

    # ! 127 = command not found
    # ! fun note - using -e on the pipx install means editable,
    # ! so i dont have to reinstall after i make a code change
    # * eventually we will have to modify the storage mechanism of commands to rank
    # * values based on usage. keep this in mind
    try:
        subprocess.run(text, shell=True, check=True, stderr=subprocess.PIPE, text=True)
    except subprocess.CalledProcessError as e:
        stderr = (e.stderr or "").lower()
        if is_unknown_command(e.returncode, stderr):
            print(f"Error in running command [{text}]: invalid or unknown command.")
        else:
            print(f"Command failed: {text} (exit {e.returncode})")
        if trace_mode:
            print("\nTraceback:")
            print(format_exc())

            if e.stderr:
                print("\n--- stderr ---")
                print(e.stderr.strip())

    except Exception as e:
        print(f"Unexpected runtime error: {e}")


def save_command(command: str) -> None:
    """
    Appends to datastore the command used so that the tool can
    track usage rate of commands and suggest accordingly.

    Args:
        command(str): The command entered in the terminal by the user

    Returns:
        _: None
    """
    with open("hold_cmds", "a", encoding="utf-8") as w:
        w.write(f"{command}\n")


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


# Note:
# when ready for full release, make sure i do something like:
# function __cmdsense_hook() {
#     cmdsense add "$(history 1)"
# },
# and then plug it into $PROMPT_COMMAND:
# PROMPT_COMMAND = "$PROMPT_COMMAND; __cmdsense_hook"
