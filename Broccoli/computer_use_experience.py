#!/usr/bin/env python3
"""Computer Use experience-rule store (shared by the main app and the worker).

A rule is natural language plus ONE compiled operational form. Compiled forms
are DATA, never executable code:

  - prompt_note:  {"note": str}                      -> injected into the model
                                                        instruction when the rule
                                                        matches the bound app.
  - hook_params:  {"hook": <whitelist>, ...fields}   -> parameterizes an existing
                                                        worker mechanism.
        hooks: "role_action_ban"    {"tool": str, "role": str}
               "non_ax_body"        {}               (app's body area is not in AX;
                                                      steers writes to the pixel path)
               "relocate_margins"   {"top": num, "side": num}
  - dsl:          {"when": {...}, "then": [{...}]}   -> tiny condition->action
                                                        interpreter; every action
                                                        reduces to an instruction
                                                        note. Safety gates stay in
                                                        worker code and can never
                                                        be unlocked from here.

DSL "when" fields (all optional, ANDed): app_contains, geometry_class,
transfer_pending (bool), phase ("navigation"|"write"), last_error_code.
DSL "then" actions: {"inject_note": str} or {"prefer_strategy": <whitelist>}.
Strategies map to fixed guidance text: menu_bar / pixel_write /
foreground_key_retry / different_element / report_blocker.
"""

from __future__ import annotations

import copy
import json
import os
import re
import tempfile
import threading
import time
from typing import Any

STORE_FILENAME = "computer_use_experience.json"
STORE_VERSION = 1
_STORE_LOCK = threading.Lock()

COMPILED_KINDS = ("prompt_note", "hook_params", "dsl")
HOOK_WHITELIST = ("role_action_ban", "non_ax_body", "relocate_margins")
STRATEGY_TEXT = {
    "menu_bar": (
        "Prefer the app's MENU-BAR items for commands (File/Edit menus support "
        "AXPress reliably in the background)."
    ),
    "pixel_write": (
        "The write destination is a non-AX surface: do not click to focus; the "
        "worker writes it via the pixel path automatically when you stop."
    ),
    "foreground_key_retry": (
        "A dropped background key press escalates automatically: after one "
        "no-effect settlement the worker retries the same key transiently in "
        "the foreground."
    ),
    "different_element": (
        "Do not repeat a refused or no-effect element; choose a different "
        "element or a different rung."
    ),
    "report_blocker": (
        "If every sanctioned rung is exhausted, call finish and report the "
        "blocker honestly instead of retrying."
    ),
}

PROVENANCE_BUILTIN = "builtin"
PROVENANCE_AUTO = "auto"
PROVENANCE_USER = "user"

STATUS_ACTIVE = "active"
STATUS_PENDING = "pending"
STATUS_COMPILING = "compiling"
STATUS_FAILED = "failed"

