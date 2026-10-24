"""
ui.py - Console output helpers (colors, headers, messages).

Colors use ANSI escape codes. Windows 10+ CMD supports them once
virtual-terminal processing is switched on, which `os.system("")` does.
Colors are turned off automatically when output is not a real console
(e.g. when output is redirected to a file or during automated tests).
"""

import os
import sys

WIDTH = 50  # Width of headers and separator lines


def _supports_color():
    if os.environ.get("NO_COLOR"):
        return False
    if not sys.stdout.isatty():
        return False
    if os.name == "nt":
        os.system("")  # Enables ANSI escape codes in Windows CMD
    return True


USE_COLOR = _supports_color()


def _code(value):
    return value if USE_COLOR else ""


RESET = _code("\033[0m")
BOLD = _code("\033[1m")
RED = _code("\033[91m")
GREEN = _code("\033[92m")
YELLOW = _code("\033[93m")
BLUE = _code("\033[94m")
CYAN = _code("\033[96m")
GRAY = _code("\033[90m")


def color(text, code):
    """Wrap text in a color code."""
    return f"{code}{text}{RESET}"


def line(char="=", width=WIDTH):
    print(char * width)


def header(title):
    """Print a boxed title, e.g. the SYSTEM INFORMATION header."""
    line()
    print(color(title.center(WIDTH), BOLD + YELLOW))
    line()


def success(message):
    print(color(message, GREEN))


def error(message):
    print(color(f"Error: {message}", RED))


def warning(message):
    print(color(message, YELLOW))


def info(message):
    print(color(message, CYAN))
