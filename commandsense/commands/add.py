"""
add.py
This module is responsible for handling the operation of
parsing a user's command and adding it to the program's
sqlite3 database.
"""

from commandsense.db import SQLiteDatabase


def register_command(command_parts: list[str], db: SQLiteDatabase) -> None:
    """
    Appends to datastore the command used so that the tool can
    track usage rate of commands and suggest accordingly.

    Args:
        command(str): The command entered in the terminal by the user

    Returns:
        _: None
    """
    command: str = " ".join(command_parts).strip()
    if not command or command.startswith("cmdsense"):
        return
    with open("hold_cmds", "a", encoding="utf-8") as w:
        w.write(f"{command}\n")
    db.register_command(command)


def register_command_v2(command_parts: list[str], db: SQLiteDatabase) -> None:
    """
    Appends to datastore the command used so that the tool can
    track usage rate of commands and suggest accordingly.

    Args:
        command(str): The command entered in the terminal by the user

    Returns:
        _: None
    """
    command: str = " ".join(command_parts).strip()
    if not command or command.startswith("cmdsense"):
        return
    db.register_command(command)