# Stores written before the English-default sweep used Chinese status values.
_LEGACY_STATUS = {
    "已生效": STATUS_ACTIVE,
    "等待生成": STATUS_PENDING,
    "生成中": STATUS_COMPILING,
    "生成失败": STATUS_FAILED,
}


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def nl_hash(rule: dict) -> str:
    import hashlib
    payload = "\n".join([
        str(rule.get("name", "") or ""),
        str(rule.get("steps_nl", "") or ""),
        str(rule.get("rule_nl", "") or ""),
        json.dumps(rule.get("applies_to") or {}, ensure_ascii=False, sort_keys=True),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def builtin_rules() -> list[dict]:
    """Factory defaults distilled from real-machine evidence (2026-07-18..22).

    Editable, restorable, never deletable. Compiled payloads are handwritten -
    builtins never depend on the AI compiler.
    """
    def rule(rid, name, applies, steps, text, kind, payload):
        item = {
            "id": rid,
            "name": name,
            "provenance": PROVENANCE_BUILTIN,
            "enabled": True,
            "applies_to": applies,
            "steps_nl": steps,
            "rule_nl": text,
            "compiled": {
                "kind": kind,
                "payload": payload,
                "nl_hash": "",
                "compiled_at": _now(),
                "status": STATUS_ACTIVE,
                "error": "",
            },
            "evidence": "Builtin: distilled from real-machine runs, 2026-07",
            "created_at": _now(),
            "updated_at": _now(),
        }
        item["compiled"]["nl_hash"] = nl_hash(item)
        return item

    return [
        rule(
            "builtin-text-transfer", "Text copy-paste",
            {"app": "any", "task_shape": "verbatim text transfer"},
            "1. Capture the source text with capture_ax_text (never touches the system clipboard)\n"
            "2. Prepare the destination container (new note/document)\n"
            "3. Prefer insert_captured_text with exact hash read-back verification\n"
            "4. When the body is not in the accessibility tree, the worker writes it via the pixel path\n"
            "5. Never click an empty body to focus it (a caret is not observable progress)",
            "System clipboard shortcuts (Cmd+A/C/V) are unreliable in SwiftUI apps and stay "
            "banned; a write counts only when proven by read-back or visual+semantic change.",
            "prompt_note",
            {"note": (
                "TEXT-TRANSFER PLAYBOOK: capture with capture_ax_text; write with "
                "insert_captured_text into a writable AX target; never use "
                "Cmd+A/C/V; never click an empty body to 'focus' it - the caret "
                "is not observable progress and the worker auto-writes non-AX "
                "bodies via the pixel path after you stop clicking."
            )},
        ),
        rule(
            "builtin-notes-non-ax-body", "Notes body is a non-AX surface",
            {"app": "Notes", "task_shape": "any"},
            "1. The Notes note body never appears in the accessibility tree "
            "(verified: fully rendered window, 233 elements, zero body)\n"
            "2. Sidebar rows/cells reject AXPress (kAXError -25206)\n"
            "3. Create notes via the toolbar button (present in the tree once rendered)\n"
            "4. Body writes work only via the pixel path",
            "For Notes: do not retry clicks on sidebar rows/cells; do not try to focus "
            "the body; leave the write to the worker's pixel path.",
            "hook_params",
            {"hook": "non_ax_body"},
        ),
        rule(
            "builtin-notes-row-ban", "Notes rows reject AX press",
            {"app": "Notes", "task_shape": "any"},
            "Notes sidebar axcell/axrow elements return kAXError -25205/-25206 for "
            "AXPress/AXOpen/AXPick (element-level unsupported, not a permission issue)",
            "Ban from the start: never send AX-form click/double_click/right_click to "
            "Notes axcell/axrow elements; steer to a different target immediately.",
            "hook_params",
            {"hook": "role_action_ban", "tool": "click", "role": "axcell"},
        ),
        rule(
            "builtin-stage-parked-render", "Parked windows do not render",
            {"app": "any", "task_shape": "any"},
            "1. Stage-parked / inactive-display / off-screen SwiftUI windows do not render; "
            "their AX trees are partial or empty\n"
            "2. Actions delivered to such windows settle 'delivered but no effect'\n"
            "3. The worker auto-expands them (bring_to_front; CLI channel when the daemon "
            "activation is silently ignored)\n"
            "4. The prior frontmost app is restored when the task ends",
            "Do not spam a parked/off-screen window; wait for the worker's foreground "
            "expand and act from the fresh tree.",
            "prompt_note",
            {"note": (
                "PARKED WINDOWS DO NOT RENDER: a Stage-parked/off-screen window "
                "exposes a partial or empty AX tree and delivered actions settle "
                "no-effect. Do not spam it - the worker expands it automatically; "
                "act from the fresh tree afterwards."
            )},
        ),
        rule(
            "builtin-relocate-margins", "Cross-display relocation margins",
            {"app": "any", "task_shape": "any"},
            "When moving a window to the target display: center horizontally (minimum "
            "side margin 24pt), top edge 60pt inside, and the whole window must land "
            "fully on screen; never fling it toward an edge.",
            "Tunable landing parameters: top = distance inside the top edge, side = "
            "minimum horizontal margin.",
            "hook_params",
            {"hook": "relocate_margins", "top": 60, "side": 24},
        ),
    ]


# ---------------------------------------------------------------- store I/O

def store_path(base_dir: str) -> str:
    return os.path.join(str(base_dir or ""), STORE_FILENAME)


def _normalize_rule(raw: Any) -> dict | None:
    if not isinstance(raw, dict):
        return None
    rid = str(raw.get("id", "") or "").strip()
    if not rid:
        return None
    compiled = raw.get("compiled") if isinstance(raw.get("compiled"), dict) else {}
    kind = str(compiled.get("kind", "") or "")
    payload = compiled.get("payload") if isinstance(compiled.get("payload"), dict) else {}
    if kind not in COMPILED_KINDS:
        kind, payload = "", {}
    applies = raw.get("applies_to") if isinstance(raw.get("applies_to"), dict) else {}
    return {
        "id": rid,
        "name": str(raw.get("name", "") or rid),
        "provenance": str(raw.get("provenance", PROVENANCE_USER) or PROVENANCE_USER),
        "enabled": bool(raw.get("enabled", True)),
        "applies_to": {
            "app": str(applies.get("app", "any") or "any"),
            "task_shape": str(applies.get("task_shape", "any") or "any"),
        },
        "steps_nl": str(raw.get("steps_nl", "") or ""),
        "rule_nl": str(raw.get("rule_nl", "") or ""),
        "compiled": {
            "kind": kind,
            "payload": payload,
            "nl_hash": str(compiled.get("nl_hash", "") or ""),
            "compiled_at": str(compiled.get("compiled_at", "") or ""),
            "status": _LEGACY_STATUS.get(
                str(compiled.get("status", "") or ""),
                str(compiled.get("status", STATUS_PENDING) or STATUS_PENDING),
            ),
            "error": str(compiled.get("error", "") or ""),
        },
        "evidence": str(raw.get("evidence", "") or ""),
        "created_at": str(raw.get("created_at", "") or _now()),
        "updated_at": str(raw.get("updated_at", "") or _now()),
    }


def load_store(base_dir: str) -> dict:
    """Load the store, seeding/refreshing builtin rules (never duplicating)."""
    path = store_path(base_dir)
    with _STORE_LOCK:
        data: dict = {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                data = json.load(handle)
        except Exception:
            data = {}
        raw_rules = data.get("rules") if isinstance(data, dict) else None
        rules: list[dict] = []
        seen: set[str] = set()
        for item in raw_rules or []:
            normalized = _normalize_rule(item)
            if normalized and normalized["id"] not in seen:
                seen.add(normalized["id"])
                rules.append(normalized)
        for builtin in builtin_rules():
            if builtin["id"] not in seen:
                rules.append(copy.deepcopy(builtin))
                seen.add(builtin["id"])
        return {"version": STORE_VERSION, "rules": rules}


def save_store(base_dir: str, store: dict) -> bool:
    path = store_path(base_dir)
    with _STORE_LOCK:
        try:
            os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
            payload = json.dumps(
                {"version": STORE_VERSION, "rules": list(store.get("rules") or [])},
                ensure_ascii=False, indent=1,
            )
            fd, tmp_path = tempfile.mkstemp(
                dir=os.path.dirname(path) or ".", prefix=".exp_", suffix=".tmp",
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as handle:
                    handle.write(payload)
                os.replace(tmp_path, path)
            finally:
                try:
                    if os.path.exists(tmp_path):
                        os.remove(tmp_path)
                except Exception:
                    pass
            return True
        except Exception:
            return False


def find_rule(store: dict, rule_id: str) -> dict | None:
    for item in store.get("rules") or []:
        if isinstance(item, dict) and item.get("id") == rule_id:
            return item
    return None


def restore_builtin(store: dict, rule_id: str) -> bool:
    for builtin in builtin_rules():
        if builtin["id"] == rule_id:
            for index, item in enumerate(store.get("rules") or []):
                if isinstance(item, dict) and item.get("id") == rule_id:
                    store["rules"][index] = copy.deepcopy(builtin)
                    return True
    return False


# ------------------------------------------------------------- validation

def validate_compiled(kind: str, payload: Any) -> str:
    """Return '' when valid, else a human-readable error."""
    if kind not in COMPILED_KINDS:
        return f"unknown kind {kind!r}"
    if not isinstance(payload, dict):
        return "payload must be an object"
    if kind == "prompt_note":
        note = payload.get("note")
        if not isinstance(note, str) or not note.strip():
            return "prompt_note needs a non-empty 'note' string"
        if len(note) > 1200:
            return "note too long (max 1200 chars)"
        return ""
    if kind == "hook_params":
        hook = str(payload.get("hook", "") or "")
        if hook not in HOOK_WHITELIST:
            return f"hook must be one of {HOOK_WHITELIST}"
        if hook == "role_action_ban":
            if not str(payload.get("role", "") or "").strip():
                return "role_action_ban needs 'role'"
            return ""
        if hook == "relocate_margins":
            for key in ("top", "side"):
                value = payload.get(key)
                if not isinstance(value, (int, float)) or not (0 <= float(value) <= 400):
                    return f"relocate_margins '{key}' must be a number in [0, 400]"
            return ""
        return ""
    when = payload.get("when")
    then = payload.get("then")
    if not isinstance(when, dict):
        return "dsl needs a 'when' object"
    allowed_when = {"app_contains", "geometry_class", "transfer_pending",
                    "phase", "last_error_code"}
    unknown = set(when) - allowed_when
    if unknown:
        return f"dsl 'when' has unknown fields: {sorted(unknown)}"
    if not isinstance(then, list) or not then:
        return "dsl needs a non-empty 'then' list"
    for action in then:
        if not isinstance(action, dict):
            return "dsl actions must be objects"
        if "inject_note" in action:
            if not isinstance(action["inject_note"], str) or not action["inject_note"].strip():
                return "inject_note must be a non-empty string"
        elif "prefer_strategy" in action:
            if action["prefer_strategy"] not in STRATEGY_TEXT:
                return f"prefer_strategy must be one of {sorted(STRATEGY_TEXT)}"
        else:
            return "dsl action must be inject_note or prefer_strategy"
    return ""


# --------------------------------------------------------- worker-side use

def _app_matches(rule: dict, app_label: str) -> bool:
    wanted = str(((rule.get("applies_to") or {}).get("app", "any")) or "any").strip().lower()
    if wanted in ("", "any", "*"):
        return True
    return wanted in str(app_label or "").strip().lower()


def rules_for_worker(store: dict) -> list[dict]:
    """Enabled rules with a valid compiled form, serialized for the worker config."""
    out = []
    for rule in store.get("rules") or []:
        if not isinstance(rule, dict) or not rule.get("enabled"):
            continue
        compiled = rule.get("compiled") or {}
        kind = str(compiled.get("kind", "") or "")
        payload = compiled.get("payload") if isinstance(compiled.get("payload"), dict) else {}
        if compiled.get("status") != STATUS_ACTIVE or validate_compiled(kind, payload):
            continue
        out.append({
            "id": rule.get("id"),
            "name": rule.get("name"),
            "applies_to": dict(rule.get("applies_to") or {}),
            "kind": kind,
            "payload": copy.deepcopy(payload),
        })
    return out


def prompt_notes(worker_rules: list[dict], app_label: str) -> list[str]:
    notes = []
    for rule in worker_rules or []:
        if rule.get("kind") == "prompt_note" and _app_matches(rule, app_label):
            note = str((rule.get("payload") or {}).get("note", "") or "").strip()
            if note:
                notes.append(note)
        elif rule.get("kind") == "hook_params" and _app_matches(rule, app_label):
            if (rule.get("payload") or {}).get("hook") == "non_ax_body":
                notes.append(STRATEGY_TEXT["pixel_write"])
    return notes


def role_action_bans(worker_rules: list[dict]) -> set[tuple]:
    """(app_lower_or_'', tool_or_'', role_lower) triples; '' = any."""
    bans = set()
    for rule in worker_rules or []:
        payload = rule.get("payload") or {}
        if rule.get("kind") == "hook_params" and payload.get("hook") == "role_action_ban":
            app = str(((rule.get("applies_to") or {}).get("app", "any")) or "any").strip().lower()
            bans.add((
                "" if app in ("", "any", "*") else app,
                str(payload.get("tool", "") or "").strip().lower(),
                str(payload.get("role", "") or "").strip().lower().replace("_", ""),
            ))
    return bans


def role_banned(bans: set[tuple], app_label: str, tool: str, role: str) -> bool:
    app_lower = str(app_label or "").strip().lower()
    tool_lower = str(tool or "").strip().lower()
    role_lower = str(role or "").strip().lower().replace("_", "")
    if not role_lower:
        return False
    for ban_app, ban_tool, ban_role in bans or set():
        if ban_role != role_lower:
            continue
        if ban_tool and ban_tool != tool_lower:
            continue
        if ban_app and ban_app not in app_lower:
            continue
        return True
    return False


def relocate_margins(worker_rules: list[dict], app_label: str) -> tuple[float, float]:
    top, side = 60.0, 24.0
    for rule in worker_rules or []:
        payload = rule.get("payload") or {}
        if rule.get("kind") == "hook_params" and payload.get("hook") == "relocate_margins" \
                and _app_matches(rule, app_label):
            try:
                top = float(payload.get("top", top))
                side = float(payload.get("side", side))
            except (TypeError, ValueError):
                pass
    return top, side


def non_ax_body_apps(worker_rules: list[dict]) -> set[str]:
    apps = set()
    for rule in worker_rules or []:
        payload = rule.get("payload") or {}
        if rule.get("kind") == "hook_params" and payload.get("hook") == "non_ax_body":
            app = str(((rule.get("applies_to") or {}).get("app", "") or "")).strip().lower()
            if app and app not in ("any", "*"):
                apps.add(app)
    return apps


def evaluate_dsl(worker_rules: list[dict], context: dict) -> list[str]:
    """Evaluate dsl rules against a context; every action reduces to a note."""
    notes = []
    app_label = str(context.get("app_label", "") or "")
    for rule in worker_rules or []:
        if rule.get("kind") != "dsl" or not _app_matches(rule, app_label):
            continue
        payload = rule.get("payload") or {}
        when = payload.get("when") if isinstance(payload.get("when"), dict) else {}
        matched = True
        if "app_contains" in when:
            matched &= str(when["app_contains"]).strip().lower() in app_label.strip().lower()
        if matched and "geometry_class" in when:
            matched &= str(when["geometry_class"]) == str(context.get("geometry_class", ""))
        if matched and "transfer_pending" in when:
            matched &= bool(when["transfer_pending"]) == bool(context.get("transfer_pending"))
        if matched and "phase" in when:
            matched &= str(when["phase"]) == str(context.get("phase", ""))
        if matched and "last_error_code" in when:
            matched &= str(when["last_error_code"]) == str(context.get("last_error_code", ""))
        if not matched:
            continue
        for action in payload.get("then") or []:
            if not isinstance(action, dict):
                continue
            if isinstance(action.get("inject_note"), str) and action["inject_note"].strip():
                notes.append(action["inject_note"].strip())
            elif action.get("prefer_strategy") in STRATEGY_TEXT:
                notes.append(STRATEGY_TEXT[action["prefer_strategy"]])
    return notes


# -------------------------------------------------------- learned candidates

def merge_learned_candidates(store: dict, candidates: list[dict]) -> int:
    """Merge worker-discovered facts; dedupe by (fact_key). Returns added count."""
    existing_ids = {str(rule.get("id")) for rule in store.get("rules") or []}
    added = 0
    for candidate in candidates or []:
        if not isinstance(candidate, dict):
            continue
        fact_key = re.sub(r"[^a-z0-9_-]+", "-", str(candidate.get("fact_key", "") or "").lower())
        if not fact_key:
            continue
        rid = f"auto-{fact_key}"
        if rid in existing_ids:
            continue
        kind = str(candidate.get("kind", "") or "")
        payload = candidate.get("payload") if isinstance(candidate.get("payload"), dict) else {}
        if validate_compiled(kind, payload):
            continue
        rule = {
            "id": rid,
            "name": str(candidate.get("name", "") or rid),
            "provenance": PROVENANCE_AUTO,
            "enabled": True,
            "applies_to": {
                "app": str(candidate.get("app", "any") or "any"),
                "task_shape": "any",
            },
            "steps_nl": str(candidate.get("steps_nl", "") or ""),
            "rule_nl": str(candidate.get("rule_nl", "") or ""),
            "compiled": {
                "kind": kind,
                "payload": copy.deepcopy(payload),
                "nl_hash": "",
                "compiled_at": _now(),
                "status": STATUS_ACTIVE,
                "error": "",
            },
            "evidence": str(candidate.get("evidence", "") or ""),
            "created_at": _now(),
            "updated_at": _now(),
        }
        rule["compiled"]["nl_hash"] = nl_hash(rule)
        store.setdefault("rules", []).append(rule)
        existing_ids.add(rid)
        added += 1
    return added


# ----------------------------------------------------------- AI compilation

def build_compile_messages(rule: dict) -> list[dict]:
    """Messages asking the model to compile NL -> one operational form."""
    spec = {
        "name": str(rule.get("name", "") or ""),
        "applies_to": rule.get("applies_to") or {},
        "steps_nl": str(rule.get("steps_nl", "") or ""),
        "rule_nl": str(rule.get("rule_nl", "") or ""),
    }
    instruction = (
        "You compile a natural-language desktop-automation experience rule into "
        "EXACTLY ONE JSON operational form. Reply with ONLY a JSON object, no "
        "prose, shaped as {\"kind\": ..., \"payload\": ...}.\n"
        "Allowed kinds:\n"
        "1. prompt_note: {\"note\": \"<=1200 chars of imperative guidance injected "
        "into the automation model's instruction when the rule's app matches\"}\n"
        "2. hook_params: {\"hook\": \"role_action_ban\", \"tool\": \"click\", "
        "\"role\": \"axcell\"} | {\"hook\": \"non_ax_body\"} | {\"hook\": "
        "\"relocate_margins\", \"top\": 60, \"side\": 24}\n"
        "3. dsl: {\"when\": {optional: app_contains/geometry_class/"
        "transfer_pending/phase/last_error_code}, \"then\": [{\"inject_note\": "
        "\"...\"} or {\"prefer_strategy\": one of menu_bar/pixel_write/"
        "foreground_key_retry/different_element/report_blocker}]}\n"
        "Choose the simplest form that faithfully expresses the rule. Most rules "
        "compile to prompt_note.\n\nRULE:\n" + json.dumps(spec, ensure_ascii=False, indent=1)
    )
    return [{"role": "user", "content": instruction}]


def parse_compiled_response(text: str) -> tuple[str, dict, str]:
    """(kind, payload, error). Error non-empty on failure."""
    raw = str(text or "").strip()
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        return "", {}, "no JSON object in the model reply"
    try:
        data = json.loads(match.group(0))
    except Exception as exc:
        return "", {}, f"JSON parse failed: {exc}"
    kind = str((data or {}).get("kind", "") or "")
    payload = data.get("payload") if isinstance(data.get("payload"), dict) else {}
    error = validate_compiled(kind, payload)
    if error:
        return "", {}, error
    return kind, payload, ""
