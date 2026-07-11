from __future__ import annotations

from typing import Any, Dict, List, Tuple

TRUSTED_PUBLISHERS = {
    "Microsoft Corporation",
    "Microsoft Windows",
}


def apply_filters(before: Dict[str, Any], after: Dict[str, Any], diff: Dict[str, Any], mode: str = "default") -> Dict[str, Any]:
    """
    Return a filtered diff for presentation. Never removes underlying evidence.

    Strategy (phase 1-2):
    - In default mode, reduce routine process churn by pairing symmetric added/removed instances per executable.
    - In all mode, return the original diff unchanged.

    Evidence safety rule:
    - Store filtered items under a private "_filtered" key per artifact/section so they remain available.
    """
    if mode == "all":
        return diff

    result = {k: v for k, v in diff.items()}

    # Initialize container for filtered counts without disrupting existing views
    filtered_meta: Dict[str, Any] = {}

    # Processes: pair symmetric added/removed instances for the same executable label
    if "processes" in diff:
        added: List[Dict[str, Any]] = list(diff["processes"].get("added", []))
        removed: List[Dict[str, Any]] = list(diff["processes"].get("removed", []))
        vis_added, fil_added, vis_removed, fil_removed = _reduce_process_churn(added, removed)

        # Write visible lists back
        proc_section = dict(diff["processes"])  # shallow copy
        proc_section["_filtered"] = {
            "added": fil_added,
            "removed": fil_removed,
            "reason": "process_count_churn",
        }
        proc_section["added"] = vis_added
        proc_section["removed"] = vis_removed
        result["processes"] = proc_section
        filtered_meta["processes"] = {
            "filtered_added": len(fil_added),
            "filtered_removed": len(fil_removed),
        }

    # Ephemeral listeners: de-emphasize likely low-interest localhost listeners (not bind-all, no service names,
    # no paired new inbound firewall rule)
    if "network_listeners" in diff:
        _deprioritize_ephemeral_listeners(before, after, diff, result, filtered_meta)

    # Trusted signed Microsoft binary changes: only FileHash changed and trusted signed binary from expected location
    _deprioritize_trusted_binary_changes(diff, result, filtered_meta)

    # Attach meta for potential future use (e.g., printing filtered summary)
    result.setdefault("_filtering", filtered_meta)
    return result


def _executable_key(process: Dict[str, Any]) -> Tuple[str, str]:
    name = (process.get("Name") or "").lower()
    path = (process.get("ExecutablePath") or "").lower()
    return (name, path)


def _reduce_process_churn(added: List[Dict[str, Any]], removed: List[Dict[str, Any]]):
    """
    Pair off symmetric added/removed instances for the same (Name, ExecutablePath) and treat them as filtered churn.
    Return visible_added, filtered_added, visible_removed, filtered_removed.
    """
    from collections import defaultdict, deque

    added_by_key: Dict[Tuple[str, str], deque] = defaultdict(deque)
    removed_by_key: Dict[Tuple[str, str], deque] = defaultdict(deque)

    for p in added:
        added_by_key[_executable_key(p)].append(p)
    for p in removed:
        removed_by_key[_executable_key(p)].append(p)

    vis_added: List[Dict[str, Any]] = []
    fil_added: List[Dict[str, Any]] = []
    vis_removed: List[Dict[str, Any]] = []
    fil_removed: List[Dict[str, Any]] = []

    # For each key, pair min(count_added, count_removed) as churn
    keys = set(added_by_key.keys()) | set(removed_by_key.keys())
    for key in keys:
        a_deque = added_by_key.get(key, deque())
        r_deque = removed_by_key.get(key, deque())
        while a_deque and r_deque:
            fil_added.append(a_deque.popleft())
            fil_removed.append(r_deque.popleft())
        # Remaining are visible
        vis_added.extend(list(a_deque))
        vis_removed.extend(list(r_deque))

    # Preserve original order roughly by sorting with a stable key (PID if present, then name)
    def _order(p: Dict[str, Any]):
        return (p.get("ProcessId") or 0, (p.get("Name") or "").lower())

    vis_added.sort(key=_order)
    vis_removed.sort(key=_order)
    return vis_added, fil_added, vis_removed, fil_removed


def _is_bind_all(addr: Any) -> bool:
    a = str(addr or "").lower()
    return a in {"0.0.0.0", "::", "[::]"}


