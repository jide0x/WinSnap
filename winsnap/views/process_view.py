import ctypes
import shutil
import shlex
import textwrap

from winsnap.views.ui import bold


FIELD_LABEL_WIDTH = 12
ARG_LABEL_WIDTH = 18


def terminal_width():
    return min(shutil.get_terminal_size(fallback=(100, 20)).columns, 120)


def print_process(process, marker=""):
    name = process.get("Name") or "Unknown"
    print(bold(name if not marker else f"{marker} {name}"))
    print()

    print_field("PID", process.get("ProcessId"))
    print_field("Parent PID", process.get("ParentProcessId"))
    print_field("Path", process.get("ExecutablePath") or "Unknown")

    command_line = process.get("CommandLine") or "Unknown"
    print_command(command_line)


def parse_command_line(command_line):
    if not command_line or command_line == "Unknown":
        return []

    try:
        argc = ctypes.c_int()
        command_line_to_argv = ctypes.windll.shell32.CommandLineToArgvW
        command_line_to_argv.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_int)]
        command_line_to_argv.restype = ctypes.POINTER(ctypes.c_wchar_p)

        argv = command_line_to_argv(command_line, ctypes.byref(argc))
        if not argv:
            return []

        parts = [clean_argument(argv[i]) for i in range(argc.value)]
        ctypes.windll.kernel32.LocalFree(argv)
        return parts
    except Exception:
        try:
            return [clean_argument(part) for part in shlex.split(command_line, posix=False)]
        except ValueError:
            return []


def clean_argument(argument):
    if len(argument) >= 2 and argument[0] == argument[-1] == '"':
        return argument[1:-1]
    return argument


def print_command(command_line):
    parts = parse_command_line(command_line)
    if not parts:
        print_field("Command", command_line)
        return

    print()
    print(bold(" Command"))
    print_field("  Exe", parts[0])

    args = parts[1:]
    if not args:
        return

    print("  Args")
    for label, value in command_arguments(args):
        print_argument(label, value)


def command_arguments(args):
    parsed = []
    index = 0

    while index < len(args):
        arg = args[index]

        if arg == "-" and index + 1 < len(args):
            parsed.append(("Argument", " ".join(args[index:])))
            break

        if is_flag(arg) and "=" in arg:
            label, value = arg.split("=", 1)
            parsed.append((label, value))
            index += 1
            continue

        if is_flag(arg) and ":" in arg and index + 1 >= len(args):
            label, value = arg.split(":", 1)
            parsed.append((label, value))
            index += 1
            continue

        if is_flag(arg) and index + 1 < len(args) and not is_flag(args[index + 1]):
            parsed.append((arg, args[index + 1]))
            index += 2
            continue

        parsed.append((arg, None))
        index += 1

    return parsed


def is_flag(argument):
    return argument not in {"-", "--"} and argument.startswith(("-", "/"))


def print_argument(label, value):
    if value is None:
        print(f"    {label}")
        return

    label_text = f"    {label:<{ARG_LABEL_WIDTH}} "
    indent = " " * len(label_text)
    width = max(40, terminal_width() - len(label_text))
    lines = wrap_value(value, width)

    print(f"{label_text}{lines[0]}")
    for line in lines[1:]:
        print(f"{indent}{line}")


def print_field(label, value):
    label_text = f" {label:<{FIELD_LABEL_WIDTH}} "
    indent = " " * len(label_text)
    width = max(40, terminal_width() - len(label_text))
    lines = wrap_value(value, width)

    print(f"{label_text}{lines[0]}")
    for line in lines[1:]:
        print(f"{indent}{line}")


def wrap_value(value, width):
    return textwrap.wrap(
        str(value),
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
    ) or ["Unknown"]
