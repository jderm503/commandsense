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

CLI_ARGS = {
    "add": "add",
    "trace_mode": "trace_mode",
    "-tm": "trace_mode",
    "num_kept_records": "num_kept_records",
    "-n": "num_kept_records",
    "time_to_keep_records": "time_to_keep_records",
    "-tk": "time_to_keep_records",
}

DEFAULT_CONFIG = {
    "trace": "False",
    "num_kept_records": "100",
    "time_to_keep_records": "14d",
}

VALID_TIME_UNITS = {"h", "d", "w", "m", "y"}


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
        make_config(user_conf_file, DEFAULT_CONFIG)

    user_conf_vars = get_user_conf_vars(user_conf_file)
    sqlite3db = SQLiteDatabase(db_file, user_conf_vars["trace"])

    try:
        if len(argv) > 1:
            cli_arg = CLI_ARGS.get(argv[1].strip().lower(), "")
            added_flag_identifier = cli_arg
            if added_flag_identifier == "add":
                add.register_command(argv[2:], sqlite3db)
            else:
                if cli_arg in (
                    "trace_mode",
                    "num_kept_records",
                    "time_to_keep_records",
                ):
                    edit_config_var(user_conf_file, user_conf_vars, cli_arg, argv[2])
                else:
                    print("(Commandsense): Unidentified command.")
        else:
            cmdsense(sqlite3db, user_conf_vars)
    finally:
        sqlite3db.close()


def cmdsense(db: SQLiteDatabase, user_conf: dict[str, bool | int | str]) -> None:
    """
    Main body of program. Is called if an additional argument isn't added to program.

    Args:
        db (SQLiteDatabase): SQLite3 Database managing command history
        trace_mode (bool): bool controlling printing of trace details

    Returns:
        _: None
    """

    trace_mode, num_kept_records, time_to_keep_records = (
        user_conf["trace"],
        user_conf["num_kept_records"],
        user_conf["time_to_keep_records"],
    )

    commands = db.load_commands_v2()

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
            print("\n")
            print(format_exc())

            if e.stderr:
                print("\n--- stderr ---")
                print(e.stderr.strip())

    except Exception as e:  # pylint: disable=broad-exception-caught
        print(f"Unexpected runtime error: {e}")
        if trace_mode:
            print("\n")
            print(format_exc())


def get_user_conf_vars(user_conf_file: Path) -> dict[str, bool | int | str]:
    """
    Retrieves & Normalizes the user config settings from their config file,
    or provides default if file not found.

    Args:
        user_conf_file (str): Path-object to the user config file location

    Returns:
        conf (dict[str, bool | int | str]): dict containing:
            - "trace" : True/False (bool)
            - "num_kept_records" : x (int)
            - "time_to_keep_records" : yt (y: int, t: str [h, d, w, m, y])
    """
    conf = dict(DEFAULT_CONFIG)
    changed_a_field = False

    try:
        with open(user_conf_file, "r", encoding="utf-8") as r:
            for line in r:
                line = line.strip().split("=")
                conf[line[0]] = line[1]

        # Convert plain strings into intended types and verify inputs are as expected
        trace = str(conf["trace"])
        if trace.lower() not in ("true", "false"):
            conf["trace"] = DEFAULT_CONFIG["trace"]
            changed_a_field = True
        conf["trace"] = trace.lower() == "true"

        try:
            conf["num_kept_records"] = int(conf["num_kept_records"])
        except ValueError:
            # Convert to default conf
            conf["num_kept_records"] = DEFAULT_CONFIG["num_kept_records"]
            changed_a_field = True

        time_keep_records = conf["time_to_keep_records"]
        if not (
            len(time_keep_records) > 1
            and time_keep_records[:-1].isdigit()
            and time_keep_records[-1] in VALID_TIME_UNITS
        ):
            conf["time_to_keep_records"] = DEFAULT_CONFIG["time_to_keep_records"]
            changed_a_field = True

    except FileNotFoundError:
        make_config(user_conf_file, conf)

    except OSError as e:
        print(f"\nError in getting user config variables: {e}")

    if changed_a_field:
        # A field was modified, update config file
        make_config(user_conf_file, conf)

    return conf


def make_config(path: Path, config: dict[str, bool | int | str]) -> None:
    """
    Create the default user config file. Used in tool initialization
    and if config file is found to be missing.

    Args:
        path (Path): path where default config should be stored
    """
    try:
        with open(path, "w", encoding="utf-8") as w:
            for k, v in config.items():
                w.write(f"{k}={v}\n")
    except OSError as e:
        print(f"Error in making config file: {e}")


def edit_config_var(
    conf_path: Path,
    existing_vars: dict[str, bool | int | str],
    config_to_change: str,
    to_be_value: str,
) -> None:
    """
    Edits the value of the passed in configuration variable name.

    Args:
        existing_vars (dict[str, bool | int | str]): current user config variables
        config_to_change (str): Name of config variable to change.
        to_be_value (str): Value which will replace existing config value
    """
    made_a_change = False
    if config_to_change == "trace":
        existing_vars[config_to_change] = to_be_value.lower() == "true"
        made_a_change = True
    elif config_to_change == "num_kept_records":
        try:
            existing_vars[config_to_change] = int(to_be_value)
            made_a_change = True
        except ValueError:
            # Leave config as is
            pass
    elif config_to_change == "time_to_keep_records":
        if (
            len(to_be_value) > 1
            and to_be_value[:-1].isdigit()
            and to_be_value[-1] in VALID_TIME_UNITS
        ):
            existing_vars[config_to_change] = to_be_value
            made_a_change = True
    if made_a_change:
        make_config(conf_path, existing_vars)


def is_unknown_command(ret_code: int, stderr: str) -> bool:
    """
    Returns a bool indicating if a ran command is known or not
    based off a return code and/or stderr print.

    Args:
        ret_code (int): exception return code
        stderr (str): stderr text

    Returns:
        _: True if unknown, False otherwise
    """
    return (
        ret_code in (127, 9009) or "not found" in stderr or "not recognized" in stderr
    )
