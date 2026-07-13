"""
db.py
This file holds the Database class which is in charge
of all logic for the sqlite database which stores
the commands the user types in normal terminal usage.
"""

from time import time
from pathlib import Path
from traceback import format_exc
import sqlite3


class SQLiteDatabase:
    """
    SQLiteDatabase
    This class is in charge of handing sqlite operations.
    """

    def __init__(self, db_path: Path, trace_mode: bool) -> None:
        # ! there could be a chance we can remove this later. isnt accessed anywhere currently
        self.db_path: Path = db_path

        self.trace_mode = trace_mode
        self.connection: sqlite3.Connection = sqlite3.connect(db_path)
        self.create_table_if_not_present()

    def __del__(self) -> None:
        """Auto-call close as a last ditch effort if manual call is removed"""
        self.close()

    def close(self) -> None:
        """
        Closes the active sqlite3 database.

        Returns:
            _: None
        """
        if self.connection is not None:
            self.connection.close()
            self.connection = None

    def register_command(self, command: str) -> None:
        """
        This function registers a command in the SQLite3 database.

        Args:
            command (str): The string command

        Returns:
            _: None
        """
        date = int(time())
        try:
            self.connection.execute(
                """
                INSERT INTO cmdsense_records (command, uses, last_use_date)
                VALUES (?, 1, ?)
                ON CONFLICT(command)
                DO UPDATE SET
                    uses = uses + 1,
                    last_use_date = excluded.last_use_date
                """,
                (command, date),
            )
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"(Commandsense): Database error: {e}")
            if self.trace_mode:
                print(format_exc())

    def create_table_if_not_present(self):
        """
        This function creates the table in the sqlite3 database if it is not present
        (such as when program run for the first time).

        Returns:
            _: None
        """
        try:
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS cmdsense_records (
                    command TEXT PRIMARY KEY,
                    uses INTEGER NOT NULL DEFAULT 1,
                    last_use_date INTEGER
                )
                """)
            self.connection.commit()
        except sqlite3.Error as e:
            print(f"(Commandsense): Database error: {e}")
            if self.trace_mode:
                print(format_exc())

    def load_commands_v2(self) -> list[str]:
        """
        This function obtains the commands in the tool's sqlite database
        and returns them as a list.

        Returns:
            cmds (list[str]): a list of commands from the sqlite3 database.
        """
        cmds: list[str] = []
        try:
            for row in self.connection.execute(
                "SELECT * FROM cmdsense_records ORDER BY uses DESC"
            ):
                cmds.append(row[0])
        except sqlite3.Error as e:
            print(f"(Commandsense): Database error: {e}")
            if self.trace_mode:
                print(format_exc())
        return cmds
