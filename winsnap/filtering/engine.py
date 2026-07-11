from __future__ import annotations

from typing import Any, Dict, List, Tuple


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