def _rule_matches_listener(rule: Dict[str, Any], listener: Dict[str, Any]) -> bool:
    # Simple match: inbound allow + protocol Any/exact + local port Any/exact/csv includes listener port
    if (str(rule.get("Direction") or "").lower() != "inbound"):
        return False
    if (str(rule.get("Action") or "").lower() != "allow"):
        return False
    rproto = str(rule.get("Protocol") or "Any").upper()
    lproto = str(listener.get("Protocol") or "").upper()
    if rproto not in {"ANY", lproto}:
        return False
    try:
        lport = int(listener.get("LocalPort"))
    except Exception:
        lport = None
    spec = str(rule.get("LocalPort") or "Any")
    if spec.lower() == "any":
        return True
    for token in spec.split(','):
        token = token.strip()
        if not token:
            continue
        if '-' in token:
            try:
                start, end = map(int, token.split('-', 1))
            except Exception:
                continue
            if lport is not None and start <= lport <= end:
                return True
        else:
            try:
                if lport is not None and int(token) == lport:
                    return True
            except Exception:
                continue
    return False


def _deprioritize_ephemeral_listeners(before: Dict[str, Any], after: Dict[str, Any], diff: Dict[str, Any], result: Dict[str, Any], filtered_meta: Dict[str, Any]) -> None:
    section = diff.get("network_listeners") or {}
    added = list(section.get("added", []))
    removed = list(section.get("removed", []))
    # Gather new inbound rules for quick matching (if firewall diff present)
    fw_added = (diff.get("firewall_rules") or {}).get("added", [])

    def should_filter(listener: Dict[str, Any]) -> bool:
        # Prefer to keep bind-all or service-associated listeners
        if _is_bind_all(listener.get("LocalAddress")):
            return False
        # If listener has service association, keep
        svc_names = listener.get("ServiceNames") or []
        if isinstance(svc_names, list) and svc_names:
            return False
        # If paired with new inbound firewall rule, keep
        for rule in fw_added:
            if _rule_matches_listener(rule, listener):
                return False
        # Otherwise filter (likely ephemeral localhost listener)
        return True

    vis_added, fil_added, vis_removed, fil_removed = [], [], [], []
    for lst in added:
        (fil_added if should_filter(lst) else vis_added).append(lst)
    for lst in removed:
        (fil_removed if should_filter(lst) else vis_removed).append(lst)

    nl = dict(section)
    nl["added"] = vis_added
    nl["removed"] = vis_removed
    # Merge with existing _filtered if present
    existing = nl.get("_filtered") or {}
    nl["_filtered"] = {
        **existing,
        "added_listeners": (existing.get("added_listeners") or []) + fil_added,
        "removed_listeners": (existing.get("removed_listeners") or []) + fil_removed,
        "reason": "ephemeral_listeners",
    }
    result["network_listeners"] = nl
    filtered_meta["network_listeners"] = {
        "filtered_added": len(fil_added) + (existing.get("filtered_added", 0) if existing else 0),
        "filtered_removed": len(fil_removed) + (existing.get("filtered_removed", 0) if existing else 0),
    }


def _is_trusted_signed_file(item: Dict[str, Any]) -> bool:
    f = item.get("file") or {}
    sig = f.get("signature") or {}
    status = str(sig.get("status") or "").lower()
    if status != "verified":
        return False
    publisher = sig.get("publisher") or ""
    if publisher not in TRUSTED_PUBLISHERS:
        return False
    path = str(f.get("path") or "").lower()
    expected_roots = ("c:\\windows", "c:\\program files", "c:\\program files (x86)")
    return any(path.startswith(root) for root in expected_roots)


def _deprioritize_trusted_binary_changes(diff: Dict[str, Any], result: Dict[str, Any], filtered_meta: Dict[str, Any]) -> None:
    # For changed items where only FileHash changed and file is trusted/signed from expected path, deprioritize
    for key in ("services", "scheduled_tasks", "registry_autoruns", "startup_folders", "firewall_rules"):
        section = diff.get(key)
        if not section:
            continue
        changed = list(section.get("changed", []))
        vis_changed: List[Dict[str, Any]] = []
        fil_changed: List[Dict[str, Any]] = []
        for ch in changed:
            changes = ch.get("changes", {})
            only_filehash = set(changes.keys()) == {"FileHash"}
            if only_filehash and _is_trusted_signed_file(ch.get("after", {})):
                fil_changed.append(ch)
            else:
                vis_changed.append(ch)
        if fil_changed:
            updated = dict(section)
            updated["changed"] = vis_changed
            existing = updated.get("_filtered") or {}
            updated["_filtered"] = {**existing, "trusted_binary_changes": fil_changed, "reason": "trusted_signed_binary"}
            result[key] = updated
            filtered_meta[key] = {
                "filtered_added": (existing.get("filtered_added", 0) if existing else 0),
                "filtered_removed": (existing.get("filtered_removed", 0) if existing else 0),
                "filtered_changed": len(fil_changed) + (existing.get("filtered_changed", 0) if existing else 0),
            }
        else:
            # Leave section unchanged
            pass
