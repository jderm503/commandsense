"""
db.py
This file holds the Database class which is in charge
of all logic for the sqlite database which stores
the commands the user types in normal terminal usage.
"""

from pathlib import Path
import sqlite3


class SQLiteDatabase:
    """
    SQLiteDatabase
    This class is in charge of handing sqlite operations.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.connection = sqlite3.connect(db_path)
        self.cursor = self.connection.cursor()


    def load_commands_v1(self) -> list[str]:
        """temp function, loading commands from file. will later switch to an sqlite model.
        when i get to that point, look into this library for storing location:
        platformdirs: https://pypi.org/project/platformdirs/
        also note that at that point i wont need a load commands function, since i will direct
        hook into sqlite. maybe just a helper function for grabbing requested stuff. will need a
        function for computing frequencies too"""
        cmds = []
        with open("hold_cmds", "r", encoding="utf-8") as r:
            for line in r:
                cmds.append(line.strip())
        return cmds
