#!/usr/bin/env python3
"""
Policy gate for tasks/tasks.yaml

Fails CI if:
- required fields missing
- task states invalid
- scope.in contains forbidden features (feed/thread/profile/streak)
- scope.out does NOT explicitly exclude those forbidden features
- missing security/privacy acceptance criteria
- missing security tests
"""

import os
import re
import sys
from typing import Any, Dict, List, Tuple

TASKS_PATH = os.path.join("tasks", "tasks.yaml")

ALLOWED_STATES = {"BACKLOG", "TODO", "IN_PROGRESS", "REVIEW", "DONE"}

# Red lines to exclude (must appear in scope.out in some form)
REDLINE_PATTERNS = {
    "feed": re.compile(r"\bfeed\b|infinite\s*scroll", re.IGNORECASE),
    "threads_chat": re.compile(r"\bthread\b|\bthreads\b|\bchat\b|reply|conversation", re.IGNORECASE),
    "profiles_identity": re.compile(r"\bprofile\b|\bprofiles\b|handle|username|identity|sender", re.IGNORECASE),
    "streaks_leaderboards": re.compile(r"\bstreak\b|\bstreaks\b|leaderboard|rank|ranking", re.IGNORECASE),
}

# Forbidden if they appear in scope.in/title/goal/etc.
FORBIDDEN_IN_SCOPE_IN = [
    REDLINE_PATTERNS["feed"],
    REDLINE_PATTERNS["threads_chat"],
    REDLINE_PATTERNS["profiles_identity"],
    REDLINE_PATTERNS["streaks_leaderboards"],
]

# Must-have security acceptance criteria keywords (loose checks)
SECURITY_MUST_HAVE = [
    re.compile(r"authn|authentication|jwt|token", re.IGNORECASE),
    re.compile(r"authz|authorization|scoped|owner|cross-user", re.IGNORECASE),
    re.compile(r"rate\s*limit|throttle", re.IGNORECASE),
    re.compile(r"validation|reject\s+unknown|schema", re.IGNORECASE),
    re.compile(r"size\s*limit|max\s*(body|text)", re.IGNORECASE),
    re.compile(r"enumeration|non-guessable|uuid|ulid|sequential", re.IGNORECASE),
    re.compile(r"no\s+raw\s+message\s+text|no\s+raw\s+text\s+in\s+logs|redact", re.IGNORECASE),
]

PRIVACY_MUST_HAVE = [
    re.compile(r"risk_level\s*==\s*2|risk\s*level\s*2|level\s*2", re.IGNORECASE),
    re.compile(r"do\s+not\s+persist\s+free\s*text|no\s+free\s*text\s+persist", re.IGNORECASE),
]

SECURITY_TESTS_MUST_HAVE = [
    re.compile(r"authz|cross-user|cannot\s+access|forbidden", re.IGNORECASE),
    re.compile(r"rate\s*limit|throttle", re.IGNORECASE),
    re.compile(r"identity\s+leak|phone|email|handle|link", re.IGNORECASE),
    re.compile(r"risk_level\s*==\s*2|no\s+free\s*text\s+write|does\s+not\s+write", re.IGNORECASE),
]


def _fail(msg: str) -> None:
    print(f"[FAIL] {msg}")
    sys.exit(1)


def _warn(msg: str) -> None:
    print(f"[WARN] {msg}")


def _ok(msg: str) -> None:
    print(f"[OK] {msg}")


def _as_list(x: Any) -> List[Any]:
    if x is None:
        return []
    if isinstance(x, list):
        return x
    return [x]


def _flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(_flatten_text(v) for v in value)
    if isinstance(value, dict):
        return "\n".join(f"{k}: {_flatten_text(v)}" for k, v in value.items())
    return str(value)


def _ensure_yaml_available():
    try:
        import yaml  # type: ignore
        return yaml
    except Exception:
        _fail(
            "PyYAML not installed. Install it with: pip3 install pyyaml\n"
            "or add it to your CI step before running this script."
        )


def _load_tasks(path: str) -> List[Dict[str, Any]]:
    yaml = _ensure_yaml_available()

    if not os.path.exists(path):
        _fail(f"Missing {path}. Create it and add tasks.")

    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if data is None:
        return []

    # Support either:
    # - a list of task dicts
    # - a dict with "tasks": [...]
    if isinstance(data, list):
        tasks = data
    elif isinstance(data, dict) and isinstance(data.get("tasks"), list):
        tasks = data["tasks"]
    else:
        _fail(f"{path} must be a YAML list of tasks OR a dict with key 'tasks'.")

    # Ensure each item is a dict
    for i, t in enumerate(tasks):
        if not isinstance(t, dict):
            _fail(f"Task at index {i} is not a mapping/object.")
    return tasks


