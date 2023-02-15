import argparse
import sys

from shared.lib.dataclasses import all_exercises
from shared.commands.base import get_language_code, get_command_name
from shared.commands import COMMANDS as SHARED_COMMANDS
from japanese.commands import COMMANDS as JAPANESE_COMMANDS

LANGUAGE_COMMANDS = {
    "jpn": JAPANESE_COMMANDS,
    "ind": {},
    "fin": {},
}

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Please provide a language and a command.")
        sys.exit(1)

    language_code = get_language_code()
    if language_code not in LANGUAGE_COMMANDS:
        print(f"Unknown language. Choose from: {', '.join(LANGUAGE_COMMANDS)}")
        sys.exit(1)

    dispatch_table = {
        **SHARED_COMMANDS,
        **LANGUAGE_COMMANDS[language_code],
    }

    command_name = get_command_name()
    if command_name not in dispatch_table:
        print(f"Unknown command. Choose from: {', '.join(dispatch_table)}")
        sys.exit(1)
    command = dispatch_table[command_name]

    command(
        all_exercises(f"{language_code}-eng"),
        argparse.ArgumentParser(),
        sys.argv[3:],
    )
