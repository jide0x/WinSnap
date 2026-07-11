from __future__ import annotations

import shlex
from typing import Optional, Dict, Any, List


def _parse_executable_from_cmdline(cmd: str) -> Optional[str]:
    if not cmd:
        return None
    # Handle Windows-style quoted exe first
    cmd = cmd.strip()
    if cmd.startswith('"'):
        end = cmd.find('"', 1)
        if end > 1:
            return cmd[1:end]
    # Fallback: split on whitespace using shlex (posix=False doesn't work reliably here), so do naive split
    parts = cmd.split()
    if parts:
        return parts[0]
    return None


def resolve_executable_from_process(proc: Dict[str, Any]) -> Optional[str]:
    path = proc.get("ExecutablePath")
    if path:
        return str(path)
    # Fallback to Name only (not a path)
    return None


def resolve_executable_from_service(svc: Dict[str, Any]) -> Optional[str]:
    path_name = svc.get("PathName")
    return _parse_executable_from_cmdline(path_name) if path_name else None


def resolve_executable_from_task(task: Dict[str, Any]) -> Optional[str]:
    actions = task.get("Actions")
    if isinstance(actions, list) and actions:
        # Take the first action string
        first = str(actions[0])
        return _parse_executable_from_cmdline(first)
    return None


def resolve_executable_from_autorun(autorun: Dict[str, Any]) -> Optional[str]:
    val = autorun.get("Value")
    return _parse_executable_from_cmdline(val) if val else None


def resolve_executable_from_startup_item(item: Dict[str, Any]) -> Optional[str]:
    target = item.get("TargetPath")
    return str(target) if target else None


def resolve_executable_from_firewall_rule(rule: Dict[str, Any]) -> Optional[str]:
    program = rule.get("Program")
    return str(program) if program else None
