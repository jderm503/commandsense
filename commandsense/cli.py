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
from commandsense.commands import add
from commandsense.db import SQLiteDatabase


def main():
    """
    Main function handles all entries into program.
    If command `cmdsense add ...` is called, branches to
    that logic, else it acts as program was ran normally.
    """
    app_data_path = PlatformDirs("commandsense")
    data_dir = app_data_path.user_data_path
    data_dir.mkdir(parents=True, exist_ok=True)

    db_file = data_dir / "commandsense.db"

    user_conf_dir = app_data_path.user_config_path
    user_conf_dir.mkdir(parents=True, exist_ok=True)
    user_conf_file = user_conf_dir / "commandsense.conf"
    if not user_conf_file.exists():
        with open(user_conf_file, 'w', encoding='utf-8') as w:
            w.write("trace=False\n")

    sqlite3db = SQLiteDatabase(db_file)

    try:
        if len(argv) > 1 and argv[1] == "add":
            add.register_command(argv[2:], sqlite3db)
        else:
            if len(argv) > 1:
                print("(Commandsense): Unidentified command.")
            else:
                cmdsense(sqlite3db, _retrieve_trace_mode(user_conf_file))
    finally:
        sqlite3db.close()


def cmdsense(db: SQLiteDatabase, trace_mode: bool) -> None:
    """
    Main body of program. Is called if the 'add' argument isn't added to program.

    Args:
        db (SQLiteDatabase): SQLite3 Database managing command history
        trace_mode (bool): bool controlling printing of trace details

    Returns:
        _: None
    """

    commands = list(set(db.load_commands_v1()))

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

def _retrieve_trace_mode(user_conf_file: Path) -> bool:
    """ Grab the trace mode from user conf file """
    line = ""
    with open(user_conf_file, 'r', encoding='utf-8') as r:
        line = r.readline()
    return True if line.split('=')[1].strip() == "True" else False


# TODO:
    # Add an ability with a flag or something to change the trace_mode
    # Add items to the user conf as i think of conf'able items