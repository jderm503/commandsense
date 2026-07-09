"""
db.py
This file holds the Database class which is in charge
of all logic for the sqlite database which stores
the commands the user types in normal terminal usage.
"""

from time import time
from pathlib import Path
import sqlite3


class SQLiteDatabase:
    """
    SQLiteDatabase
    This class is in charge of handing sqlite operations.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path: Path = db_path
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
        self.connection.execute("""
            INSERT INTO cmdsense_records (command, uses, last_use_date)
            VALUES (?, 1, ?)
            ON CONFLICT(command)
            DO UPDATE SET
                uses = uses + 1,
                last_use_date = excluded.last_use_date
            """, (command, date))
        self.connection.commit()


    def create_table_if_not_present(self):
        """
        This function creates the table in the sqlite3 database if it is not present
        (such as when program run for the first time).

        Returns:
            _: None
        """
        self.connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cmdsense_records (
                command TEXT PRIMARY KEY,
                uses INTEGER NOT NULL DEFAULT 1,
                last_use_date INTEGER
            )
            """
        )
        self.connection.commit()


    def load_commands_v1(self) -> list[str]:
        """temp function, loading commands from file. will later switch to an sqlite model.
        when i get to that point, look into this library for storing location:
        platformdirs: https://pypi.org/project/platformdirs/
        also note that at that point i wont need a load commands function, since i will direct
        hook into sqlite. maybe just a helper function for grabbing requested stuff. will need a
        function for computing frequencies too"""
        cmds: list[str] = []
        with open("hold_cmds", "r", encoding="utf-8") as r:
            for line in r:
                cmds.append(line.strip())
        return cmds
