#!/usr/bin/env python3
"""Resolve explicit lesson roles and check their runtime receipt.

This validates supplied identities; the agent must obtain them from its host's
runtime metadata. It cannot inspect or enforce a model dispatch itself.
"""

import argparse
import json
import os
from pathlib import Path
import sys

ROLES = ("author", "reviewer", "support")
FIELDS = ("model", "effort")
IMPLICIT_MARKERS = frozenset(("inherit", "default", "auto", "automatic"))


class RoutingError(ValueError):
    pass


def read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RoutingError(f"{path}: {exc}") from exc
    if not isinstance(value, dict):
        raise RoutingError(f"{path}: expected a JSON object")
    return value


def role(value, where):
    if not isinstance(value, dict) or set(value) != set(FIELDS):
        raise RoutingError(f"{where}: require exactly model and effort")
    for field in FIELDS:
        if not isinstance(value[field], str) or not value[field].strip():
            raise RoutingError(f"{where}: {field} must be a nonempty string")
        if value[field] != value[field].strip():
            raise RoutingError(f"{where}: {field} has surrounding whitespace")
        if value[field].casefold() in IMPLICIT_MARKERS:
            raise RoutingError(f"{where}: {field} must be an explicit identity, not {value[field]}")
    return dict(value)


def policy(value, where, complete):
    if set(value) != {"version", "roles"} or value["version"] != 1:
        raise RoutingError(f"{where}: require version 1 and roles")
    roles = value["roles"]
    if not isinstance(roles, dict) or not set(roles).issubset(ROLES):
        raise RoutingError(f"{where}: unknown or malformed roles")
    if complete and set(roles) != set(ROLES):
        raise RoutingError(f"{where}: require author, reviewer, and support")
    if not roles:
        raise RoutingError(f"{where}: roles cannot be empty")
    return {name: role(spec, f"{where}: {name}") for name, spec in roles.items()}


def resolve(workspace=None, user_config=None, workspace_config=None, override=None):
    user_path = Path(user_config) if user_config else Path(
        os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    ) / "blackboard/lesson-routing.json"
    workspace_path = (Path(workspace_config) if workspace_config else
                      Path(workspace) / ".blackboard/lesson-routing.json" if workspace else None)
    for named_path in (user_config, workspace_config):
        if named_path is not None and not Path(named_path).is_file():
            raise RoutingError(f"{named_path}: explicitly named policy file is missing")
    request = policy(read_json(override), str(override), complete=False) if override else {}
    # A complete direct request outranks even a broken lower-priority file.
    selected = {}
    sources = {}
    # A workspace policy replaces the whole user policy; neither silently
    # inherits missing roles from the other.
    path = workspace_path if workspace_path and workspace_path.exists() else user_path
    if path.exists() and set(request) != set(ROLES):
        selected = policy(read_json(path), str(path), complete=True)
        sources = {name: str(path) for name in selected}
    if request:
        selected.update(request)
        sources.update({name: "explicit user request" for name in request})
    return {"mode": "explicit" if selected else "automatic",
            "roles": {name: {"requested": selected[name], "source": sources[name]}
                      for name in ROLES if name in selected}}


def check(receipt, selected):
    if receipt.get("selection") != selected:
        raise RoutingError("receipt selection differs from current policy; resolve again")
    runs = receipt.get("runs")
    if not isinstance(runs, dict):
        raise RoutingError("receipt: runs must be an object")
    if selected["mode"] == "automatic":
        return
    if not isinstance(receipt.get("long_lesson"), bool):
        raise RoutingError("receipt: long_lesson must be true or false")
    for name in ("author", "reviewer", "support"):
        if name == "support" and name not in runs:
            continue  # Support is optional; its identity is required if used.
        run = runs.get(name)
        if not isinstance(run, dict):
            raise RoutingError(f"receipt: missing {name} runtime record")
        selected_role = selected["roles"].get(name)
        wanted = (selected_role["requested"] if selected_role else
                  role(run.get("requested"), f"receipt: {name} requested"))
        if run.get("requested") != wanted:
            raise RoutingError(f"receipt: {name} requested identity differs from policy")
        if run.get("resolved") != wanted:
            raise RoutingError(f"receipt: {name} resolved runtime identity differs from request")
        if run.get("outcome") != ("passed" if name == "reviewer" else "complete"):
            raise RoutingError(f"receipt: {name} did not complete")
    reviewer = runs["reviewer"]
    if reviewer.get("fresh_agent") is not True or reviewer.get("findings_resolved") is not True:
        raise RoutingError("receipt: independent review or findings resolution missing")
    if "tone_editor" not in runs:
        raise RoutingError("receipt: every lesson requires a fresh tone editor")
    if "tone_editor" in runs:
        tone = runs["tone_editor"]
        author = runs["author"]["resolved"]
        if (not isinstance(tone, dict) or tone.get("requested") != author or
                tone.get("resolved") != author or tone.get("fresh_agent") is not True or
                tone.get("outcome") != "complete"):
            raise RoutingError("receipt: tone editor must be fresh, complete, and match author identity")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("resolve", "check"))
    parser.add_argument("--workspace", help="workspace root containing optional .blackboard policy")
    parser.add_argument("--user-config", help="override per-user config path (testing or setup)")
    parser.add_argument("--workspace-config", help="override workspace config path")
    parser.add_argument("--override", help="JSON file containing explicit user-requested role overrides")
    parser.add_argument("--receipt", help="receipt JSON path for check")
    args = parser.parse_args(argv)
    try:
        selected = resolve(args.workspace, args.user_config, args.workspace_config, args.override)
        if args.command == "check":
            if not args.receipt:
                raise RoutingError("check requires --receipt")
            check(read_json(args.receipt), selected)
            print("lesson routing receipt: OK")
        else:
            print(json.dumps(selected, indent=2))
    except RoutingError as exc:
        print(f"lesson routing blocked: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
