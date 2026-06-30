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
    command = " ".join(command_parts).strip()
    if not command or command.startswith("cmdsense"):
        return
    with open("hold_cmds", "a", encoding="utf-8") as w:
        w.write(f"{command}\n")
