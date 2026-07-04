import sys


USE_COLOR = sys.stdout.isatty()


class Color:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    GREEN = "\033[32m"
    RED = "\033[31m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def color(text, code):
    if not USE_COLOR:
        return text
    return f"{code}{text}{Color.RESET}"


def success(text):
    return color(text, Color.GREEN)


def error(text):
    return color(text, Color.RED)


def warning(text):
    return color(text, Color.YELLOW)


def info(text):
    return color(text, Color.CYAN)


def bold(text):
    return color(text, Color.BOLD)