def _require_fields(task: Dict[str, Any], fields: List[str], task_id: str):
    for f in fields:
        if f not in task or task[f] in (None, "", []):
            _fail(f"Task {task_id}: missing/empty required field '{f}'.")


def _check_state(task: Dict[str, Any], task_id: str):
    state = task.get("state")
    if state not in ALLOWED_STATES:
        _fail(f"Task {task_id}: invalid state '{state}'. Allowed: {sorted(ALLOWED_STATES)}")


def _check_scope_redlines(task: Dict[str, Any], task_id: str):
    scope = task.get("scope") or {}
    scope_in = _as_list(scope.get("in"))
    scope_out = _as_list(scope.get("out"))

    in_text = _flatten_text(scope_in + [task.get("title"), task.get("goal")])
    out_text = _flatten_text(scope_out)

    # Forbidden in scope.in/title/goal
    for pat in FORBIDDEN_IN_SCOPE_IN:
        if pat.search(in_text):
            _fail(f"Task {task_id}: forbidden feature detected in scope.in/title/goal: '{pat.pattern}'")

    # Must explicitly exclude in scope.out (at least one item per category)
    missing = []
    for name, pat in REDLINE_PATTERNS.items():
        if not pat.search(out_text):
            missing.append(name)

    if missing:
        _fail(
            f"Task {task_id}: scope.out must explicitly exclude red-lines. Missing exclusions for: {missing}.\n"
            "Add items in scope.out like: 'No feed', 'No threads/chat', 'No profiles/identity', 'No streaks/leaderboards'."
        )


def _check_acceptance_security(task: Dict[str, Any], task_id: str):
    ac = task.get("acceptance_criteria") or {}
    security = _as_list(ac.get("security"))
    privacy = _as_list(ac.get("privacy"))

    if not security:
        _fail(f"Task {task_id}: acceptance_criteria.security is required and cannot be empty.")
    if not privacy:
        _fail(f"Task {task_id}: acceptance_criteria.privacy is required and cannot be empty.")

    sec_text = _flatten_text(security)
    priv_text = _flatten_text(privacy)

    for pat in SECURITY_MUST_HAVE:
        if not pat.search(sec_text):
            _fail(f"Task {task_id}: acceptance_criteria.security missing requirement matching: '{pat.pattern}'")

    # Crisis rule: risk_level==2 + do not persist free text
    for pat in PRIVACY_MUST_HAVE:
        if not pat.search(priv_text):
            _fail(f"Task {task_id}: acceptance_criteria.privacy missing requirement matching: '{pat.pattern}'")


def _check_tests_security(task: Dict[str, Any], task_id: str):
    tests = task.get("tests") or {}
    sec_tests = _as_list(tests.get("security"))
    if not sec_tests:
        _fail(f"Task {task_id}: tests.security is required and cannot be empty.")

    text = _flatten_text(sec_tests)
    for pat in SECURITY_TESTS_MUST_HAVE:
        if not pat.search(text):
            _fail(f"Task {task_id}: tests.security missing test coverage matching: '{pat.pattern}'")


def _check_completion_definition(task: Dict[str, Any], task_id: str):
    cd = _as_list(task.get("completion_definition"))
    if not cd:
        _fail(f"Task {task_id}: completion_definition is required.")
    cd_text = _flatten_text(cd)
    # Basic sanity: must mention tests + security/safety
    if not re.search(r"test", cd_text, re.IGNORECASE):
        _fail(f"Task {task_id}: completion_definition should mention tests passing.")
    if not re.search(r"security", cd_text, re.IGNORECASE):
        _fail(f"Task {task_id}: completion_definition should mention security checklist passed.")
    if not re.search(r"red-line|red line|no red", cd_text, re.IGNORECASE):
        _warn(f"Task {task_id}: consider explicitly mentioning red-line violations in completion_definition.")


def main() -> None:
    tasks = _load_tasks(TASKS_PATH)
    if not tasks:
        _fail(f"{TASKS_PATH} is empty. Add tasks before running the gate.")

    _ok(f"Loaded {len(tasks)} tasks from {TASKS_PATH}")

    seen_ids = set()
    for idx, task in enumerate(tasks):
        task_id = task.get("id") or f"(index {idx})"
        _require_fields(task, ["id", "title", "owner", "state", "goal", "scope", "acceptance_criteria", "tests"], task_id)

        if task["id"] in seen_ids:
            _fail(f"Duplicate task id: {task['id']}")
        seen_ids.add(task["id"])

        _check_state(task, task_id)
        _check_scope_redlines(task, task_id)
        _check_acceptance_security(task, task_id)
        _check_tests_security(task, task_id)
        _check_completion_definition(task, task_id)

    _ok("Policy check passed ✅")


if __name__ == "__main__":
    main()
