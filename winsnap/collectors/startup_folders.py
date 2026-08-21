import os
from datetime import datetime, timezone

# ---------------------------------------------------------------------------
# Native startup folder collection: enumerate the user and machine Startup
# folders directly, resolving .lnk shortcuts by parsing the Shell Link binary
# format (no PowerShell / WScript.Shell COM round-trip).
# ---------------------------------------------------------------------------

_HAS_LINK_TARGET_ID_LIST = 0x00000001
_HAS_LINK_INFO = 0x00000002
_HAS_NAME = 0x00000004
_HAS_RELATIVE_PATH = 0x00000008
_HAS_WORKING_DIR = 0x00000010
_HAS_ARGUMENTS = 0x00000020
_HAS_ICON_LOCATION = 0x00000040
_IS_UNICODE = 0x00000080


def _parse_lnk(path):
    """Return (target_path, arguments, working_directory) from a .lnk file.

    Missing fields are returned as empty strings to match WScript.Shell.
    """
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None, None, None

    if len(data) < 0x4C:
        return None, None, None

    link_flags = int.from_bytes(data[0x14:0x18], "little")

    pos = 0x4C

    if link_flags & _HAS_LINK_TARGET_ID_LIST:
        if pos + 2 > len(data):
            return None, None, None
        id_list_size = int.from_bytes(data[pos:pos + 2], "little")
        pos += 2 + id_list_size

    target_path = ""
    if link_flags & _HAS_LINK_INFO:
        link_info_start = pos
        if pos + 0x1C > len(data):
            return None, None, None
        link_info_size = int.from_bytes(data[pos:pos + 4], "little")
        header_size = int.from_bytes(data[pos + 4:pos + 8], "little")
        local_base_path_offset = int.from_bytes(data[pos + 0x10:pos + 0x14], "little")

        if header_size >= 0x24:
            unicode_offset = int.from_bytes(data[pos + 0x18:pos + 0x1C], "little")
        else:
            unicode_offset = 0

        if unicode_offset:
            target_path = _read_nt_string(data, link_info_start + unicode_offset) or ""
        elif local_base_path_offset:
            target_path = _read_nt_string(data, link_info_start + local_base_path_offset) or ""

        pos += link_info_size

    strings = {}
    for flag, key in (
        (_HAS_NAME, "name"),
        (_HAS_RELATIVE_PATH, "relative_path"),
        (_HAS_WORKING_DIR, "working_dir"),
        (_HAS_ARGUMENTS, "arguments"),
        (_HAS_ICON_LOCATION, "icon_location"),
    ):
        if link_flags & flag:
            if pos + 2 > len(data):
                break
            count = int.from_bytes(data[pos:pos + 2], "little")
            pos += 2
            char_size = 2 if (link_flags & _IS_UNICODE) else 1
            raw = data[pos:pos + count * char_size]
            pos += count * char_size
            strings[key] = raw.decode("utf-16-le" if char_size == 2 else "cp1252", errors="replace")

    arguments = strings.get("arguments", "")
    working_directory = strings.get("working_dir", "")
    return target_path, arguments, working_directory


def _read_nt_string(data, offset):
    if offset <= 0 or offset >= len(data):
        return None
    end = data.find(b"\x00", offset)
    if end == -1:
        end = len(data)
    return data[offset:end].decode("cp1252", errors="replace")


def _format_o(mtime_ns):
    ticks = mtime_ns // 100
    dt = datetime.fromtimestamp(ticks / 10_000_000, timezone.utc)
    fraction = f"{ticks % 10_000_000:07d}"
    return dt.strftime("%Y-%m-%dT%H:%M:%S") + "." + fraction + "Z"


def collect_startup_folders():
    folders = [
        ("User", os.path.join(os.environ.get("APPDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")),
        ("Machine", os.path.join(os.environ.get("PROGRAMDATA", ""), r"Microsoft\Windows\Start Menu\Programs\Startup")),
    ]

    results = []
    for scope, folder_path in folders:
        try:
            entries = list(os.scandir(folder_path))
        except OSError:
            continue
        for entry in entries:
            if entry.name.lower() == "desktop.ini":
                continue
            try:
                st = entry.stat()
            except OSError:
                continue
            extension = os.path.splitext(entry.name)[1]
            target_path = arguments = working_directory = None
            if extension.lower() == ".lnk":
                target_path, arguments, working_directory = _parse_lnk(entry.path)
            results.append({
                "Scope": scope,
                "FolderPath": folder_path,
                "Name": entry.name,
                "FullName": entry.path,
                "Extension": extension,
                "Length": st.st_size,
                "LastWriteTimeUtc": _format_o(st.st_mtime_ns),
                "TargetPath": target_path,
                "Arguments": arguments,
                "WorkingDirectory": working_directory,
            })

    return results
