#!/usr/bin/env python3
"""Broccoli Computer Use worker (phase 1: local cua-driver over MCP stdio).

Observation contract (verified against cua-driver 0.8.3 on 2026-07-18):
the real driver has NO tool named "screenshot" and its full-desktop capture
(get_desktop_state) is DISABLED by default (capture_scope=window). Broccoli
keeps the ordinary daemon in that privacy-preserving mode. A main-display task
may instead use a task-private daemon/HOME/socket whose desktop scope is fully
attested; even then, the loop stays AX/window-first and permits only one fresh,
target-contained desktop action after the window delivery ladder is exhausted:
  - before the task is bound to an app, each step observes a TEXT snapshot of
    running apps/windows (get_accessibility_tree: name/bundle_id/pid JSON);
  - once bound, each step observes the bound app's WINDOW via get_window_state,
    which returns BOTH the UI element tree (element_index handles for click/
    type_text/press_key) and a window-local PNG screenshot;
  - drivers without get_window_state (offline test fakes, other MCP servers)
    fall back to the legacy single "screenshot"/"capture" tool loop.
Coordinate contract: window pixel actions (click x/y) use the SAME pixel space
as the get_window_state PNG, so the resize ratio converts model coordinates
back exactly; element_index/element_token calls carry no coordinates and are
passed through untouched.

Stop contract: the parent writes the cancel file, then waits a grace window
before escalating to SIGTERM/SIGKILL. This worker polls the cancel file every
second (a dedicated watcher task racing the agent loop), so a stop request is
answered with a proper `cancelled` result — including salvaged evidence —
within a couple of seconds, well inside the parent's grace window.

Salvage contract: every ending (finish / no-more-calls / max-steps / overall
time limit / error / cancel) reports the evidence collected so far — executed
actions, visited applications, model narratives, and the last screenshot saved
to disk. Time-limit/error/cancel endings additionally mark metadata partial=True.
"""

from __future__ import annotations

import asyncio
import base64
import copy
import hashlib
import io
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any
import uuid

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from openai import OpenAI
from PIL import Image

try:
    import computer_use_experience as _experience
except Exception:  # a frozen build without the module keeps working rule-less
    _experience = None


RESULT_PREFIX = "__BROCCOLI_COMPUTER_USE_RESULT__"
PROGRESS_PREFIX = "__BROCCOLI_COMPUTER_USE_PROGRESS__"
INSTALL_COMMAND = '/bin/bash -c "$(curl -fsSL https://cua.ai/driver/install.sh)"'
WINDOW_OBSERVE_TOOL = "get_window_state"
APPS_OBSERVE_TOOLS = ("list_apps", "get_accessibility_tree")
WINDOW_OBSERVE_MAX_ELEMENTS = 400
TREE_TEXT_LIMIT = 8000
MODEL_ELEMENTS_TEXT_LIMIT = 12000
APPS_TEXT_LIMIT = 4000
# Conservative tool classifier, checked against the real cua-driver 0.8.3 tool
# list on 2026-07-18: any mutating token anywhere in the name wins; otherwise a
# tool is read-only ONLY when its FIRST token is a known observational verb.
# Unknown shapes default to state-changing (they then need an explicit target
# or get refused — 宁可少能力，不可失控).
READ_ONLY_FIRST_TOKENS = {
    "screenshot", "capture", "get", "list", "read", "describe", "inspect",
    "query", "status", "snapshot", "observe", "find", "search",
}
MUTATING_TOKENS = {
    "click", "type", "key", "keys", "press", "scroll", "drag", "drop", "move",
    "write", "set", "input", "tap", "swipe", "paste", "close", "open", "launch",
    "quit", "kill", "focus", "activate", "select", "delete", "create", "send",
    "hotkey", "shortcut", "run", "exec", "execute", "install", "edit", "resize",
}
TARGET_KEYS = (
    "bundle_id", "application", "application_name", "app", "app_name",
    "process_name", "pid", "window_id", "target_app",
)
COORDINATE_KEYS = {"x", "y", "start_x", "start_y", "end_x", "end_y", "from_x", "from_y", "to_x", "to_y"}
ELEMENT_ADDRESS_KEYS = ("element_index", "element_token")
SESSION_KEYS = ("session", "session_id", "sessionId")
DISPLAY_SELECTOR_KEYS = (
    "display_id", "screen_id", "monitor_id", "display_index", "screen_index", "monitor_index",
)
PIXEL_ADDRESS_MODES = {"window_pixel", "desktop_pixel"}
GEOMETRY_ALIGNED = "ALIGNED"
GEOMETRY_STAGE_TRANSFORMED = "STAGE_TRANSFORMED"
GEOMETRY_AMBIGUOUS = "AMBIGUOUS"
GEOMETRY_OFFSCREEN = "OFFSCREEN_OR_MINIMIZED"
GEOMETRY_LEGACY = "LEGACY_SCREENSHOT"
EFFECT_CONFIRMED = "CONFIRMED"
EFFECT_CONFIRMED_DOWNSTREAM = "CONFIRMED_BY_DOWNSTREAM"
EFFECT_PENDING = "PENDING"
EFFECT_ABSENT = "EFFECT_ABSENT"
EFFECT_INDETERMINATE = "INDETERMINATE"
EFFECT_NOT_DELIVERED = "NOT_DELIVERED"
EFFECT_SUPERSEDED = "SUPERSEDED_BY_CONFIRMED_RETRY"
DELIVERY_NOT_ATTEMPTED = "NOT_ATTEMPTED"
DELIVERY_DELIVERED_UNVERIFIED = "DELIVERED_UNVERIFIED"
DELIVERY_DRIVER_ERROR = "DRIVER_ERROR"
DELIVERY_UNKNOWN_AFTER_ATTEMPT = "UNKNOWN_AFTER_ATTEMPT"
WORKER_OWNED_TOOLS = {
    "check_permissions", "health_report", "start_session", "end_session",
    "get_accessibility_tree", "list_apps", "list_windows", "get_window_state",
    "get_desktop_state", "get_screen_size", "get_cursor_position",
    "get_agent_cursor_state", "get_config", "get_recording_state",
    "check_for_update", "zoom", "screenshot", "capture",
    "start_recording", "stop_recording", "replay_trajectory", "install_ffmpeg",
    "set_config", "set_agent_cursor_enabled", "set_agent_cursor_motion",
    "set_agent_cursor_style", "move_cursor",
}
# cua-driver 0.35 composite/meta tools. Each runs several actions, arbitrary
# script, an install, or a capture parse inside ONE driver call, out of reach of
# the worker's per-action target binding and effect verification. They are
# never offered to the model, and a model call is refused like a worker-owned tool.
MODEL_BLOCKED_DRIVER_TOOLS = {"run_script", "run_steps", "install_extension", "parse_visual_regions"}
APP_BIND_TOOLS = {"launch_app"}
PERSISTENT_FOREGROUND_TOOLS = {"bring_to_front", "open_app", "activate_app", "focus_app"}
APP_SWITCH_TOOLS = APP_BIND_TOOLS | PERSISTENT_FOREGROUND_TOOLS
SYNTHETIC_TRANSFER_TOOLS = {"capture_ax_text", "insert_captured_text"}
VISIBLE_ACTION_TOKENS = {
    "click", "type", "key", "keys", "press", "scroll", "drag", "drop",
    "write", "set", "input", "tap", "swipe", "paste", "select", "delete", "edit",
}


def _emit(prefix: str, payload: dict) -> None:
    print(prefix + json.dumps(payload, ensure_ascii=False), flush=True)


def _emit_result(payload: dict) -> None:
    _emit(RESULT_PREFIX, payload)


def _emit_progress(payload: dict) -> None:
    _emit(PROGRESS_PREFIX, payload)


def _positive_int(value: Any, default: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return parsed if parsed > 0 else default


def _cancelled(config: dict) -> bool:
    path = str(config.get("cancel_path", "") or "").strip()
    return bool(path and os.path.exists(path))


def _driver_error() -> str:
    return (
        "CuaDriver is unavailable. Install it with the official command:\n"
        f"{INSTALL_COMMAND}\n\n"
        "After installation, grant CuaDriver both Accessibility and Screen Recording "
        "permissions in System Settings. Broccoli never runs the installer for you."
    )


def _new_evidence() -> dict:
    """Mutable evidence container shared across the whole worker lifetime so
    that timeout / error / cancel endings can salvage what was collected."""
    return {
        "actions": [],
        "visited_targets": [],
        "narratives": [],
        "latest_original": b"",
        "latest_fingerprint": "",
        "latest_window": {},
        "driver_session": "",
        "failure_source": "",
        "display_policy": {},
        "desktop_isolation": {},
    }


def _save_actions_log(config: dict, evidence: dict) -> str:
    """Persist the per-action driver responses next to the final screenshot.
    Forensics on 2026-07-18 found the in-memory actions array is dropped by the
    step archive, leaving failed runs undiagnosable from disk — this file is
    the durable record of what every click/type actually returned."""
    base = str((config or {}).get("final_screenshot", "") or "")
    if not base:
        return ""
    try:
        target = Path(base).expanduser().with_suffix(".actions.json")
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps({
            "task": str((config or {}).get("task", "") or ""),
            "driver_session": str(evidence.get("driver_session", "") or ""),
            "display_policy": _json_safe(evidence.get("display_policy") or {}),
            "desktop_isolation": _json_safe(evidence.get("desktop_isolation") or {}),
            "actions": list(evidence.get("actions") or []),
            "effect_report": _effect_report(list(evidence.get("actions") or [])),
            "visited_targets": list(evidence.get("visited_targets") or []),
            "narratives": list(evidence.get("narratives") or []),
        }, ensure_ascii=False, indent=1), encoding="utf-8")
        return str(target)
    except Exception:
        return ""


def _salvage_metadata(
        config: dict, evidence: dict, partial: bool = False, failure_source: str = "") -> dict:
    final_path = _save_final_screenshot(
        str((config or {}).get("final_screenshot", "") or ""),
        evidence.get("latest_original") or b"",
    )
    effect_report = _effect_report(list(evidence.get("actions") or []))
    metadata = {
        "actions": list(evidence.get("actions") or []),
        "visited_targets": list(evidence.get("visited_targets") or []),
        "narratives": list(evidence.get("narratives") or []),
        "final_screenshot": final_path,
        "actions_log": _save_actions_log(config, evidence),
        "driver_session": str(evidence.get("driver_session", "") or ""),
        "failure_source": str(failure_source or evidence.get("failure_source", "") or ""),
        "display_policy": _json_safe(evidence.get("display_policy") or {}),
        "desktop_isolation": _json_safe(evidence.get("desktop_isolation") or {}),
        "effect_report": effect_report,
        "experience_candidates": _json_safe(list(evidence.get("experience_candidates") or [])),
    }
    if partial or effect_report.get("partial"):
        metadata["partial"] = True
    return metadata


def _last_narrative(evidence: dict) -> str:
    narratives = evidence.get("narratives") or []
    return str(narratives[-1]) if narratives else ""


def _flatten_error(exc: BaseException) -> str:
    """anyio task groups (inside the MCP client) wrap body exceptions into
    ExceptionGroup, whose str() is 'unhandled errors in a TaskGroup (...)'.
    Dig out the leaf messages so availability errors (401/429/5xx) stay
    visible to the parent process's model-failover classifier."""
    seen: list[str] = []

    def walk(error: BaseException) -> None:
        if isinstance(error, BaseExceptionGroup):
            for sub in error.exceptions:
                walk(sub)
            return
        text = str(error).strip() or error.__class__.__name__
        if text not in seen:
            seen.append(text)

    walk(exc)
    return "; ".join(seen) if seen else str(exc)


async def _call_in_daemon_thread(func, *args):
    """Run a blocking call on a DAEMON thread so that cancelling the awaiting
    task never blocks worker exit. asyncio.to_thread is unsuitable here: the
    default executor is joined by asyncio.run() on shutdown, which would make a
    cancelled 120s model call delay process exit far past the stop deadline."""
    loop = asyncio.get_running_loop()
    future = loop.create_future()

    def _deliver(setter):
        def _apply():
            if not future.done():
                setter()
        try:
            loop.call_soon_threadsafe(_apply)
        except RuntimeError:
            pass

    def _runner():
        try:
            value = func(*args)
        except BaseException as exc:  # noqa: BLE001 - forwarded to the awaiting task
            # Rebind before closing over it: Python unbinds `exc` when the except
            # block exits, but the lambda runs later on the event loop.
            # asyncio.Future rejects StopIteration/StopAsyncIteration as their
            # semantics collide with coroutine termination. Normalize them so
            # a malformed/exhausted callback becomes an ordinary worker error
            # instead of leaving the Future pending until the LLM timeout.
            if isinstance(exc, (StopIteration, StopAsyncIteration)):
                error = RuntimeError(
                    f"{exc.__class__.__name__}: {str(exc).strip() or 'callback exhausted'}"
                )
            else:
                error = exc
            _deliver(lambda: future.set_exception(error))
        else:
            _deliver(lambda: future.set_result(value))

    threading.Thread(target=_runner, daemon=True).start()
    return await future


def _ensure_driver_daemon(driver_command: str) -> None:
    """Probe the standalone daemon; launch CuaDriver.app when it is not reachable.

    确认清单 1 (2026-07-18, cua-driver 0.8.3): `status` and `mcp` are real CLI
    subcommands and the stdio transport works — confirmed on the installed
    driver. `open` is used WITHOUT -n on purpose — a fresh probe failure must
    not stack a second CuaDriver instance next to one already running.
    """
    try:
        probe = subprocess.run(
            [driver_command, "status"], capture_output=True, text=True, timeout=4,
        )
        if probe.returncode == 0:
            return
    except Exception:
        pass
    if sys.platform == "darwin" and Path("/Applications/CuaDriver.app").exists():
        try:
            subprocess.Popen(
                ["/usr/bin/open", "-g", "-a", "CuaDriver", "--args", "serve"],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            )
        except Exception:
            return
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            try:
                probe = subprocess.run(
                    [driver_command, "status"], capture_output=True, text=True, timeout=2,
                )
                if probe.returncode == 0:
                    return
            except Exception:
                pass
            time.sleep(0.5)


def _tool_dict(tool: Any) -> dict:
    if hasattr(tool, "model_dump"):
        data = tool.model_dump(by_alias=True)
    elif isinstance(tool, dict):
        data = dict(tool)
    else:
        data = {
            "name": getattr(tool, "name", ""),
            "description": getattr(tool, "description", ""),
            "inputSchema": getattr(tool, "inputSchema", {}),
        }
    return {
        "name": str(data.get("name", "") or ""),
        "description": str(data.get("description", "") or ""),
        "inputSchema": data.get("inputSchema") or data.get("input_schema") or {"type": "object"},
    }


def _schema_properties(schema: dict) -> dict:
    properties = schema.get("properties") if isinstance(schema, dict) else {}
    return properties if isinstance(properties, dict) else {}


def _with_driver_session(arguments: dict, schema: dict, driver_session: str) -> dict:
    """Give every supporting driver call the task's private session identity.

    Model-provided session values are deliberately overwritten: one worker run
    owns one driver cursor/cache namespace, so a prompt cannot accidentally
    reuse another task's element cache.
    """
    prepared = dict(arguments or {})
    properties = _schema_properties(schema)
    for key in SESSION_KEYS:
        if key in properties:
            prepared[key] = driver_session
    return prepared


def _model_input_schema(schema: dict) -> dict:
    """Hide worker-owned session arguments from the model-facing schema."""
    cleaned = copy.deepcopy(schema if isinstance(schema, dict) else {"type": "object"})
    properties = cleaned.get("properties")
    if isinstance(properties, dict):
        for key in SESSION_KEYS:
            properties.pop(key, None)
    required = cleaned.get("required")
    if isinstance(required, list):
        cleaned["required"] = [key for key in required if key not in SESSION_KEYS]
    return cleaned


def _worker_owned_tool(name: str) -> bool:
    lowered = str(name or "").lower()
    if lowered in SYNTHETIC_TRANSFER_TOOLS:
        return False
    return lowered in WORKER_OWNED_TOOLS or lowered in MODEL_BLOCKED_DRIVER_TOOLS or _is_read_only(lowered)


def _name_tokens(name: str) -> list[str]:
    return [token for token in re.split(r"[^a-z0-9]+", str(name or "").lower()) if token]


def _is_read_only(name: str) -> bool:
    tokens = _name_tokens(name)
    if not tokens:
        return False
    if any(token in MUTATING_TOKENS for token in tokens):
        return False
    return tokens[0] in READ_ONLY_FIRST_TOKENS


def _schema_target_keys(schema: dict) -> list[str]:
    properties = schema.get("properties") if isinstance(schema, dict) else {}
    if not isinstance(properties, dict):
        return []
    return [key for key in TARGET_KEYS if key in properties]


def _target_identity(arguments: dict, schema: dict) -> str:
    for key in _schema_target_keys(schema):
        value = arguments.get(key)
        if value not in (None, ""):
            return f"{key}:{value}"
    return ""


def _fill_target_from_bound_token(
        arguments: dict, address_mode: str, schema: dict,
        elements: list[dict], window_context: dict) -> tuple[dict, list[str]]:
    """Supply pid/window_id for a token-addressed action on the bound window.

    cua-driver 0.35 documents pid as optional with element_token ("it carries
    the pid"), so models omit the target and guard_action refuses the call. A
    token naming an element of the current fresh observation identifies exactly
    the bound window; filling its pid/window_id lets guard_action run its normal
    checks on that target. A token outside that observation, or an action that
    names any other target, is returned unchanged for guard_action to judge.
    """
    if address_mode != "element_ax" or not isinstance(arguments, dict):
        return arguments, []
    token = str(arguments.get("element_token", "") or "").strip()
    if not token:
        return arguments, []
    if any(arguments.get(key) not in (None, "") for key in TARGET_KEYS if key != "window_id"):
        return arguments, []
    context = window_context if isinstance(window_context, dict) else {}
    pid = context.get("pid")
    window_id = context.get("window_id")
    if pid is None or window_id is None:
        return arguments, []
    given_window = arguments.get("window_id")
    if given_window not in (None, "") and str(given_window) != str(window_id):
        return arguments, []
    if not any(
            isinstance(item, dict) and str(item.get("element_token", "") or "") == token
            for item in elements or []):
        return arguments, []
    properties = _schema_properties(schema)
    filled = dict(arguments)
    added = []
    for key, value in (("pid", pid), ("window_id", window_id)):
        if key in properties and filled.get(key) in (None, ""):
            filled[key] = int(value)
            added.append(key)
    return filled, added


def _is_broccoli_text(value: str) -> bool:
    lowered = str(value or "").lower()
    return "broccoli" in lowered


def guard_action(name: str, arguments: dict, schema: dict, bound_identities) -> tuple[str, str, str]:
    """Return (verdict, identity, reason). verdict:
    'allow'   — execute now (read-only, first bind, or already-bound identity);
    'refuse'  — never execute (no target / Broccoli / unresolvable);
    'resolve' — state-changing call on a NEW identity while already bound; the
                caller must prove same-app or perform an explicit, freshly
                grounded application switch inside the approved task."""
    lowered = str(name or "").lower()
    if lowered in PERSISTENT_FOREGROUND_TOOLS:
        return (
            "refuse", "",
            "CU_PERSISTENT_FOREGROUND_NOT_AUTHORIZED: persistent app activation is not part of "
            "the normal input ladder. Use background delivery first and an exact one-shot "
            "delivery_mode='foreground' retry only after a verified no-effect result.",
        )
    if lowered not in SYNTHETIC_TRANSFER_TOOLS and _is_read_only(name):
        return "allow", "", ""
    identity = _target_identity(arguments, schema)
    if not identity:
        return "refuse", "", "State-changing tool has no explicit app/window target; phase 1 refused it."
    if _is_broccoli_text(identity):
        return "refuse", identity, "Operating Broccoli itself is forbidden to prevent a feedback loop."
    bound = set(bound_identities or ())
    if not bound or identity in bound:
        return "allow", identity, ""
    return "resolve", identity, ""


def scale_coordinates(arguments: dict, ratio: float) -> dict:
    """Model coordinates use the resized screenshot; the driver's pixel actions
    use the ORIGINAL pixels of that same PNG (window-local for get_window_state,
    full-image for the legacy screenshot mode) — confirmed against cua-driver
    0.8.3's click/drag docs on 2026-07-18. Element-addressed calls
    (element_index / element_token) carry no meaningful coordinates and pass
    through untouched."""
    if not isinstance(arguments, dict):
        return dict(arguments or {})
    if any(key in arguments for key in ELEMENT_ADDRESS_KEYS):
        return dict(arguments)
    if ratio <= 0 or ratio == 1:
        return dict(arguments)
    converted = dict(arguments)
    for key in COORDINATE_KEYS:
        value = converted.get(key)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            converted[key] = round(value / ratio)
    return converted


def _policy_error(code: str, message: str, **evidence: Any) -> dict:
    """Stable, machine-readable refusal used by routing, geometry and display guards."""
    return {
        "code": str(code),
        "stage": str(evidence.pop("stage", "address")),
        "retriable": bool(evidence.pop("retriable", False)),
        "message": str(message),
        "evidence": _json_safe(evidence),
    }


def _finite_number(value: Any) -> float | None:
    if isinstance(value, bool):
        return None
    try:
        parsed = float(value)
    except (TypeError, ValueError):
        return None
    return parsed if math.isfinite(parsed) else None


def _canonical_identity_value(value: Any) -> Any:
    """Normalize equivalent numeric PID/window identity representations."""
    if isinstance(value, bool):
        return str(value).lower()
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError):
        return str(value or "").strip()


def _canonical_target_identity(identity: str) -> str:
    key, separator, value = str(identity or "").partition(":")
    if separator and key in {"pid", "window_id"}:
        return f"{key}:{_canonical_identity_value(value)}"
    return str(identity or "")


def _rect(value: Any) -> dict | None:
    if not isinstance(value, dict):
        return None
    x = _finite_number(value.get("x"))
    y = _finite_number(value.get("y"))
    width = _finite_number(value.get("width", value.get("w")))
    height = _finite_number(value.get("height", value.get("h")))
    if None in (x, y, width, height) or width <= 0 or height <= 0:
        return None
    return {"x": x, "y": y, "width": width, "height": height}


def _agent_cursor_target(
        action_arguments: dict, current_elements: list[dict],
        display_inventory: list[dict], target_display_policy: dict) -> dict:
    """Resolve a truthful overlay position without participating in delivery.

    The agent cursor is presentation-only.  Hidden/Stage/off-Space AX elements
    often have no drawable screen frame even though their AX action remains
    perfectly addressable.  Such cases return evidence instead of raising.
    """
    action_arguments = action_arguments if isinstance(action_arguments, dict) else {}
    token = str(action_arguments.get("element_token", "") or "").strip()
    wanted_index = action_arguments.get("element_index")
    matched_element = None
    for item in current_elements or []:
        if not isinstance(item, dict):
            continue
        if token and str(item.get("element_token", "") or "") == token:
            matched_element = item
            break
        if not token and wanted_index is not None:
            try:
                if int(item.get("element_index")) == int(wanted_index):
                    matched_element = item
                    break
            except (TypeError, ValueError):
                continue
    frame = _rect((matched_element or {}).get("frame"))
    base = {
        "available": False,
        "mode": "worker_owned_overlay",
        "target_frame": _json_safe(frame or {}),
        "requested_position": {},
        "real_pointer_moved": False,
        "action_continued": True,
    }
    if frame is None or frame["height"] <= 1 or frame["width"] <= 1:
        return {**base, "reason": "no_drawable_frame"}
    point = {
        "x": frame["x"] + frame["width"] / 2.0,
        "y": frame["y"] + frame["height"] / 2.0,
    }
    candidate_displays = display_inventory
    if str((target_display_policy or {}).get("mode", "auto")) == "display":
        candidate_displays = [dict((target_display_policy or {}).get("display") or {})]
    if candidate_displays:
        grounded = any(
            (bounds := _rect(display.get("bounds") if isinstance(display, dict) else None)) is not None
            and bounds["x"] <= point["x"] < bounds["x"] + bounds["width"]
            and bounds["y"] <= point["y"] < bounds["y"] + bounds["height"]
            for display in candidate_displays
        )
        if not grounded:
            return {
                **base,
                "reason": "outside_selected_display",
                "requested_position": _json_safe(point),
            }
    return {
        **base,
        "available": True,
        "reason": "",
        "requested_position": _json_safe(point),
    }


def _is_transition_auxiliary_window(item: dict) -> bool:
    """Identify the tiny off-screen helper surfaces emitted during transitions.

    Stage Manager and launch animations can briefly expose a very thin Quartz
    window ahead of the real application window.  It is not safe to bind the
    task, AX tree, or pixel geometry to that helper.  A real on-screen strip or
    an explicit dialog/sheet remains eligible.
    """
    if not isinstance(item, dict) or item.get("is_on_screen") is not False:
        return False
    role_text = " ".join(str(item.get(key, "") or "") for key in ("role", "subrole")).lower()
    modal_or_panel = bool(
        _is_modal_window(item)
        or any(marker in role_text for marker in ("panel", "popover"))
    )
    bounds = _rect(item.get("bounds"))
    ratio = 0.0
    if bounds is not None:
        shorter = min(bounds["width"], bounds["height"])
        longer = max(bounds["width"], bounds["height"])
        ratio = longer / max(shorter, 1.0)
    return bool(
        bounds is not None
        and min(bounds["width"], bounds["height"]) <= 32
        and ratio >= 8.0
        and not str(item.get("title", "") or "").strip()
        and not modal_or_panel
    )


ACCESSORY_WINDOW_MAX_SIDE = 64.0


def _is_accessory_window(item: dict) -> bool:
    """An untitled, non-modal surface too small to hold app content.

    Some apps own an icon-sized companion window (e.g. a 46x42 assistant orb)
    one z-level above the real document window; ranking by z-order alone binds
    the task to it. It stays eligible only when no other window is.
    """
    if not isinstance(item, dict) or _is_modal_window(item):
        return False
    if str(item.get("title", "") or "").strip():
        return False
    bounds = _rect(item.get("bounds"))
    return bool(
        bounds is not None
        and max(bounds["width"], bounds["height"]) <= ACCESSORY_WINDOW_MAX_SIDE
    )


def _is_modal_window(item: dict) -> bool:
    if not isinstance(item, dict):
        return False
    role_text = " ".join(
        str(item.get(key, "") or "") for key in ("role", "subrole")
    ).replace("_", "").lower()
    return bool(
        item.get("is_modal") is True or item.get("modal") is True
        or "dialog" in role_text or "sheet" in role_text
    )


def _explicit_display_ax_only(
        name: str, address_mode: str, window_context: dict,
        target_display_policy: dict) -> tuple[bool, dict]:
    """Fail closed to true AX actions when the app is on another display."""
    explicit_mismatch = bool(
        str((target_display_policy or {}).get("mode", "auto")) == "display"
        and isinstance(window_context, dict)
        and window_context
        and window_context.get("display_policy_match") is not True
    )
    if not explicit_mismatch:
        return True, {}
    lowered = str(name or "").lower()
    allowed = str(address_mode or "") in {"element_ax", "topology"} \
        or lowered == "capture_ax_text" \
        or lowered in APP_SWITCH_TOOLS
    return allowed, {
        "selected_display": _json_safe((target_display_policy or {}).get("display") or {}),
        "window_display": _json_safe((window_context or {}).get("display_assignment") or {}),
        "allowed_surface": "background AX only",
    }


def _window_pixel_points_on_selected_display(
        arguments: dict, window_context: dict,
        target_display_policy: dict) -> tuple[bool, dict]:
    """Prove every window-local pixel endpoint lands on the selected display."""
    if str((target_display_policy or {}).get("mode", "auto")) != "display":
        return True, {}
    display = (target_display_policy or {}).get("display")
    selected = _rect(display.get("bounds") if isinstance(display, dict) else None)
    geometry = (window_context or {}).get("geometry")
    geometry = geometry if isinstance(geometry, dict) else {}
    window = _rect(geometry.get("cg_bounds")) or _rect((window_context or {}).get("bounds"))
    image_size = geometry.get("image_size") if isinstance(geometry.get("image_size"), list) else []
    try:
        image_width, image_height = float(image_size[0]), float(image_size[1])
    except (IndexError, TypeError, ValueError):
        image_width, image_height = 0.0, 0.0
    if selected is None or window is None or image_width <= 0 or image_height <= 0:
        return False, {"reason": "selected-display/window image geometry is incomplete"}
    pairs = []
    for x_key, y_key in (
            ("x", "y"), ("start_x", "start_y"), ("end_x", "end_y"),
            ("from_x", "from_y"), ("to_x", "to_y")):
        x_value = _finite_number((arguments or {}).get(x_key))
        y_value = _finite_number((arguments or {}).get(y_key))
        if x_value is None or y_value is None:
            continue
        screen_x = window["x"] + x_value * window["width"] / image_width
        screen_y = window["y"] + y_value * window["height"] / image_height
        inside = bool(
            selected["x"] <= screen_x < selected["x"] + selected["width"]
            and selected["y"] <= screen_y < selected["y"] + selected["height"]
        )
        pairs.append({
            "keys": [x_key, y_key],
            "window_image": {"x": x_value, "y": y_value},
            "screen": {"x": round(screen_x, 3), "y": round(screen_y, 3)},
            "inside_selected_display": inside,
        })
    return bool(pairs) and all(item["inside_selected_display"] for item in pairs), {
        "points": pairs,
        "selected_display_bounds": _json_safe(selected),
        "window_bounds": _json_safe(window),
        "window_image_size": [image_width, image_height],
    }


def _ax_window_frame(elements: list[dict]) -> dict | None:
    """Return the largest root-ish AXWindow/AXDialog frame from a fresh tree."""
    candidates: list[tuple[tuple[int, float], dict]] = []
    for item in elements or []:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "") or "").replace("_", "").lower()
        if role not in {"axwindow", "window", "axdialog", "dialog", "axsheet", "sheet"}:
            continue
        frame = _rect(item.get("frame"))
        if frame is None:
            continue
        try:
            depth = int(item.get("depth", 99))
        except (TypeError, ValueError):
            depth = 99
        area = frame["width"] * frame["height"]
        candidates.append(((-depth, area), frame))
    if not candidates:
        return None
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    return candidates[0][1]


def _image_dimensions(image_bytes: bytes) -> tuple[int, int]:
    if not image_bytes:
        return (0, 0)
    try:
        with Image.open(io.BytesIO(image_bytes)) as source:
            return tuple(int(value) for value in source.size)
    except Exception:
        return (0, 0)


def _classify_window_geometry(
        cg_bounds: Any, elements: list[dict], image_size: tuple[int, int],
        is_on_screen: Any = None, on_current_space: Any = None) -> dict:
    """Cross-check the Quartz window used for the PNG with the AX root window.

    Stage Manager shelf thumbnails keep the same CG window id while exposing a
    tiny compositor rectangle and the full underlying AXWindow frame. Pixel
    conversion is unsafe in that state; AX addressing remains valid.
    """
    cg = _rect(cg_bounds)
    ax = _ax_window_frame(elements)
    result = {
        "classification": GEOMETRY_AMBIGUOUS,
        "pixel_safe": False,
        "cg_bounds": _json_safe(cg or {}),
        "ax_frame": _json_safe(ax or {}),
        "image_size": [int(image_size[0]), int(image_size[1])],
        "reason": "CG/AX geometry could not be closed.",
        "metrics": {},
    }
    if is_on_screen is not True or on_current_space is False \
            or cg is None or cg["width"] < 2 or cg["height"] < 2:
        result.update({
            "classification": GEOMETRY_OFFSCREEN,
            "reason": (
                "The selected CG window is off-screen, off-Space, hidden, minimized, has unknown "
                "visibility, or has invalid bounds."
            ),
        })
        return result
    if ax is None:
        result["reason"] = "The fresh accessibility snapshot did not expose an AXWindow frame."
        return result

    size_err = max(
        abs(ax["width"] - cg["width"]) / max(ax["width"], cg["width"]),
        abs(ax["height"] - cg["height"]) / max(ax["height"], cg["height"]),
    )
    origin_err = math.hypot(ax["x"] - cg["x"], ax["y"] - cg["y"])
    origin_tolerance = max(4.0, 0.01 * math.hypot(ax["width"], ax["height"]))
    cg_area = cg["width"] * cg["height"]
    ax_area = ax["width"] * ax["height"]
    area_ratio = min(cg_area, ax_area) / max(cg_area, ax_area)
    scale_x = image_size[0] / cg["width"] if image_size[0] > 0 else 0.0
    scale_y = image_size[1] / cg["height"] if image_size[1] > 0 else 0.0
    anisotropy = (
        abs(scale_x - scale_y) / max(scale_x, scale_y)
        if scale_x > 0 and scale_y > 0 else None
    )
    result["metrics"] = {
        "size_error": round(size_err, 6),
        "origin_error": round(origin_err, 3),
        "origin_tolerance": round(origin_tolerance, 3),
        "area_ratio": round(area_ratio, 6),
        "png_scale_x": round(scale_x, 6),
        "png_scale_y": round(scale_y, 6),
        "png_anisotropy": round(anisotropy, 6) if anisotropy is not None else None,
    }
    image_valid = image_size[0] > 0 and image_size[1] > 0
    image_isotropic = anisotropy is not None and anisotropy <= 0.02
    if size_err <= 0.03 and origin_err <= origin_tolerance and image_valid and image_isotropic:
        result.update({
            "classification": GEOMETRY_ALIGNED,
            "pixel_safe": True,
            "reason": "CG bounds and the AXWindow frame are aligned.",
        })
    elif size_err > 0.15 or area_ratio < 0.70:
        result.update({
            "classification": GEOMETRY_STAGE_TRANSFORMED,
            "reason": (
                "CG bounds describe a compositor thumbnail while AX exposes a materially different "
                "window frame (Stage Manager transformation suspected)."
            ),
        })
    else:
        result["reason"] = (
            "CG/AX/PNG geometry is incomplete or differs beyond the safe pixel tolerance."
        )
    return result


def _geometry_signature(window_context: dict) -> tuple:
    geometry = window_context.get("geometry") if isinstance(window_context, dict) else {}
    if not isinstance(geometry, dict):
        geometry = {}

    def rect_signature(value: Any) -> tuple:
        parsed = _rect(value)
        if parsed is None:
            return ()
        return tuple(round(parsed[key], 2) for key in ("x", "y", "width", "height"))

    return (
        window_context.get("pid"), window_context.get("window_id"),
        geometry.get("classification"), rect_signature(geometry.get("cg_bounds")),
        rect_signature(geometry.get("ax_frame")), tuple(geometry.get("image_size") or ()),
    )


def _assign_window_to_display(cg_bounds: Any, displays: list[dict]) -> dict:
    """Assign a CG window to exactly one display by largest intersection.

    The driver 0.8.3 schema supplies no display list/id, so production callers
    may have an empty list and must keep desktop fallback unavailable. This
    pure helper nevertheless makes the filtering rule explicit and testable
    for a future safe display provider.
    """
    window = _rect(cg_bounds)
    if window is None:
        return {"status": "UNKNOWN", "display": None, "intersection_area": 0.0}
    candidates: list[tuple[float, dict]] = []
    for position, item in enumerate(displays or []):
        if not isinstance(item, dict):
            continue
        bounds = _rect(item.get("bounds", item))
        if bounds is None:
            continue
        left = max(window["x"], bounds["x"])
        top = max(window["y"], bounds["y"])
        right = min(window["x"] + window["width"], bounds["x"] + bounds["width"])
        bottom = min(window["y"] + window["height"], bounds["y"] + bounds["height"])
        area = max(0.0, right - left) * max(0.0, bottom - top)
        if area <= 0:
            continue
        normalized = dict(item)
        normalized.setdefault("display_index", position)
        candidates.append((area, normalized))
    if not candidates:
        return {"status": "OFFSCREEN", "display": None, "intersection_area": 0.0}
    candidates.sort(key=lambda pair: pair[0], reverse=True)
    best_area, best = candidates[0]
    tied = [item for area, item in candidates if abs(area - best_area) <= 1.0]
    if len(tied) > 1:
        return {
            "status": "AMBIGUOUS", "display": None,
            "intersection_area": round(best_area, 3),
            "candidates": _json_safe(tied),
        }
    return {
        "status": "ASSIGNED", "display": _json_safe(best),
        "intersection_area": round(best_area, 3),
        "is_main": bool(best.get("is_main") or best.get("main") or best.get("primary")),
    }


def _runtime_display_inventory(config: dict) -> list[dict]:
    """Re-enumerate displays in the worker; use main's snapshot only as fallback.

    The approval dialog can remain open while a monitor is unplugged or the
    desktop is rearranged. Main-process geometry is therefore descriptive,
    never runtime authority.
    """
    try:
        from computer_use_display import (  # local, Qt-free helper
            display_topology_signature,
            enumerate_displays,
        )
        live = [
            dict(item) for item in enumerate_displays()
            if isinstance(item, dict) and _rect(item.get("bounds"))
        ]
        if live:
            signature = display_topology_signature(live)
            for item in live:
                item["topology_signature"] = signature
            return live
    except Exception:
        pass
    if sys.platform == "darwin":
        # A stale approval-time snapshot cannot prove the current physical
        # topology. Losing live CoreGraphics enumeration therefore removes
        # display/desktop capability instead of silently trusting old bounds.
        return []
    provided = config.get("display_inventory") if isinstance(config, dict) else None
    if isinstance(provided, list):
        return [dict(item) for item in provided if isinstance(item, dict) and _rect(item.get("bounds"))]
    return []


def _target_display_policy(config: dict, inventory: list[dict]) -> dict:
    target = config.get("target_display") if isinstance(config, dict) else None
    if not isinstance(target, dict) or str(target.get("mode", "auto") or "auto").lower() == "auto":
        return {"mode": "auto"}
    stable_id = str(target.get("stable_id", "") or "").strip()
    bounds = _rect(target.get("bounds"))
    if not stable_id or bounds is None:
        return {
            "mode": "display", "valid": False, "stable_id": stable_id,
            "error": _policy_error(
                "CU_TARGET_DISPLAY_UNRESOLVED",
                "The explicit target display lacks a stable id or valid bounds.",
                stage="display",
            ),
        }
    matches = [
        item for item in inventory
        if str(item.get("stable_id", "") or "") == stable_id
    ]
    expected_topology = str(target.get("topology_signature", "") or "").strip()
    current_topologies = {
        str(item.get("topology_signature", "") or "").strip()
        for item in inventory if str(item.get("topology_signature", "") or "").strip()
    }
    if expected_topology and current_topologies != {expected_topology}:
        return {
            "mode": "display", "valid": False, "stable_id": stable_id,
            "error": _policy_error(
                "CU_DISPLAY_TOPOLOGY_CHANGED",
                "The display topology changed after task approval; re-approve against the current layout.",
                stage="display", stable_id=stable_id,
                expected_topology=expected_topology,
                current_topologies=sorted(current_topologies),
            ),
        }
    # Explicit display control requires a fresh inventory in the worker too.
    # Main's resolved bounds may be stale after hot-plug/rearrangement and must
    # never be treated as proof that the same physical display still exists.
    if len(matches) != 1:
        return {
            "mode": "display", "valid": False, "stable_id": stable_id,
            "error": _policy_error(
                "CU_TARGET_DISPLAY_UNRESOLVED",
                "The explicit target display is absent or ambiguous in the current topology.",
                stage="display", stable_id=stable_id, matches=len(matches),
            ),
        }
    resolved = dict(matches[0])
    resolved["bounds"] = _json_safe(_rect(resolved.get("bounds")) or bounds)
    resolved.setdefault("stable_id", stable_id)
    return {"mode": "display", "valid": True, "display": resolved}


def _display_matches_policy(assignment: dict, policy: dict) -> bool:
    if str(policy.get("mode", "auto")) == "auto":
        return True
    if not policy.get("valid") or assignment.get("status") != "ASSIGNED":
        return False
    actual = assignment.get("display") if isinstance(assignment.get("display"), dict) else {}
    wanted = policy.get("display") if isinstance(policy.get("display"), dict) else {}
    actual_id = str(actual.get("stable_id", "") or "")
    wanted_id = str(wanted.get("stable_id", "") or "")
    if actual_id and wanted_id:
        return actual_id == wanted_id
    return _assign_window_to_display(
        actual.get("bounds"), [wanted],
    ).get("status") == "ASSIGNED"


def _main_display_record(displays: list[dict], policy: dict | None = None) -> dict | None:
    if isinstance(policy, dict) and str(policy.get("mode", "auto")) == "display":
        selected = policy.get("display") if isinstance(policy.get("display"), dict) else {}
        if selected.get("is_main") is True and _rect(selected.get("bounds")) is not None:
            return dict(selected)
    mains = [
        dict(item) for item in displays or []
        if isinstance(item, dict) and item.get("is_main") is True
        and _rect(item.get("bounds")) is not None
    ]
    return mains[0] if len(mains) == 1 else None


def _desktop_owner_window_rects(
        payload: Any, pid: int, main_display: dict,
        window_id: int | None = None) -> list[dict]:
    payload = _unwrap_structured(payload)
    windows = payload.get("windows") if isinstance(payload, dict) else payload
    main = _rect(main_display.get("bounds") if isinstance(main_display, dict) else None)
    if main is None:
        return []
    result: list[dict] = []
    for item in windows if isinstance(windows, list) else []:
        if not isinstance(item, dict) or item.get("is_on_screen") is not True:
            continue
        try:
            if int(item.get("pid") or 0) != int(pid):
                continue
            if window_id is not None and int(item.get("window_id") or 0) != int(window_id):
                continue
        except (TypeError, ValueError):
            continue
        bounds = _rect(item.get("bounds"))
        if bounds is None:
            continue
        left = max(bounds["x"], main["x"])
        top = max(bounds["y"], main["y"])
        right = min(bounds["x"] + bounds["width"], main["x"] + main["width"])
        bottom = min(bounds["y"] + bounds["height"], main["y"] + main["height"])
        if right <= left or bottom <= top:
            continue
        result.append({
            "window_id": item.get("window_id"),
            "title": str(item.get("title", "") or ""),
            "bounds": {
                "x": left, "y": top,
                "width": right - left, "height": bottom - top,
            },
        })
    return result


def _desktop_coordinate_guard(arguments: dict, window_context: dict) -> tuple[bool, dict]:
    geometry = window_context.get("geometry") if isinstance(window_context, dict) else None
    geometry = geometry if isinstance(geometry, dict) else {}
    image_size = geometry.get("image_size") if isinstance(geometry.get("image_size"), list) else []
    try:
        image_width, image_height = float(image_size[0]), float(image_size[1])
    except (IndexError, TypeError, ValueError):
        return False, {"reason": "desktop image dimensions are unavailable"}
    main = _rect(window_context.get("main_display_bounds"))
    owner_windows = window_context.get("desktop_owner_windows")
    if main is None or image_width <= 0 or image_height <= 0 or not isinstance(owner_windows, list):
        return False, {"reason": "desktop/main-display owner geometry is unavailable"}
    owner_rects = [
        _rect(item.get("bounds")) for item in owner_windows if isinstance(item, dict)
    ]
    owner_rects = [item for item in owner_rects if item is not None]
    if not owner_rects:
        return False, {"reason": "the grounded process has no fresh visible main-display windows"}
    coordinate_groups = (
        ("x", "y"),
        ("start_x", "start_y"), ("end_x", "end_y"),
        ("from_x", "from_y"), ("to_x", "to_y"),
    )
    points: list[dict] = []
    for x_key, y_key in coordinate_groups:
        if x_key not in arguments and y_key not in arguments:
            continue
        px = _finite_number(arguments.get(x_key))
        py = _finite_number(arguments.get(y_key))
        if px is None or py is None:
            return False, {"reason": f"incomplete desktop coordinate pair {x_key}/{y_key}"}
        screen_x = main["x"] + px * main["width"] / image_width
        screen_y = main["y"] + py * main["height"] / image_height
        inside = any(
            rect["x"] <= screen_x < rect["x"] + rect["width"]
            and rect["y"] <= screen_y < rect["y"] + rect["height"]
            for rect in owner_rects
        )
        points.append({
            "image": {"x": px, "y": py},
            "screen": {"x": round(screen_x, 3), "y": round(screen_y, 3)},
            "inside_target": inside,
        })
    return bool(points) and all(item["inside_target"] for item in points), {
        "points": points,
        "owner_windows": _json_safe(owner_windows),
        "main_display_bounds": _json_safe(main),
        "image_size": [image_width, image_height],
    }


def _primary_display_selector(value: Any) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, (int, float)):
        return int(value) == 0
    return str(value or "").strip().lower() in {"0", "main", "primary", "main display"}


def _sanitize_action_arguments(
        name: str, arguments: dict, schema: dict,
        desktop_fallback: dict | None = None) -> tuple[dict, str, list[str], dict | None]:
    """Rebuild a mutually-exclusive driver payload from model arguments.

    0.8.3 exposes defaults for every click addressing field, and some models
    echo them all. In particular ``element_token:""`` + ``element_index:0``
    poisoned otherwise-valid x/y clicks in Notes. Empty/default element fields
    are routing noise, not an AX request.
    """
    original = dict(arguments or {})
    scope = str(original.get("scope", "") or "").strip().lower()
    selected = [(key, original.get(key)) for key in DISPLAY_SELECTOR_KEYS if key in original]
    if selected and any(not _primary_display_selector(value) for _key, value in selected):
        return {}, "desktop_pixel", [], _policy_error(
            "CU_SELECTED_DISPLAY_UNSUPPORTED_083",
            "cua-driver 0.8.3 has no display selector and its desktop capture is main-display only.",
            stage="display", selectors=dict(selected),
        )
    if scope == "desktop" or selected:
        fallback = desktop_fallback if isinstance(desktop_fallback, dict) else {}
        if fallback.get("target_is_main") is False:
            return {}, "desktop_pixel", [], _policy_error(
                "CU_SELECTED_DISPLAY_UNSUPPORTED_083",
                "cua-driver 0.8.3 desktop capture/click is limited to a proven main-display target.",
                stage="display", selectors=dict(selected),
            )
        if not all(fallback.get(key) is True for key in (
                "isolated_daemon", "private_home_verified", "force_proxy",
                "tcc_identity_verified", "capture_scope_desktop", "capture_verified")):
            return {}, "desktop_pixel", [], _policy_error(
                "CU_DESKTOP_SCOPE_NOT_ISOLATED",
                "Desktop fallback lacks the complete private-daemon isolation attestation.",
                stage="display", selectors=dict(selected), capture_scope="desktop",
            )
        if fallback.get("target_is_main") is not True:
            return {}, "desktop_pixel", [], _policy_error(
                "CU_SELECTED_DISPLAY_UNSUPPORTED_083",
                "cua-driver 0.8.3 desktop capture/click requires a target proven to belong to the main display.",
                stage="display", selectors=dict(selected),
            )
        if not fallback.get("authorized") or not str(fallback.get("fresh_snapshot_id", "") or ""):
            return {}, "desktop_pixel", [], _policy_error(
                "CU_DESKTOP_SNAPSHOT_REQUIRED",
                "Desktop input requires an explicit fallback transition and a fresh full-desktop snapshot.",
                stage="geometry", retriable=True,
            )

        properties = _schema_properties(schema)
        desktop_coordinates = any(
            all(_finite_number(original.get(key)) is not None for key in group)
            for group in (
                ("x", "y"),
                ("start_x", "start_y", "end_x", "end_y"),
                ("from_x", "from_y", "to_x", "to_y"),
            )
        )
        if "scope" not in properties or not desktop_coordinates:
            return {}, "desktop_pixel", [], _policy_error(
                "CU_DESKTOP_ACTION_UNSUPPORTED_083",
                "This 0.8.3 tool cannot express a coordinate-grounded scope='desktop' action.",
                stage="address",
            )
        cleaned = {
            key: value for key, value in original.items()
            if (not properties or key in properties) and key not in DISPLAY_SELECTOR_KEYS
        }
        dropped = [key for key in original if key not in cleaned]
        for key in (*ELEMENT_ADDRESS_KEYS, "from_zoom", "debug_image_out"):
            if key in cleaned:
                cleaned.pop(key, None)
                dropped.append(key)
        cleaned["scope"] = "desktop"
        return cleaned, "desktop_pixel", sorted(set(dropped)), None

    properties = _schema_properties(schema)
    cleaned = {
        key: value for key, value in original.items()
        if (not properties or key in properties) and key not in DISPLAY_SELECTOR_KEYS
    }
    dropped = [key for key in original if key not in cleaned]
    token_present = "element_token" in cleaned
    token = str(cleaned.get("element_token", "") or "").strip()
    index_value = cleaned.get("element_index")
    index_valid = _finite_number(index_value) is not None and int(float(index_value)) >= 0
    coordinate_groups = (
        ("x", "y"),
        ("start_x", "start_y", "end_x", "end_y"),
        ("from_x", "from_y", "to_x", "to_y"),
    )
    coordinates = any(
        all(_finite_number(cleaned.get(key)) is not None for key in group)
        for group in coordinate_groups
    )
    lowered = str(name or "").lower()
    key_action = lowered in {"hotkey", "shortcut", "press_key", "key", "press_keys"}
    key_supports_element = lowered in {"press_key", "key", "press_keys"}
    if lowered in APP_SWITCH_TOOLS:
        address_mode = "topology"
    elif key_action and key_supports_element and token:
        # CuaDriver press_key can first focus one fresh AX element and then
        # deliver the key event in the background.  Keep that official
        # addressing path instead of silently stripping its focus target.
        address_mode = "element_ax"
    elif key_action and key_supports_element and index_valid and not (
            token_present and not token and coordinates
            and int(float(index_value)) == 0):
        # A real AX index wins over echoed x/y.  The one exception is the
        # known empty-token + schema-default index=0 poison shape, where the
        # explicit coordinate pair is the only trustworthy address.
        address_mode = "element_ax"
    elif key_action and coordinates:
        # press_key and hotkey can both focus a window-local pixel before key
        # injection.  This path inherits the full geometry/display safeguards.
        address_mode = "window_pixel"
    elif key_action:
        address_mode = "key"
    elif token:
        address_mode = "element_ax"
    elif token_present and not token and coordinates and (
            not index_valid or int(float(index_value)) == 0):
        # Empty token plus x/y is the known 0.8.3 poison-pill shape. Treat the
        # token and schema-default index as absent and preserve the pixel intent.
        address_mode = "window_pixel"
    elif index_valid:
        address_mode = "element_ax"
    elif coordinates:
        address_mode = "window_pixel"
    else:
        address_mode = "direct"

    def discard(keys) -> None:
        for key in keys:
            if key in cleaned:
                cleaned.pop(key, None)
                if key not in dropped:
                    dropped.append(key)

    if address_mode == "element_ax":
        discard((*COORDINATE_KEYS, "scope", "from_zoom", "debug_image_out", "count"))
        if token:
            cleaned["element_token"] = token
            discard(("element_index",))
        else:
            discard(("element_token",))
    elif address_mode == "window_pixel":
        discard(ELEMENT_ADDRESS_KEYS)
        if cleaned.get("scope") in (None, "", "window"):
            discard(("scope",))
        if cleaned.get("from_zoom") is False:
            discard(("from_zoom",))
        if not str(cleaned.get("debug_image_out", "") or "").strip():
            discard(("debug_image_out",))
    elif address_mode in {"key", "topology", "direct"}:
        discard((*ELEMENT_ADDRESS_KEYS, *COORDINATE_KEYS, "scope", "from_zoom", "debug_image_out"))

    return cleaned, address_mode, sorted(set(dropped)), None


def _driver_payload_for_address_mode(arguments: dict, address_mode: str) -> dict:
    prepared = dict(arguments or {})
    if address_mode == "desktop_pixel":
        prepared.pop("pid", None)
        prepared.pop("window_id", None)
        prepared.pop("delivery_mode", None)
        prepared["scope"] = "desktop"
    return prepared


def _content_blocks(result: Any) -> list[dict]:
    content = getattr(result, "content", None)
    if content is None and isinstance(result, dict):
        content = result.get("content")
    blocks = []
    for item in content or []:
        if hasattr(item, "model_dump"):
            blocks.append(item.model_dump(by_alias=True))
        elif isinstance(item, dict):
            blocks.append(dict(item))
    return blocks


def _image_from_blocks(blocks: list[dict]) -> bytes:
    for block in blocks:
        if str(block.get("type", "")) == "image" and block.get("data"):
            return base64.b64decode(block["data"])
    return b""


def _text_from_blocks(blocks: list[dict]) -> str:
    return "\n".join(
        str(block.get("text", "") or "") for block in blocks if block.get("type") == "text"
    ).strip()


def _result_summary(result: Any) -> str:
    parts = []
    for block in _content_blocks(result):
        if block.get("type") == "text":
            parts.append(str(block.get("text", "") or ""))
        elif block.get("type") == "image":
            parts.append("[image returned]")
    summary = "\n".join(item for item in parts if item).strip()
    if not summary:
        structured = _structured_payload(result)
        if structured is not None:
            try:
                summary = json.dumps(_json_safe(structured), ensure_ascii=False)
            except Exception:
                summary = str(structured)
    if _result_is_error(result):
        return summary or "Driver returned isError=true."
    return summary or "Tool completed."


def _structured_payload(result: Any) -> Any:
    payload = getattr(result, "structuredContent", None)
    if payload is None:
        payload = getattr(result, "structured_content", None)
    if payload is not None:
        return payload
    text = _text_from_blocks(_content_blocks(result))
    if text:
        try:
            return json.loads(text)
        except Exception:
            return None
    return None


def _result_is_error(result: Any) -> bool:
    """MCP SDKs expose CallToolResult's error bit under either alias."""
    for key in ("isError", "is_error"):
        value = getattr(result, key, None)
        if value is None and isinstance(result, dict):
            value = result.get(key)
        if isinstance(value, str):
            value = value.strip().lower() in {"1", "true", "yes"}
        if value is not None:
            return bool(value)
    return False


def _fingerprint_basis(components: dict) -> str:
    """Evidence basis of an observation fingerprint, tolerant of old records."""
    if not isinstance(components, dict) or not components:
        return ""
    basis = str(components.get("basis", "") or "")
    if basis:
        return basis
    if str(components.get("raw_image_sha256", "") or ""):
        return "image+ax"
    return "ax_only"


def _json_safe(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump(by_alias=True))
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return repr(value)


def _log_content_blocks(result: Any) -> list[dict]:
    """Keep response evidence without duplicating base64 screenshots to JSON."""
    logged = []
    for block in _content_blocks(result):
        item = _json_safe(block)
        if isinstance(item, dict) and item.get("type") == "image":
            encoded = str(item.get("data", "") or "")
            item["data"] = "[image omitted from action log]"
            item["encoded_length"] = len(encoded)
        logged.append(item)
    return logged


def _driver_confirms_effect(result: Any) -> bool:
    if _result_is_error(result):
        return False
    # Effect confirmation is a privileged signal.  Accept it only from the
    # transport's explicit structured-content field, never from a text block
    # that merely happens to contain JSON or words such as "effect confirmed".
    # Text output is routinely an echo/debug summary and is not application
    # postcondition evidence.
    payload = getattr(result, "structuredContent", None)
    if payload is None:
        payload = getattr(result, "structured_content", None)
    if payload is None and isinstance(result, dict):
        payload = result.get("structuredContent")
        if payload is None:
            payload = result.get("structured_content")
    if payload is None:
        return False
    payload = _json_safe(payload)

    negative_effects = {
        "unverifiable", "suspected_noop", "suspectednoop", "no_effect",
        "noeffect", "not_confirmed", "notconfirmed", "failed", "failure",
        "rejected", "refused", "unknown",
    }

    def verdict(record: Any) -> bool | None:
        if not isinstance(record, dict):
            return None
        normalized = {
            str(key).replace("_", "").lower(): value
            for key, value in record.items()
        }
        effect = normalized.get("effect")
        explicit_negative = bool(
            normalized.get("verified") is False
            or normalized.get("effectconfirmed") is False
            or (
                isinstance(effect, str)
                and effect.strip().replace(" ", "_").lower() in negative_effects
            )
            or (
                isinstance(effect, dict)
                and (
                    effect.get("confirmed") is False
                    or effect.get("verified") is False
                )
            )
        )
        if explicit_negative:
            return False
        nested = record.get("result")
        nested_verdict = verdict(nested) if isinstance(nested, dict) else None
        if nested_verdict is False:
            return False
        explicit_positive = bool(
            normalized.get("verified") is True
            or normalized.get("effectconfirmed") is True
            or (
                isinstance(effect, str)
                and effect.strip().lower() == "confirmed"
            )
            or (isinstance(effect, dict) and effect.get("confirmed") is True)
        )
        if explicit_positive:
            return True
        # Accept one explicit result envelope only. Never recurse through
        # request/input/metadata/preflight fields that may echo parameters or
        # describe transport validation rather than application effect.
        return nested_verdict

    return verdict(payload) is True


_TREE_ROW_INDEX_RE = re.compile(r"^\s*-?\s*\[\d+\]")
_TREE_ROW_ROLE_RE = re.compile(r"\bAX[A-Za-z]+")
_TREE_ROW_QUOTED_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _tree_text_signature(markdown: str) -> str:
    """Digest the visible text of tree rows that carry no element index.

    Static text such as a calculator display or a window's "Edited" marker is
    never an indexed element, so the semantic element hash cannot see it change,
    and the 9x8 dHash rounds a digit away. Indexed rows are already covered by
    the element hash. Only the role and quoted text are kept: internal ids and
    other bracket metadata may vary between reads of an unchanged window.
    """
    rows = []
    for line in str(markdown or "").splitlines():
        if _TREE_ROW_INDEX_RE.match(line):
            continue
        texts = _TREE_ROW_QUOTED_RE.findall(line)
        if not texts:
            continue
        role = _TREE_ROW_ROLE_RE.search(line)
        rows.append((role.group(0) if role else "") + "|" + "|".join(texts))
    if not rows:
        return ""
    return hashlib.sha256("\n".join(rows).encode("utf-8")).hexdigest()


def _observation_fingerprint(image_bytes: bytes, elements: list[dict],
                             tree_text_sha256: str = "") -> dict:
    """Combine exact + perceptual screenshot facts with stable AX facts.

    The exact digest deliberately participates in the breaker key: a subtle
    real UI change that dHash rounds away must reset the streak. Encoding-only
    noise may therefore make the breaker less eager, which is safer than a
    false no-progress verdict.
    """
    raw_image_sha256 = hashlib.sha256(image_bytes).hexdigest() if image_bytes else ""
    image_phash = ""
    if image_bytes:
        try:
            with Image.open(io.BytesIO(image_bytes)) as source:
                gray = source.convert("L").resize((9, 8), Image.Resampling.LANCZOS)
                pixels = list(gray.getdata())
                bits = []
                for row in range(8):
                    offset = row * 9
                    bits.extend(pixels[offset + col] > pixels[offset + col + 1] for col in range(8))
                image_phash = f"{sum((1 << index) for index, bit in enumerate(bits) if bit):016x}"
        except Exception:
            image_phash = hashlib.sha256(image_bytes).hexdigest()[:16]
    stable_elements = []
    semantic_elements = []
    for item in elements or []:
        if not isinstance(item, dict):
            continue
        stable_elements.append({
            "role": item.get("role"),
            "label": item.get("label"),
            "value": item.get("value"),
            "frame": _json_safe(item.get("frame") or {}),
        })
        semantic_elements.append({
            "role": item.get("role"),
            "label": item.get("label"),
            "value": item.get("value"),
            "selected": item.get("selected"),
            "focused": item.get("focused"),
            "expanded": item.get("expanded"),
            "enabled": item.get("enabled"),
        })
    encoded_elements = json.dumps(stable_elements, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    elements_sha256 = hashlib.sha256(encoded_elements.encode("utf-8")).hexdigest()
    encoded_semantic = json.dumps(
        semantic_elements, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    )
    tree_text_sha256 = str(tree_text_sha256 or "")
    if tree_text_sha256:
        # Unindexed visible text is semantic state too (see _tree_text_signature).
        encoded_semantic += "\n" + tree_text_sha256
    semantic_elements_sha256 = hashlib.sha256(encoded_semantic.encode("utf-8")).hexdigest()
    combined_source = f"{raw_image_sha256}:{image_phash}:{elements_sha256}"
    if tree_text_sha256:
        combined_source += f":{tree_text_sha256}"
    combined = hashlib.sha256(combined_source.encode("ascii")).hexdigest()
    # The action oracle deliberately ignores exact PNG bytes and element
    # frames. Caret blinking, cursor overlays and encoding noise must not count
    # as task progress; meaningful labels/values/states and perceptual content do.
    oracle = hashlib.sha256(
        f"{image_phash}:{semantic_elements_sha256}".encode("ascii")
    ).hexdigest()
    return {
        "combined": combined,
        "oracle": oracle,
        # Comparisons are only meaningful between fingerprints built from the
        # same evidence: a screenshot-backed oracle and an AX-only oracle
        # differ trivially without proving any UI change.
        "basis": "image+ax" if image_bytes else ("ax_only" if stable_elements else "none"),
        "raw_image_sha256": raw_image_sha256,
        "image_phash": image_phash,
        "elements_sha256": elements_sha256,
        "semantic_elements_sha256": semantic_elements_sha256,
        "tree_text_sha256": tree_text_sha256,
    }


def _structured_elements(payload: Any) -> list[dict]:
    payload = _unwrap_structured(payload)
    if not isinstance(payload, dict):
        return []
    elements = payload.get("elements")
    return [dict(item) for item in elements or [] if isinstance(item, dict)]


def _model_elements_json(elements: list[dict], limit: int = MODEL_ELEMENTS_TEXT_LIMIT) -> tuple[str, int]:
    """Return valid, bounded JSON for the model-facing element snapshot.

    Cutting a serialized array with `_clip` produces invalid JSON and can split
    the very element_token the next action needs. Keep only action-relevant
    fields, keep oversized text elements addressable through a bounded preview
    plus length/hash metadata, prioritize interactive roles, and add whole
    objects until the budget is reached. The full unmodified list remains in
    worker memory for stale-token/index validation and exact AX transfer.
    """
    fields = (
        "element_index", "element_token", "role", "label", "value", "frame",
        "enabled", "focused", "selected", "actions",
    )
    compact = []
    for position, item in enumerate(elements or []):
        if not isinstance(item, dict):
            continue
        reduced: dict = {}
        for key in fields:
            value = item.get(key)
            if value in (None, "", [], {}):
                continue
            if key in {"label", "value"} and isinstance(value, str) and len(value) > 512:
                reduced[key] = value[:512]
                reduced[f"{key}_preview_only"] = True
                reduced[f"{key}_char_count"] = len(value)
                reduced[f"{key}_sha256"] = hashlib.sha256(value.encode("utf-8")).hexdigest()
            else:
                reduced[key] = _json_safe(value)
        reduced["_tree_order"] = position
        compact.append(reduced)

    interactive_markers = (
        "button", "field", "text", "checkbox", "radio", "link", "menuitem",
        "slider", "switch", "cell", "row", "tab", "pop", "combo", "increment",
    )

    def priority(item: dict) -> tuple[int, int]:
        role = str(item.get("role", "") or "").lower()
        actionable = bool(item.get("actions")) or any(marker in role for marker in interactive_markers)
        return (0 if actionable else 1, int(item.get("_tree_order", 0) or 0))

    selected: list[dict] = []
    for item in sorted(compact, key=priority):
        candidate = [*selected, item]
        encoded = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))
        if len(encoded) > max(256, int(limit)):
            continue
        selected = candidate
    for item in selected:
        item.pop("_tree_order", None)
    return json.dumps(selected, ensure_ascii=False, separators=(",", ":")), max(0, len(compact) - len(selected))


def _synthetic_transfer_descriptors() -> list[dict]:
    """Worker-local exact-text transfer tools; no source text crosses the tool log."""
    return [
        {
            "name": "capture_ax_text",
            "description": (
                "Capture exact text from explicitly selected elements in the current fresh AX snapshot into a "
                "task-private in-memory transfer buffer. Use only when the source text is actually exposed by AX. "
                "Returns only character count and SHA-256; it does not touch the system clipboard."
            ),
            "inputSchema": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "pid": {"type": "integer"},
                    "window_id": {"type": "integer"},
                    "element_tokens": {
                        "type": "array", "minItems": 1,
                        "items": {"type": "string"},
                    },
                },
                "required": ["pid", "window_id", "element_tokens"],
            },
        },
        {
            "name": "insert_captured_text",
            "description": (
                "Write the task-private transfer buffer exactly into one fresh destination text element. The "
                "buffer may come from capture_ax_text or from a verified real clipboard copy after visible selection. "
                "The text itself is never placed in model arguments or the actions log."
            ),
            "inputSchema": {
                "type": "object", "additionalProperties": False,
                "properties": {
                    "pid": {"type": "integer"},
                    "window_id": {"type": "integer"},
                    "element_token": {"type": "string"},
                },
                "required": ["pid", "window_id", "element_token"],
            },
        },
    ]


def _capture_ax_text(elements: list[dict], tokens: list[str]) -> tuple[str, dict]:
    wanted = {str(token).strip() for token in tokens or [] if str(token).strip()}
    selected: list[tuple[int, str, str]] = []
    present: set[str] = set()
    for order, item in enumerate(elements or []):
        if not isinstance(item, dict):
            continue
        token = str(item.get("element_token", "") or "").strip()
        if token not in wanted:
            continue
        present.add(token)
        role = str(item.get("role", "") or "")
        value = ""
        for key in ("value", "label", "title", "description"):
            candidate = item.get(key)
            if isinstance(candidate, str) and candidate.strip():
                value = candidate
                break
        if value:
            selected.append((order, role, value))
    missing = sorted(wanted - present)
    if missing:
        raise ValueError("Stale AX transfer token(s): " + ", ".join(missing[:5]))
    chunks: list[str] = []
    for _order, _role, value in sorted(selected, key=lambda entry: entry[0]):
        if not chunks or chunks[-1] != value:
            chunks.append(value)
    text = "\n".join(chunks)
    if not text.strip():
        raise ValueError("The selected fresh AX elements expose no readable text.")
    encoded = text.encode("utf-8")
    return text, {
        "source_element_count": len(selected),
        "char_count": len(text),
        "utf8_bytes": len(encoded),
        "sha256": hashlib.sha256(encoded).hexdigest(),
    }


def _is_writable_ax_element(item: dict) -> bool:
    if not isinstance(item, dict) or item.get("enabled") is False:
        return False
    role = str(item.get("role", "") or "").replace("_", "").lower()
    actions = item.get("actions") or []
    if not isinstance(actions, (list, tuple)):
        actions = [actions]
    normalized_actions = {
        str(action or "").replace("_", "").lower() for action in actions
    }
    return bool(
        any(marker in role for marker in ("textfield", "textarea", "textview", "editabletext"))
        or any("setvalue" in action for action in normalized_actions)
        or item.get("editable") is True
        or item.get("writable") is True
        or item.get("settable") is True
    )


def _writable_ax_targets(elements: list[dict]) -> list[dict]:
    """Return bounded, text-free destination hints from the fresh AX tree."""
    targets = []
    for item in elements or []:
        if not _is_writable_ax_element(item):
            continue
        token = str(item.get("element_token", "") or "").strip()
        if not token:
            continue
        label = str(item.get("label", "") or item.get("title", "") or "").strip()
        role = str(item.get("role", "") or "")
        search_like = "search" in (role + " " + label).lower()
        targets.append({
            "element_token": token,
            "element_index": item.get("element_index"),
            "role": role,
            "label": label[:160],
            "search_like": search_like,
        })
    targets.sort(key=lambda item: (item["search_like"], str(item.get("element_index", ""))))
    return targets[:20]


def _resolve_action_element(
        arguments: dict, elements: list[dict],
        original_arguments: dict | None = None) -> dict | None:
    """Resolve one action handle only inside the current fresh AX snapshot."""
    arguments = arguments if isinstance(arguments, dict) else {}
    original = original_arguments if isinstance(original_arguments, dict) else arguments
    token = str(
        arguments.get("element_token", "")
        or original.get("element_token", "") or ""
    ).strip()
    wanted_index = arguments.get("element_index")
    if wanted_index is None and not token:
        wanted_index = original.get("element_index")
    for item in elements or []:
        if not isinstance(item, dict):
            continue
        if token and str(item.get("element_token", "") or "") == token:
            return item
        if not token and wanted_index is not None:
            try:
                if int(item.get("element_index")) == int(wanted_index):
                    return item
            except (TypeError, ValueError):
                continue
    return None


def _semantic_text_sha256(value: Any) -> str:
    text = str(value or "").strip()
    return hashlib.sha256(text.encode("utf-8")).hexdigest() if text else ""


def _ax_target_selector_from_element(item: dict) -> dict:
    """Build a value-free AX identity that survives token/index regeneration.

    ``element_token`` and ``element_index`` are snapshot-local handles.  They
    are intentionally absent here.  The selector is conservative: if several
    controls share it, verification refuses to guess which one is the target.
    """
    item = item if isinstance(item, dict) else {}
    actions = item.get("actions") or []
    if not isinstance(actions, (list, tuple)):
        actions = [actions]
    identifier = ""
    for key in ("accessibility_identifier", "identifier", "automation_id"):
        if str(item.get(key, "") or "").strip():
            identifier = str(item.get(key, "") or "").strip()
            break
    visible_name = ""
    visible_name_source = ""
    for key in ("label", "title", "description"):
        if str(item.get(key, "") or "").strip():
            visible_name = str(item.get(key, "") or "").strip()
            visible_name_source = key
            break
    raw_value = item.get("value")
    value_known = isinstance(raw_value, str)
    value_bytes = raw_value.encode("utf-8") if value_known else b""
    return {
        "version": 1,
        "source_element_index": item.get("element_index"),
        "role": str(item.get("role", "") or "").strip().lower(),
        "subrole": str(item.get("subrole", "") or "").strip().lower(),
        "identifier_sha256": _semantic_text_sha256(identifier),
        "name_source": visible_name_source,
        "name_sha256": _semantic_text_sha256(visible_name),
        "actions": sorted({
            str(action or "").strip().lower()
            for action in actions if str(action or "").strip()
        }),
        # Persist only a digest/size baseline, never the user's field text.
        "value_known_before": value_known,
        "value_sha256_before": (
            hashlib.sha256(value_bytes).hexdigest() if value_known else ""
        ),
        "value_utf8_bytes_before": len(value_bytes) if value_known else 0,
        "writable_at_bind": _is_writable_ax_element(item),
    }


def _ax_target_selector_signature(selector: dict) -> tuple:
    selector = selector if isinstance(selector, dict) else {}
    return (
        "ax_target_v1",
        str(selector.get("role", "") or ""),
        str(selector.get("subrole", "") or ""),
        str(selector.get("identifier_sha256", "") or ""),
        str(selector.get("name_source", "") or ""),
        str(selector.get("name_sha256", "") or ""),
        tuple(str(item or "") for item in (selector.get("actions") or [])),
    )


def _ax_unknown_replay_target_signature(selector: dict) -> tuple:
    """Fail-closed identity for an ambiguous post-dispatch replay barrier.

    Accessibility names and action lists can change as a direct result of a
    click (Play -> Pause, collapsed -> expanded).  They therefore cannot be
    used to manufacture permission to repeat an UNKNOWN delivery. Identifier
    presence can itself flicker across SwiftUI/Stage snapshots, so the UNKNOWN
    path deliberately uses one coarse process-local AX element scope.
    """
    # Identifier visibility itself can change between SwiftUI/Stage snapshots.
    # UNKNOWN is an exceptional path, so keep one process-scoped AX element
    # barrier instead of allowing missing<->present identifier transitions to
    # authorize duplicate input.
    return ("ax_element_scope_v1",)


def _stable_ax_target_selector(
        arguments: dict, elements: list[dict],
        original_arguments: dict | None = None) -> dict:
    matched = _resolve_action_element(arguments, elements, original_arguments)
    if matched is None:
        return {}
    selector = _ax_target_selector_from_element(matched)
    identifier = str(selector.get("identifier_sha256", "") or "")
    if identifier:
        selector["identifier_match_count_at_bind"] = sum(
            1 for item in elements or []
            if isinstance(item, dict)
            and str(_ax_target_selector_from_element(item).get(
                "identifier_sha256", ""
            ) or "") == identifier
        )
    else:
        selector["identifier_match_count_at_bind"] = 0
    return selector


def _target_selector_candidates(elements: list[dict], selector: dict) -> list[dict]:
    if not isinstance(selector, dict) or not selector:
        return []
    identifier = str(selector.get("identifier_sha256", "") or "")
    if identifier:
        if int(selector.get("identifier_match_count_at_bind", 0) or 0) != 1:
            return []
        wanted_role = str(selector.get("role", "") or "")
        wanted_subrole = str(selector.get("subrole", "") or "")
        candidates = []
        for item in elements or []:
            if not isinstance(item, dict):
                continue
            candidate = _ax_target_selector_from_element(item)
            if str(candidate.get("identifier_sha256", "") or "") != identifier:
                continue
            if str(candidate.get("role", "") or "") != wanted_role \
                    or str(candidate.get("subrole", "") or "") != wanted_subrole:
                continue
            candidates.append(item)
        return candidates
    # Without a stable identifier, a same-looking control elsewhere in a new
    # tree is not a trustworthy successor.  Require both the original semantic
    # selector and its source index.  Index regeneration therefore yields an
    # explicit INDETERMINATE result instead of guessing.
    wanted = _ax_target_selector_signature(selector)
    try:
        source_index = int(selector.get("source_element_index"))
    except (TypeError, ValueError):
        return []
    candidates = []
    for item in elements or []:
        if not isinstance(item, dict):
            continue
        try:
            candidate_index = int(item.get("element_index"))
        except (TypeError, ValueError):
            continue
        if candidate_index == source_index \
                and _ax_target_selector_signature(
                    _ax_target_selector_from_element(item)
                ) == wanted:
            candidates.append(item)
    return candidates


def _target_text_postcondition(
        elements: list[dict], selector: dict, *,
        expected_text: str = "", expected_sha256: str = "",
        write_semantics: str = "") -> dict:
    """Evaluate text only on one uniquely identified destination element."""
    identity_candidates = _target_selector_candidates(elements, selector)
    candidates = [item for item in identity_candidates if _is_writable_ax_element(item)]
    selector_signature = _ax_target_selector_signature(selector) if selector else ()
    evidence = {
        "target_selector_bound": bool(selector),
        "target_has_stable_identifier": bool(
            isinstance(selector, dict)
            and str(selector.get("identifier_sha256", "") or "")
            and int(selector.get("identifier_match_count_at_bind", 0) or 0) == 1
        ),
        "target_match_count": len(candidates),
        "target_identity_match_count": len(identity_candidates),
        "target_writable": len(candidates) == 1,
        "target_selector_sha256": (
            hashlib.sha256(repr(selector_signature).encode("utf-8")).hexdigest()
            if selector_signature else ""
        ),
        "expected_text_present": False,
        "expected_text_exact": False,
        "expected_text_hash_present": False,
        "target_value_changed": False,
        "expected_state_preexisting": False,
        "action_specific_text_transition": False,
    }
    if len(candidates) != 1:
        return evidence
    target = candidates[0]
    # The destination's accessible name describes its identity; it is not the
    # editable payload.  Only the AX value property may prove a text write.
    values = [target.get("value")] if isinstance(target.get("value"), str) else []
    after_value = values[0] if values else None
    after_hash = (
        hashlib.sha256(after_value.encode("utf-8")).hexdigest()
        if isinstance(after_value, str) else ""
    )
    before_known = bool(selector.get("value_known_before") is True)
    before_hash = str(selector.get("value_sha256_before", "") or "")
    evidence["target_value_changed"] = bool(
        before_known and after_hash and after_hash != before_hash
    )
    if expected_text:
        evidence["expected_text_exact"] = any(value == expected_text for value in values)
        evidence["expected_text_present"] = any(
            value == expected_text or expected_text in value for value in values
        )
    expected_hash = str(expected_sha256 or "").strip().lower()
    if expected_hash:
        evidence["expected_text_hash_present"] = any(
            hashlib.sha256(value.encode("utf-8")).hexdigest() == expected_hash
            for value in values
        )
    evidence["expected_state_preexisting"] = bool(
        selector.get("expected_text_present_before") is True
        or selector.get("expected_text_exact_before") is True
        or (expected_hash and before_known and before_hash == expected_hash)
    )
    semantics = str(write_semantics or "").strip().lower()
    if semantics == "insert_text":
        append_hash = str(selector.get("expected_append_sha256", "") or "")
        evidence["action_specific_text_transition"] = bool(
            before_known and after_hash and append_hash
            and after_hash == append_hash and after_hash != before_hash
        )
    elif semantics == "replace_exact":
        expected_now = bool(
            evidence["expected_text_exact"]
            or evidence["expected_text_hash_present"]
        )
        evidence["action_specific_text_transition"] = bool(
            expected_now and evidence["target_value_changed"]
        )
    return evidence


def _transfer_buffer_pending(transfer_buffer: dict) -> bool:
    return bool(
        isinstance(transfer_buffer, dict)
        and str(transfer_buffer.get("text", "") or "")
        and transfer_buffer.get("insert_verified") is not True
    )


def _is_paste_shortcut(name: str, arguments: dict) -> bool:
    return _is_command_shortcut(name, arguments, "v")


def _is_copy_shortcut(name: str, arguments: dict) -> bool:
    return _is_command_shortcut(name, arguments, "c")


def _is_select_all_shortcut(name: str, arguments: dict) -> bool:
    return _is_command_shortcut(name, arguments, "a")


def _is_command_shortcut(name: str, arguments: dict, final_key: str) -> bool:
    if str(name or "").lower() not in {"hotkey", "shortcut", "press_key", "key", "press_keys"}:
        return False
    keys = _normalized_action_keys(arguments if isinstance(arguments, dict) else {})
    return bool(
        keys and keys[-1] == str(final_key or "").lower()
        and any(item in {"cmd", "command", "meta"} for item in keys[:-1])
    )


def _transfer_prompt(transfer_buffer: dict, elements: list[dict]) -> str:
    if not _transfer_buffer_pending(transfer_buffer):
        return ""
    metadata = transfer_buffer.get("metadata") \
        if isinstance(transfer_buffer.get("metadata"), dict) else {}
    targets = _writable_ax_targets(elements)
    return (
        "\nTASK-PRIVATE TEXT TRANSFER IS PENDING: "
        f"char_count={metadata.get('char_count', 0)}, sha256={metadata.get('sha256', '')}. "
        "Completion is blocked until insert_captured_text writes this exact buffer to a fresh writable AX "
        "destination and the next AX tree reads the same hash back. Cmd+V is prohibited while this buffer "
        "is pending. Fresh writable destinations (search_like targets are lower priority): "
        + json.dumps(targets, ensure_ascii=False, separators=(",", ":"))
        + "\n"
    )


def _elements_contain_text_hash(
        elements: list[dict], expected_sha256: str,
        target_selector: dict | None = None) -> bool:
    """Compatibility helper with mandatory target scoping.

    A whole-tree hash search can be satisfied by an unrelated static label and
    must never prove a destination write.  Missing/ambiguous selectors fail
    closed.
    """
    return bool(_target_text_postcondition(
        elements, target_selector or {}, expected_sha256=expected_sha256,
    ).get("expected_text_hash_present"))


def _clipboard_text_snapshot() -> tuple[str, dict]:
    """Read text plus log-safe metadata from the pasteboard in one atomic probe.

    Callers may keep the text only in the task-private transfer buffer.  The
    returned metadata is the only part permitted in progress/evidence logs.
    """
    try:
        probe = subprocess.run(
            ["/usr/bin/pbpaste"], capture_output=True, timeout=2, check=False,
        )
    except Exception as exc:
        return "", {"available": False, "error": str(exc)}
    if probe.returncode != 0:
        return "", {
            "available": False,
            "error": (probe.stderr or b"").decode("utf-8", errors="replace")[:300],
        }
    payload = bytes(probe.stdout or b"")
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        return "", {
            "available": False,
            "error": f"clipboard text was not valid UTF-8: {exc}",
            "utf8_bytes": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    metadata = {
        "available": True,
        "utf8_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    return text, metadata


def _clipboard_text_fingerprint() -> dict:
    """Return only hash/size metadata; never expose the clipboard text."""
    _text, metadata = _clipboard_text_snapshot()
    return metadata


def _clipboard_write_text(text: str) -> dict:
    """Write a private probe/restore value; return log-safe metadata only."""
    payload = str(text or "").encode("utf-8")
    try:
        result = subprocess.run(
            ["/usr/bin/pbcopy"], input=payload, capture_output=True,
            timeout=2, check=False,
        )
    except Exception as exc:
        return {"available": False, "error": str(exc)}
    if result.returncode != 0:
        return {
            "available": False,
            "error": (result.stderr or b"").decode("utf-8", errors="replace")[:300],
        }
    return {
        "available": True,
        "utf8_bytes": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def _clipboard_probe_result(
        original_text: str, before: dict, probe: dict) -> tuple[str, dict]:
    """Read and settle one copy probe without exposing clipboard text in logs."""
    copied_text, after = _clipboard_text_snapshot()
    probe_installed = bool(
        isinstance(probe, dict)
        and probe.get("available") is True and probe.get("sha256")
    )
    changed = bool(
        after.get("available")
        and after.get("utf8_bytes", 0) > 0
        and ((
            probe_installed and after.get("sha256") != probe.get("sha256")
        ) or (
            not probe_installed and before.get("available") and (
                before.get("sha256") != after.get("sha256")
                or before.get("utf8_bytes") != after.get("utf8_bytes")
            )
        ))
    )
    absence_proven = bool(
        after.get("available")
        and ((probe_installed and after.get("sha256") == probe.get("sha256"))
             or (not probe_installed and before.get("available")
                 and before.get("sha256") == after.get("sha256")
                 and before.get("utf8_bytes") == after.get("utf8_bytes")))
    )
    restore: dict = {}
    if not changed and probe_installed:
        restore = _clipboard_write_text(original_text)
    evidence = {
        "overwrite_disclosed": True,
        "before": before,
        "probe": probe,
        "after": after,
        "changed": changed,
        "absence_proven": absence_proven,
        "restored_after_no_effect": bool(restore.get("available") is True),
        "restore": restore,
        "raw_text_logged": False,
    }
    return (copied_text if changed else ""), evidence


def _expects_visible_change(name: str, arguments: dict) -> bool:
    """Conservative screenshot breaker classifier.

    Clipboard copies, focus/foreground changes, launch/session/config/cursor and
    recording operations are intentionally excluded because a byte-identical
    target-window PNG is a valid success for those actions.
    """
    lowered = str(name or "").lower()
    tokens = set(_name_tokens(lowered))
    if lowered in APP_SWITCH_TOOLS or lowered in WORKER_OWNED_TOOLS:
        return False
    if {"copy", "clipboard", "focus", "activate", "front", "launch", "open"} & tokens:
        return False
    modifiers = arguments.get("modifier") or arguments.get("modifiers") or []
    if not isinstance(modifiers, (list, tuple)):
        modifiers = [modifiers] if modifiers not in (None, "") else []
    keys = arguments.get("keys")
    if isinstance(keys, (list, tuple)):
        key_parts = list(keys)
    elif keys not in (None, ""):
        key_parts = re.split(r"[+\s]+", str(keys))
    else:
        singular = arguments.get("key")
        key_parts = [singular] if singular not in (None, "") else []
    normalized_keys = [str(item).strip().lower() for item in [*modifiers, *key_parts] if str(item).strip()]
    if lowered in {"hotkey", "shortcut", "press_key", "key"} \
            and normalized_keys and normalized_keys[-1] == "c" \
            and any(item in {"cmd", "command", "meta"} for item in normalized_keys[:-1]):
        return False
    if lowered in {"hotkey", "shortcut"}:
        return bool(normalized_keys)
    return bool(tokens & VISIBLE_ACTION_TOKENS)


def _normalized_action_keys(arguments: dict) -> list[str]:
    modifiers = arguments.get("modifier") or arguments.get("modifiers") or []
    if not isinstance(modifiers, (list, tuple)):
        modifiers = [modifiers] if modifiers not in (None, "") else []
    keys = arguments.get("keys")
    if isinstance(keys, (list, tuple)):
        key_parts = list(keys)
    elif keys not in (None, ""):
        key_parts = re.split(r"[+\s]+", str(keys))
    else:
        singular = arguments.get("key")
        key_parts = [singular] if singular not in (None, "") else []
    aliases = {
        "command": "cmd", "meta": "cmd", "cmd": "cmd",
        "control": "ctrl", "ctrl": "ctrl",
        "option": "alt", "alt": "alt",
        "shift": "shift", "function": "fn", "fn": "fn",
    }
    normalized = [
        aliases.get(str(item).strip().lower(), str(item).strip().lower())
        for item in [*modifiers, *key_parts] if str(item).strip()
    ]
    modifier_order = {"cmd": 0, "ctrl": 1, "alt": 2, "shift": 3, "fn": 4}
    canonical_modifiers = sorted(
        {item for item in normalized if item in modifier_order},
        key=lambda item: modifier_order[item],
    )
    ordinary_keys = [item for item in normalized if item not in modifier_order]
    return [*canonical_modifiers, *ordinary_keys]


def _normalized_action_modifiers(arguments: dict) -> tuple[str, ...]:
    """Canonicalize modifier aliases/order without admitting ordinary keys."""
    raw = arguments.get("modifier") or arguments.get("modifiers") or []
    if not isinstance(raw, (list, tuple)):
        raw = [raw] if raw not in (None, "") else []
    aliases = {
        "command": "cmd", "meta": "cmd", "cmd": "cmd",
        "control": "ctrl", "ctrl": "ctrl",
        "option": "alt", "alt": "alt",
        "shift": "shift", "function": "fn", "fn": "fn",
    }
    order = {"cmd": 0, "ctrl": 1, "alt": 2, "shift": 3, "fn": 4}
    normalized = {
        aliases.get(str(item).strip().lower(), str(item).strip().lower())
        for item in raw if str(item).strip()
    }
    return tuple(sorted(normalized, key=lambda item: (order.get(item, 99), item)))


def _action_oracle_spec(name: str, arguments: dict, address_mode: str) -> dict:
    lowered = str(name or "").lower()
    keys = _normalized_action_keys(arguments)
    command = any(item in {"cmd", "command", "meta"} for item in keys[:-1])
    final_key = keys[-1] if keys else ""
    expected_text = ""
    for key in ("text", "value", "input"):
        if arguments.get(key) not in (None, ""):
            expected_text = str(arguments.get(key))
            break
    if lowered in APP_SWITCH_TOOLS:
        kind = "topology"
    elif command and final_key == "c":
        kind = "clipboard_copy"
    elif command and final_key == "a":
        kind = "selection"
    elif command and final_key == "v":
        kind = "paste"
    elif command and final_key in {"n", "o"}:
        kind = "create_or_open"
    elif expected_text or lowered in {"type_text", "set_value", "write_text", "input_text", "paste"}:
        kind = "text_mutation"
    elif lowered in APP_SWITCH_TOOLS:
        kind = "topology"
    elif _expects_visible_change(lowered, arguments):
        kind = "visual_mutation"
    else:
        kind = "driver_only"
    # A call whose transport fails after dispatch may already have mutated the
    # app. Default every actual app-input tool to replay-sensitive, with only
    # audited read/cursor/session plumbing and copy/selection as explicit safe
    # exceptions. This is deliberately broader than mathematical idempotence:
    # a second click, Enter, delete, send or launch can all duplicate work.
    replay_sensitive = bool(
        lowered == "insert_captured_text"
        or (
            lowered != "capture_ax_text"
            and kind not in {"clipboard_copy", "selection"}
            and not _worker_owned_tool(lowered)
        )
    )
    text_write_semantics = ""
    if lowered in {"type_text", "write_text", "input_text"}:
        text_write_semantics = "insert_text"
    elif lowered in {"set_value", "insert_captured_text"}:
        text_write_semantics = "replace_exact"
    return {
        "kind": kind,
        "address_mode": str(address_mode or "direct"),
        "expected_text": expected_text,
        "expects_visual_change": kind in {
            "paste", "create_or_open", "text_mutation", "visual_mutation", "topology",
        },
        "visually_silent": kind in {"clipboard_copy", "selection", "driver_only"},
        "non_idempotent": kind in {"paste", "create_or_open", "text_mutation"},
        "replay_sensitive": replay_sensitive,
        "text_write_semantics": text_write_semantics,
    }


def _bind_oracle_to_ax_target(
        oracle: dict, arguments: dict, address_mode: str,
        elements: list[dict], original_arguments: dict | None = None) -> dict:
    """Attach a value-free target selector to an element-addressed oracle."""
    bound = dict(oracle or {})
    if str(address_mode or "") != "element_ax":
        return bound
    selector = _stable_ax_target_selector(
        arguments, elements, original_arguments=original_arguments,
    )
    if selector:
        matched = _resolve_action_element(
            arguments, elements, original_arguments=original_arguments,
        )
        before_value = matched.get("value") if isinstance(matched, dict) else None
        expected_text = str(bound.get("expected_text", "") or "")
        expected_hash = str(bound.get("expected_text_sha256", "") or "").lower()
        if isinstance(before_value, str) and expected_text:
            selector["expected_text_present_before"] = (
                expected_text == before_value or expected_text in before_value
            )
            selector["expected_text_exact_before"] = expected_text == before_value
            if str(bound.get("text_write_semantics", "") or "") == "insert_text":
                successor = (before_value + expected_text).encode("utf-8")
                selector["expected_append_sha256"] = hashlib.sha256(successor).hexdigest()
                selector["expected_append_utf8_bytes"] = len(successor)
        elif expected_hash and selector.get("value_known_before") is True:
            selector["expected_text_exact_before"] = (
                str(selector.get("value_sha256_before", "") or "").lower()
                == expected_hash
            )
        bound["target_selector"] = selector
    return bound


def _canonical_action_signature(
        name: str, arguments: dict, address_mode: str,
        window_context: dict, identity: str = "", elements: list[dict] | None = None,
        original_arguments: dict | None = None,
        replay_stable_element: bool = False) -> tuple:
    """Return a snapshot-stable identity for one logical input operation.

    Driver AX tokens are fresh-snapshot handles (``s0042:17``); their prefix
    must never make a repeated operation look new.  Resolve them back to the
    current element index plus a bounded semantic fingerprint.  Conversely,
    tool/key/button/text payloads and every pixel endpoint remain part of the
    signature so unrelated operations cannot lock one another out.
    """
    arguments = arguments if isinstance(arguments, dict) else {}
    original = original_arguments if isinstance(original_arguments, dict) else arguments
    mode = str(address_mode or "direct")
    pid = _canonical_identity_value(arguments.get("pid", window_context.get("pid")))
    window_id = _canonical_identity_value(
        arguments.get("window_id", window_context.get("window_id"))
    )

    def normalized_element() -> tuple:
        token = str(arguments.get("element_token", "") or original.get("element_token", "") or "").strip()
        candidate_index = arguments.get("element_index")
        if candidate_index is None and not token:
            candidate_index = original.get("element_index")
        matched = _resolve_action_element(arguments, elements or [], original)
        if replay_stable_element:
            # UNKNOWN-delivery replay safety must survive a fresh AX tree that
            # renumbers the same control.  Ambiguous semantic identities are
            # intentionally coarse and therefore over-block rather than risk a
            # duplicate side effect.
            selector = (
                _ax_target_selector_from_element(matched)
                if matched is not None else {}
            )
            return (
                "element_semantic",
                *_ax_unknown_replay_target_signature(selector),
            )
        index: Any = (matched or {}).get("element_index", candidate_index)
        if index is None and token and ":" in token:
            suffix = token.rsplit(":", 1)[-1]
            try:
                index = int(suffix)
            except (TypeError, ValueError):
                index = None
        try:
            index = int(index) if index is not None else None
        except (TypeError, ValueError):
            index = None
        role = str((matched or {}).get("role", "") or "").strip().lower()
        label = str((matched or {}).get("label", "") or "")
        actions = (matched or {}).get("actions") or []
        if not isinstance(actions, (list, tuple)):
            actions = [actions]
        label_hash = hashlib.sha256(label.encode("utf-8")).hexdigest() if label else ""
        token_fallback = ""
        if index is None and token:
            token_fallback = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return (
            "element", index, role, label_hash,
            tuple(sorted(str(item).strip().lower() for item in actions if str(item).strip())),
            token_fallback,
        )

    if mode == "element_ax":
        address = normalized_element()
    elif mode in PIXEL_ADDRESS_MODES:
        address = (
            "pixels",
            *tuple(
                (key, round(float(value), 6))
                for key in sorted(COORDINATE_KEYS)
                if (value := _finite_number(arguments.get(key))) is not None
            ),
        )
    elif mode == "key" and (
            original.get("element_token") not in (None, "")
            or original.get("element_index") is not None):
        address = ("focus_assertion", *normalized_element())
    else:
        address = ()

    excluded = {
        "delivery_mode", "session", "session_id", "sessionId", "debug_image_out",
        "pid", "window_id", "scope", "element_token", "element_index",
        *COORDINATE_KEYS,
    }
    payload = []
    for key in sorted(arguments):
        if key in excluded:
            continue
        value = arguments.get(key)
        if key in {"modifier", "modifiers", "keys"}:
            if not isinstance(value, (list, tuple)):
                value = [value] if value not in (None, "") else []
            value = tuple(str(item).strip().lower() for item in value if str(item).strip())
        elif key in {"text", "value", "input"} and value not in (None, ""):
            encoded = str(value).encode("utf-8")
            value = ("sha256", hashlib.sha256(encoded).hexdigest(), len(encoded))
        elif isinstance(value, (dict, list, tuple)):
            value = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload.append((str(key), value))
    if str(name or "").strip().lower() == "insert_captured_text":
        # The destination address alone is not the complete operation: two
        # task-private buffers written to the same AX element must not share an
        # unknown-delivery replay barrier. Only worker-produced hash/length
        # metadata participates; the private text never enters the signature.
        for key in (
                "__worker_transfer_sha256", "__worker_transfer_utf8_bytes",
                "__worker_transfer_generation", "__worker_insert_method"):
            if original.get(key) not in (None, ""):
                payload.append((key, original.get(key)))
    return (
        "operation", str(name or "").strip().lower(), mode,
        pid, window_id, _canonical_target_identity(identity), address, tuple(payload),
    )


def _unknown_replay_action_signature(
        name: str, arguments: dict, address_mode: str,
        window_context: dict, identity: str = "", elements: list[dict] | None = None,
        original_arguments: dict | None = None) -> tuple:
    """Return transport-alias- and snapshot-independent replay semantics."""
    signature = _canonical_action_signature(
        name, arguments, address_mode, window_context, identity,
        elements=elements, original_arguments=original_arguments,
        replay_stable_element=True,
    )
    if not isinstance(signature, tuple) or len(signature) != 8:
        return signature
    marker, tool_name, mode, pid, window_id, target_identity, address, payload = signature
    lowered = str(name or "").strip().lower()
    payload_items = list(payload if isinstance(payload, tuple) else ())
    if str(mode or "") == "element_ax":
        # An AX action may itself open/select another window in the same app.
        # Keep UNKNOWN element barriers process-scoped so that this topology
        # effect cannot manufacture replay permission.
        window_id = "app_scope_element_ax"
    if lowered in {"hotkey", "shortcut", "press_key", "key", "press_keys"}:
        tool_name = "key_event"
        payload_items = [
            item for item in payload_items
            if isinstance(item, tuple) and item
            and str(item[0]) not in {"key", "keys", "modifier", "modifiers"}
        ]
        normalized_keys = tuple(_normalized_action_keys(
            original_arguments if isinstance(original_arguments, dict) else arguments
        ))
        payload_items.append(("normalized_keys", normalized_keys))
        if normalized_keys and normalized_keys[-1] in {"n", "o"} \
                and "cmd" in normalized_keys[:-1]:
            # A successful create/open action can itself select a newly created
            # window.  Keep its UNKNOWN barrier at process scope so that the
            # changed window_id cannot authorize another Cmd+N/Cmd+O.
            window_id = "app_scope_create_or_open"
    elif lowered in {"type_text", "set_value", "write_text", "input_text", "insert_captured_text"}:
        tool_name = "text_write"
        payload_items = [
            item for item in payload_items
            if isinstance(item, tuple) and item
            and str(item[0]) not in {
                "text", "value", "input",
                "delay_ms", "from_zoom",
                "__worker_transfer_sha256", "__worker_transfer_utf8_bytes",
                "__worker_transfer_generation", "__worker_insert_method",
            }
        ]
        original = original_arguments if isinstance(original_arguments, dict) else arguments
        if lowered == "insert_captured_text":
            transfer_hash = str(original.get("__worker_transfer_sha256", "") or "")
            transfer_bytes = int(original.get("__worker_transfer_utf8_bytes", 0) or 0)
            text_payload = ("sha256", transfer_hash, transfer_bytes)
        else:
            text_value = next((
                arguments.get(key) for key in ("text", "value", "input")
                if arguments.get(key) not in (None, "")
            ), "")
            encoded = str(text_value or "").encode("utf-8")
            text_payload = (
                "sha256", hashlib.sha256(encoded).hexdigest(), len(encoded)
            ) if encoded else ()
        payload_items.append(("text_payload", text_payload))
    elif lowered in {"click", "mouse_click", "tap", "double_click", "right_click"}:
        tool_name = "pointer_click"
        payload_items = [
            item for item in payload_items
            if isinstance(item, tuple) and item
            and str(item[0]) not in {
                "button", "count", "click_count", "times", "action",
                "modifier", "modifiers", "from_zoom",
            }
        ]
        default_button = "right" if lowered == "right_click" else "left"
        raw_button = str(
            arguments.get("button", default_button) or default_button
        ).strip().lower()
        button = {
            "primary": "left", "secondary": "right", "middle": "middle",
        }.get(raw_button, raw_button)
        default_count = 2 if lowered == "double_click" else 1
        count_value = arguments.get(
            "count", arguments.get(
                "click_count", arguments.get("times", default_count)
            )
        )
        try:
            click_count = max(1, int(count_value or 1))
        except (TypeError, ValueError):
            click_count = 1
        raw_action = str(arguments.get("action", "click") or "click").strip().lower()
        # CuaDriver exposes the same AX operations through both dedicated
        # tools and click(action=...).  Normalize those aliases before hashing
        # so UNKNOWN cannot be replayed by changing only the tool spelling.
        original_mode = str(address_mode or "")
        if original_mode in PIXEL_ADDRESS_MODES:
            # action is AX-only on 0.8.3's click tool.  Pixel delivery is
            # determined solely by button/count.
            raw_action = "click"
        if raw_action == "show_menu":
            button = "right"
            click_count = 1
        elif raw_action == "open":
            button = "left"
            click_count = 2
        elif original_mode == "element_ax" and lowered not in {
                "double_click", "right_click"}:
            # count is pixel-only; arbitrary explicit values cannot create
            # replay permission for a repeated AX action.
            click_count = 1
        click_aliases = {"click", "press", "tap"}
        if button == "right":
            click_aliases.add("show_menu")
        if click_count == 2 or lowered == "double_click":
            click_aliases.add("open")
        click_action = "click" if raw_action in click_aliases else raw_action
        payload_items.extend((
            ("button", button), ("click_count", click_count),
            ("pointer_action", click_action),
        ))
        modifiers = _normalized_action_modifiers(arguments)
        if modifiers:
            payload_items.append(("normalized_modifiers", modifiers))
    elif lowered == "scroll":
        payload_items = [
            item for item in payload_items
            if isinstance(item, tuple) and item
            and str(item[0]) not in {"amount", "by", "from_zoom"}
        ]
        try:
            amount = max(1, int(arguments.get("amount", 3) or 3))
        except (TypeError, ValueError):
            amount = 3
        by = str(arguments.get("by", "line") or "line").strip().lower()
        payload_items.extend((("amount", amount), ("by", by)))
    elif lowered == "drag":
        payload_items = [
            item for item in payload_items
            if isinstance(item, tuple) and item
            and str(item[0]) not in {
                "button", "duration_ms", "steps", "from_zoom",
                "modifier", "modifiers",
            }
        ]
        button = str(arguments.get("button", "left") or "left").strip().lower()
        payload_items.append(("button", button))
        modifiers = _normalized_action_modifiers(arguments)
        if modifiers:
            payload_items.append(("normalized_modifiers", modifiers))
    elif lowered in APP_SWITCH_TOOLS:
        tool_name = "app_switch"
        # Launch identity belongs to the requested bundle/name, never to the
        # app/window that happened to be observed before dispatch.
        pid = "launch_target_scope"
        window_id = "launch_target_scope"
        normalized_launch = []
        bundle_supplied = bool(str(arguments.get("bundle_id", "") or "").strip())
        for item in payload_items:
            if not isinstance(item, tuple) or not item:
                continue
            key = str(item[0])
            value = item[1] if len(item) > 1 else None
            if key == "creates_new_application_instance" and value is not True:
                continue
            if key in {"additional_arguments", "urls"} \
                    and value in (None, "", "[]", (), []):
                continue
            if key == "name" and bundle_supplied:
                continue
            normalized_launch.append(item)
        payload_items = normalized_launch
    # A lost reply means the side effect may already have landed.  Address
    # modality is only a delivery route, not permission to repeat the semantic
    # input through AX, window pixels, or desktop pixels.  The UNKNOWN path is
    # therefore deliberately process-scoped and address-free; payload/tool
    # semantics still distinguish e.g. left vs right click, key sequences, and
    # exact text hashes.
    mode = "app_input_scope"
    window_id = "app_scope_unknown_input"
    if str(target_identity or "").startswith("window_id:"):
        target_identity = f"pid:{pid}" if pid not in (None, "") else "app_scope"
    address = ()
    return (
        marker, tool_name, mode, pid, window_id, target_identity,
        address, tuple(sorted(payload_items, key=lambda item: str(item[0]))),
    )


def _unknown_replay_operation_sha256(
        name: str, arguments: dict, address_mode: str,
        window_context: dict, identity: str = "", elements: list[dict] | None = None,
        original_arguments: dict | None = None) -> str:
    signature = _unknown_replay_action_signature(
        name, arguments, address_mode, window_context, identity,
        elements=elements, original_arguments=original_arguments,
    )
    return hashlib.sha256(repr(signature).encode("utf-8")).hexdigest()


def _action_rung_key(
        name: str, arguments: dict, address_mode: str, oracle: dict,
        window_context: dict, identity: str = "", elements: list[dict] | None = None,
        original_arguments: dict | None = None, state_epoch: int = 0) -> tuple:
    """Identify one exact delivery rung without conflating unrelated actions."""
    delivery_mode = str(arguments.get("delivery_mode", "background") or "background").lower()
    operation = _normalized_exact_operation_signature(
        name, arguments, address_mode, window_context, identity,
        elements=elements, original_arguments=original_arguments,
        stable_ax_target=False,
    )
    geometry_epoch = (
        window_context.get("geometry_epoch") if str(address_mode or "") in PIXEL_ADDRESS_MODES else None
    )
    return (
        "rung", operation, delivery_mode, geometry_epoch, int(state_epoch or 0),
        str((oracle or {}).get("kind", "driver_only") or "driver_only"),
    )


def _rung_operation_sha256(rung_key: tuple) -> str:
    """Hash the state-epoch-independent logical operation inside a rung."""
    if not isinstance(rung_key, tuple) or len(rung_key) < 2:
        return ""
    return hashlib.sha256(repr(rung_key[1]).encode("utf-8")).hexdigest()


def _ax_unsupported_memo_key(name: str, window_context: dict, oracle_spec: dict) -> tuple:
    """Stable identity for an element that rejected an AX action with a kAXError.

    Keyed on the value-free AX selector signature so the ban survives
    element_index/token regeneration across snapshots but never outlives the
    process or leaks to lookalike elements in other apps.
    """
    selector = oracle_spec.get("target_selector") \
        if isinstance(oracle_spec.get("target_selector"), dict) else {}
    if not selector:
        return ()
    return (
        (window_context or {}).get("pid"),
        str(name or "").lower(),
        _ax_target_selector_signature(selector),
    )


_AX_ACTION_ERROR_RE = re.compile(
    r"AXUIElementPerformAction\(\s*(AX\w+)\s*\)\s+returned\s+(-25\d{3})"
)


def _rung_tuple(value: Any) -> tuple:
    """Rebuild an in-memory rung tuple from its JSON-safe record form.

    _json_safe turns nested tuples into lists when a rung is stored on an
    action record; the attempted-rungs set holds the original tuples.
    """
    def convert(item: Any) -> Any:
        if isinstance(item, (list, tuple)):
            return tuple(convert(part) for part in item)
        return item
    if not isinstance(value, (list, tuple)) or not value:
        return ()
    return convert(value)


def _quota_reconciliation_operation_sha256(
        name: str, arguments: dict, address_mode: str, oracle: dict,
        window_context: dict, identity: str = "", elements: list[dict] | None = None,
        original_arguments: dict | None = None) -> str:
    """Stable exact identity for reconciling a worker-deferred model call.

    Unlike UNKNOWN replay safety, quota reconciliation may remain precise. AX
    handles are replaced only when the fresh tree supplied one unique stable
    accessibility identifier; otherwise the deferred record intentionally has
    no cross-snapshot reconciliation key.
    """
    signature = _normalized_exact_operation_signature(
        name, arguments, address_mode, window_context, identity,
        elements=elements, original_arguments=original_arguments,
        oracle=oracle, stable_ax_target=True,
    )
    if not signature:
        return ""
    return hashlib.sha256(repr(signature).encode("utf-8")).hexdigest()


def _normalized_exact_operation_signature(
        name: str, arguments: dict, address_mode: str,
        window_context: dict, identity: str = "", elements: list[dict] | None = None,
        original_arguments: dict | None = None, oracle: dict | None = None,
        stable_ax_target: bool = False) -> tuple:
    """Exact target identity plus normalized driver semantics/defaults."""
    signature = list(_canonical_action_signature(
        name, arguments, address_mode, window_context, identity,
        elements=elements, original_arguments=original_arguments,
    ))
    if stable_ax_target and str(address_mode or "") == "element_ax":
        stable_address = _effect_chain_address_signature(
            arguments, address_mode, oracle or {},
        )
        if stable_address is None:
            return ()
        signature[6] = stable_address
    replay_signature = _unknown_replay_action_signature(
        name, arguments, address_mode, window_context, identity,
        elements=elements, original_arguments=original_arguments,
    )
    if isinstance(replay_signature, tuple) and len(replay_signature) == 8:
        replay_tool = str(replay_signature[1] or "")
        replay_payload = list(
            replay_signature[7] if isinstance(replay_signature[7], tuple) else ()
        )
        lowered = str(name or "").strip().lower()
        if replay_tool in {"pointer_click", "key_event"}:
            signature[1] = replay_tool
        else:
            signature[1] = lowered
        if lowered == "insert_captured_text":
            original = original_arguments \
                if isinstance(original_arguments, dict) else arguments
            generation = original.get("__worker_transfer_generation")
            if generation not in (None, ""):
                replay_payload.append(("__worker_transfer_generation", generation))
            insert_method = str(original.get("__worker_insert_method", "") or "")
            if insert_method:
                # Exact rung identity distinguishes a rejected set_value from
                # the next type_text method. UNKNOWN replay intentionally
                # strips this field above, so a method change never replays an
                # ambiguous private write.
                replay_payload.append(("__worker_insert_method", insert_method))
        signature[7] = tuple(sorted(
            replay_payload, key=lambda item: str(item[0]) if isinstance(item, tuple) else repr(item),
        ))
    return tuple(signature)


def _action_address_signature(arguments: dict, address_mode: str) -> tuple:
    """Conservative target signature used only to keep retry chains separate.

    A change of modality is an expected ladder escalation (AX -> window pixel ->
    desktop pixel), so callers compare this signature only while staying on the
    same modality.  Within one modality, a different element/coordinate/text is
    treated as a different user action and must not be silently superseded.
    """
    arguments = arguments if isinstance(arguments, dict) else {}
    mode = str(address_mode or "direct")
    if mode == "element_ax":
        token = str(arguments.get("element_token", "") or "").strip()
        if token:
            if ":" in token:
                try:
                    return ("index", int(token.rsplit(":", 1)[-1]))
                except (TypeError, ValueError):
                    pass
            return ("token_sha256", hashlib.sha256(token.encode("utf-8")).hexdigest())
        if arguments.get("element_index") is not None:
            return ("index", str(arguments.get("element_index")))
    if mode in PIXEL_ADDRESS_MODES:
        return tuple(
            (key, _finite_number(arguments.get(key)))
            for key in sorted(COORDINATE_KEYS)
            if key in arguments
        )
    keys = tuple(_normalized_action_keys(arguments))
    if keys:
        return ("keys", *keys)
    for key in ("text", "value", "input"):
        if arguments.get(key) not in (None, ""):
            return (key, str(arguments.get(key)))
    return ()


def _effect_chain_address_signature(
        arguments: dict, address_mode: str, oracle: dict) -> tuple | None:
    """Return a retry-safe target, or None when AX identity is insufficient."""
    if str(address_mode or "") != "element_ax":
        return _action_address_signature(arguments, address_mode)
    selector = (oracle or {}).get("target_selector") \
        if isinstance((oracle or {}).get("target_selector"), dict) else {}
    identifier = str(selector.get("identifier_sha256", "") or "")
    if not identifier or int(
            selector.get("identifier_match_count_at_bind", 0) or 0
    ) != 1:
        # Snapshot indices are handles, not identities.  With no stable AX
        # identifier, start a fresh lineage instead of allowing a newly
        # reindexed control to supersede another control's failed action.
        return None
    return (
        "ax_identifier_v1", identifier,
        str(selector.get("role", "") or ""),
        str(selector.get("subrole", "") or ""),
    )


def _effect_chain_target_matches(
        previous_mode: str, previous_address: tuple, previous_geometry_epoch: Any,
        current_mode: str, current_address: tuple, current_geometry_epoch: Any) -> bool:
    """Keep retry lineage exact; a modality change needs an explicit grant."""
    current_mode = str(current_mode or "")
    same_epoch = (
        current_mode not in PIXEL_ADDRESS_MODES
        or current_geometry_epoch == previous_geometry_epoch
    )
    return bool(
        current_mode == str(previous_mode or "")
        and same_epoch
        and (
            not current_address or not previous_address
            or tuple(current_address) == tuple(previous_address)
        )
    )


def _operation_signature(name: str, arguments: dict, address_mode: str) -> tuple:
    """Exact logical operation identity used to authorize one transient retry.

    Delivery mode and session plumbing are deliberately excluded; every target,
    key/text payload and pixel coordinate remains part of the signature.
    """
    arguments = arguments if isinstance(arguments, dict) else {}
    payload = []
    for key in sorted(arguments):
        if key in {"delivery_mode", "session", "session_id", "sessionId", "debug_image_out"}:
            continue
        value = arguments.get(key)
        if key in {"modifier", "modifiers", "keys"} and isinstance(value, (list, tuple)):
            value = tuple(str(item).strip().lower() for item in value)
        elif isinstance(value, (dict, list, tuple)):
            value = json.dumps(_json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        payload.append((str(key), value))
    return (str(name or "").lower(), str(address_mode or "direct"), tuple(payload))


def _desktop_operation_semantics(name: str, arguments: dict) -> tuple:
    """Return the non-address meaning that must survive a desktop escalation.

    Window-local and desktop coordinates necessarily differ, so coordinates
    cannot be compared literally across those two scopes.  Everything else
    that can change the requested operation (button/count/keys/text/options)
    remains exact.  Text is represented only by a digest and byte length.
    """
    arguments = arguments if isinstance(arguments, dict) else {}
    excluded = {
        "delivery_mode", "session", "session_id", "sessionId", "debug_image_out",
        "pid", "window_id", "scope", "display_index", "display_id", "display_uuid",
        "screen", "screen_id", "screen_index", "monitor", "monitor_id", "monitor_index",
        "element_token", "element_index", "from_zoom", *COORDINATE_KEYS,
    }
    payload = []
    for key in sorted(arguments):
        if key in excluded:
            continue
        value = arguments.get(key)
        if key in {"modifier", "modifiers", "keys"}:
            if not isinstance(value, (list, tuple)):
                value = [value] if value not in (None, "") else []
            value = tuple(str(item).strip().lower() for item in value if str(item).strip())
        elif key in {"text", "value", "input"} and value not in (None, ""):
            encoded = str(value).encode("utf-8")
            value = ("sha256", hashlib.sha256(encoded).hexdigest(), len(encoded))
        elif isinstance(value, (dict, list, tuple)):
            value = json.dumps(
                _json_safe(value), ensure_ascii=False, sort_keys=True, separators=(",", ":"),
            )
        payload.append((str(key), value))
    return (str(name or "").strip().lower(), tuple(payload))


def _effect_chain_base_signature(
        name: str, arguments: dict, oracle: dict, window_context: dict,
        original_arguments: dict | None = None) -> tuple:
    """Return the payload-aware base of one visible-effect retry lineage.

    Synthetic insertion strips the private text from driver/model logs, so its
    worker-produced digest and byte length must be restored here. Otherwise a
    later, different buffer aimed at the same control could inherit and settle
    the first buffer's retry chain.
    """
    semantic_arguments = dict(arguments or {})
    original = original_arguments if isinstance(original_arguments, dict) else {}
    if str(name or "").strip().lower() == "insert_captured_text":
        for key in (
                "__worker_transfer_sha256", "__worker_transfer_utf8_bytes",
                "__worker_transfer_generation"):
            if original.get(key) not in (None, ""):
                semantic_arguments[key] = original.get(key)
    return (
        str(name or ""),
        str((oracle or {}).get("kind", "driver_only") or "driver_only"),
        _desktop_operation_semantics(name, semantic_arguments),
        window_context.get("pid"),
        window_context.get("window_id"),
    )


def _weak_absence_label(action: dict) -> str:
    """Short model-facing description of an action: tool plus key/coordinates."""
    if not isinstance(action, dict):
        return "the previous action"
    arguments = action.get("original_arguments") \
        if isinstance(action.get("original_arguments"), dict) else {}
    if not arguments:
        arguments = action.get("arguments") if isinstance(action.get("arguments"), dict) else {}
    parts = []
    for key in ("key", "keys", "modifiers", "x", "y", "button"):
        value = arguments.get(key)
        if value not in (None, "", [], {}):
            parts.append(f"{key}={json.dumps(value, ensure_ascii=False)}")
    tool = str(action.get("tool", "") or "action")
    return f"{tool}({', '.join(parts)})" if parts else tool


def _absence_proven_exactly(action: dict) -> bool:
    """True when EFFECT_ABSENT rests on an exact postcondition.

    Exact: the uniquely bound text destination lacks the expected text, or the
    copy produced no new clipboard fingerprint. Anything else was decided by an
    unchanged coarse fingerprint, which misses small changes (a digit, the text
    caret, focus, a small icon); re-sending on that basis can duplicate input.
    """
    if not isinstance(action, dict):
        return False
    oracle = action.get("oracle") if isinstance(action.get("oracle"), dict) else {}
    if str(oracle.get("kind", "") or "") == "clipboard_copy":
        clipboard = action.get("clipboard") if isinstance(action.get("clipboard"), dict) else {}
        return clipboard.get("absence_proven") is True
    evidence = action.get("effect_evidence") if isinstance(action.get("effect_evidence"), dict) else {}
    has_expected_text = bool(oracle.get("expected_text") or oracle.get("expected_text_sha256"))
    try:
        target_matches = int(evidence.get("target_match_count", 0) or 0)
    except (TypeError, ValueError):
        target_matches = 0
    return has_expected_text and target_matches == 1


def _build_transient_foreground_grant(
        action: dict, current_window: dict) -> dict | None:
    """Create one fresh, exact foreground grant from a delivered no-effect rung."""
    if not isinstance(action, dict) or not isinstance(current_window, dict):
        return None
    arguments = action.get("arguments") if isinstance(action.get("arguments"), dict) else {}
    address_mode = str(action.get("address_mode", "") or "")
    source_window = action.get("window") if isinstance(action.get("window"), dict) else {}
    source_geometry = source_window.get("geometry") if isinstance(source_window.get("geometry"), dict) else {}
    current_geometry = current_window.get("geometry") \
        if isinstance(current_window.get("geometry"), dict) else {}
    driver_attempted = action.get("driver_attempted")
    if driver_attempted is None:  # compatibility for older durable logs/tests
        driver_attempted = action.get("executed") is True
    delivered_unverified = _action_was_delivered_unverified(action)
    clipboard_evidence = action.get("clipboard") \
        if isinstance(action.get("clipboard"), dict) else {}
    clipboard_absence_proven = bool(
        str((action.get("oracle") or {}).get("kind", "") or "") == "clipboard_copy"
        and driver_attempted is True
        and clipboard_evidence.get("absence_proven") is True
    )
    tool_name = str(action.get("tool", "") or "").lower()
    # The driver docs define delivery_mode:"foreground" for press_key/hotkey as
    # the coordinate-free escalation when a background key event is dropped
    # (front the window <1ms via the NSMenu path, act, restore the prior
    # frontmost). No pixels are involved, so Stage/thumbnail geometry must not
    # veto it. An element-addressed key press escalates by dropping the
    # snapshot-local focus handle (docs: foreground requires window_id and no
    # element addressing).
    key_escalation = tool_name in {"press_key", "hotkey"} \
        and address_mode in {"key", "element_ax"}
    if not (
            action.get("allowed") is True
            and driver_attempted is True
            and (delivered_unverified or clipboard_absence_proven)
            and action.get("is_error") is not True
            and action.get("effect_status") == EFFECT_ABSENT
            and str(arguments.get("delivery_mode", "background") or "background").lower() == "background"
            and (address_mode == "window_pixel" or key_escalation)
            and source_window.get("pid") == current_window.get("pid")
            and source_window.get("window_id") == current_window.get("window_id")
            and source_window.get("geometry_epoch") == current_window.get("geometry_epoch")
            and str(current_window.get("snapshot_id", "") or "")):
        return None
    if address_mode == "window_pixel" and not (
            str(source_geometry.get("classification", "")) == GEOMETRY_ALIGNED
            and str(current_geometry.get("classification", "")) == GEOMETRY_ALIGNED
            and int(current_window.get("geometry_stability", 0) or 0) >= 2):
        # Thumbnail-space window pixels are not valid on the fronted window;
        # only the coordinate-free key escalation is geometry-independent.
        return None
    grant_arguments = copy.deepcopy(arguments)
    grant_original = copy.deepcopy(
        action.get("original_arguments")
        if isinstance(action.get("original_arguments"), dict) else arguments
    )
    grant_driver_arguments = copy.deepcopy(
        action.get("driver_arguments")
        if isinstance(action.get("driver_arguments"), dict) else {}
    )
    grant_address_mode = address_mode
    if key_escalation:
        for stale_key in ("element_token", "element_index"):
            grant_arguments.pop(stale_key, None)
            grant_original.pop(stale_key, None)
            grant_driver_arguments.pop(stale_key, None)
        if current_window.get("window_id") is not None:
            grant_arguments.setdefault("window_id", current_window.get("window_id"))
        grant_address_mode = "key"
    signature = _canonical_action_signature(
        str(action.get("tool", "") or ""), grant_arguments, grant_address_mode,
        current_window, str(action.get("target_identity", "") or ""),
        original_arguments=grant_original,
    )
    return {
        "operation_signature": signature,
        "operation_signature_sha256": hashlib.sha256(repr(signature).encode("utf-8")).hexdigest(),
        "pid": current_window.get("pid"),
        "window_id": current_window.get("window_id"),
        "geometry_epoch": current_window.get("geometry_epoch"),
        "post_snapshot_id": str(current_window.get("snapshot_id", "") or ""),
        "effect_chain_id": str(action.get("effect_chain_id", "") or ""),
        "authorized_by_step": action.get("step"),
        "target_identity": str(action.get("target_identity", "") or ""),
        "tool": str(action.get("tool", "") or ""),
        "address_mode": grant_address_mode,
        "arguments": grant_arguments,
        "original_arguments": grant_original,
        "driver_arguments": grant_driver_arguments,
        "copy_selection_authorization": copy.deepcopy(
            action.get("copy_selection_authorization")
            if isinstance(action.get("copy_selection_authorization"), dict) else {}
        ),
        "oracle": copy.deepcopy(action.get("oracle") if isinstance(action.get("oracle"), dict) else {}),
        "state_epoch": int(action.get("verified_state_epoch", 0) or 0),
        "consumed": False,
    }


def _private_transfer_log_metadata(transfer_buffer: dict) -> dict:
    """Return the non-secret identity of the current in-memory text buffer."""
    metadata = transfer_buffer.get("metadata") \
        if isinstance(transfer_buffer, dict) and isinstance(
            transfer_buffer.get("metadata"), dict
        ) else {}
    try:
        generation = int(transfer_buffer.get("generation", 0) or 0)
    except (TypeError, ValueError, AttributeError):
        generation = 0
    try:
        char_count = int(metadata.get("char_count", 0) or 0)
    except (TypeError, ValueError):
        char_count = 0
    try:
        utf8_bytes = int(metadata.get("utf8_bytes", 0) or 0)
    except (TypeError, ValueError):
        utf8_bytes = 0
    return {
        "generation": generation,
        "sha256": str(metadata.get("sha256", "") or "").lower(),
        "char_count": char_count,
        "utf8_bytes": utf8_bytes,
    }


def _build_private_insert_type_text_grant(
        action: dict, current_window: dict, current_elements: list[dict],
        transfer_metadata: dict, *, delivery_mode: str) -> tuple[dict | None, dict]:
    """Build one worker-owned type_text rung without retaining its plaintext.

    ``set_value`` and ``type_text`` are not interchangeable retries after an
    ambiguous dispatch.  This builder accepts only an explicit set_value
    rejection/no-effect result for the background rung, or an unambiguously
    delivered background type_text whose next exact AX readback proved no
    effect for the foreground rung.  The destination must still be the same
    unique writable AX element and must expose an exactly empty value, so the
    insertion has replace-exact semantics without guessing a cursor/selection.
    """
    reason = {"authorized": False, "delivery_mode": str(delivery_mode or "")}
    if not isinstance(action, dict) or not isinstance(current_window, dict):
        reason["reason"] = "missing_source_or_window"
        return None, reason
    mode = str(delivery_mode or "").strip().lower()
    if mode not in {"background", "foreground"}:
        reason["reason"] = "invalid_delivery_mode"
        return None, reason
    if str(action.get("tool", "") or "") != "insert_captured_text" \
            or action.get("allowed") is not True \
            or action.get("driver_attempted") is not True:
        reason["reason"] = "source_is_not_attempted_private_insert"
        return None, reason
    driver_meta = action.get("driver_arguments") \
        if isinstance(action.get("driver_arguments"), dict) else {}
    source_method = str(driver_meta.get("driver_tool", "") or "").lower()
    source_transfer = driver_meta.get("transfer_buffer") \
        if isinstance(driver_meta.get("transfer_buffer"), dict) else {}
    if mode == "background":
        explicit_rejection = bool(
            action.get("delivery_outcome") == DELIVERY_DRIVER_ERROR
            and action.get("is_error") is True
            and action.get("effect_status") == EFFECT_ABSENT
        )
        delivered_no_effect = bool(
            action.get("delivery_outcome") == DELIVERY_DELIVERED_UNVERIFIED
            and action.get("is_error") is not True
            and action.get("effect_status") == EFFECT_ABSENT
        )
        if source_method != "set_value" or not (
                explicit_rejection or delivered_no_effect):
            reason["reason"] = "set_value_not_safely_settled"
            return None, reason
    else:
        source_delivery = str(
            (action.get("arguments") or {}).get("delivery_mode", "background")
            if isinstance(action.get("arguments"), dict) else "background"
        ).lower()
        if not (
                source_method == "type_text"
                and source_delivery == "background"
                and action.get("delivery_outcome") == DELIVERY_DELIVERED_UNVERIFIED
                and action.get("is_error") is not True
                and action.get("effect_status") == EFFECT_ABSENT):
            reason["reason"] = "background_type_text_not_safely_settled"
            return None, reason

    oracle = action.get("oracle") if isinstance(action.get("oracle"), dict) else {}
    selector = oracle.get("target_selector") \
        if isinstance(oracle.get("target_selector"), dict) else {}
    identifier = str(selector.get("identifier_sha256", "") or "")
    if not identifier or int(
            selector.get("identifier_match_count_at_bind", 0) or 0
    ) != 1:
        reason["reason"] = "target_has_no_unique_stable_identifier"
        return None, reason
    source_window = action.get("window") \
        if isinstance(action.get("window"), dict) else {}
    source_snapshot_id = str(action.get("snapshot_id", "") or "")
    source_post_snapshot_id = str(action.get("post_snapshot_id", "") or "")
    current_snapshot_id = str(current_window.get("snapshot_id", "") or "")
    if source_window.get("pid") != current_window.get("pid") \
            or source_window.get("window_id") != current_window.get("window_id") \
            or not current_snapshot_id:
        reason["reason"] = "target_window_changed_or_not_fresh"
        return None, reason
    if mode == "background" and (
            current_snapshot_id == source_snapshot_id
            or (source_post_snapshot_id and source_post_snapshot_id != current_snapshot_id)):
        reason["reason"] = "background_fallback_requires_next_fresh_observation"
        return None, reason
    if mode == "foreground" and source_post_snapshot_id != current_snapshot_id:
        reason["reason"] = "foreground_requires_exact_absence_observation"
        return None, reason

    identity_candidates = _target_selector_candidates(current_elements, selector)
    writable = [item for item in identity_candidates if _is_writable_ax_element(item)]
    if len(identity_candidates) != 1 or len(writable) != 1:
        reason.update({
            "reason": "target_is_missing_ambiguous_or_not_writable",
            "target_identity_match_count": len(identity_candidates),
            "target_writable_match_count": len(writable),
        })
        return None, reason
    target = writable[0]
    if not isinstance(target.get("value"), str) or target.get("value") != "":
        reason.update({
            "reason": "target_value_is_not_known_empty",
            "target_value_known": isinstance(target.get("value"), str),
            "target_value_empty": target.get("value") == "",
        })
        return None, reason

    current_transfer = {
        "generation": int(transfer_metadata.get("generation", 0) or 0),
        "sha256": str(transfer_metadata.get("sha256", "") or "").lower(),
        "char_count": int(transfer_metadata.get("char_count", 0) or 0),
        "utf8_bytes": int(transfer_metadata.get("utf8_bytes", 0) or 0),
    }
    expected_hash = str(
        source_transfer.get("sha256", "")
        or oracle.get("transfer_sha256", "")
        or oracle.get("expected_text_sha256", "")
        or ""
    ).lower()
    try:
        expected_generation = int(
            source_transfer.get("generation", oracle.get("transfer_generation", 0)) or 0
        )
    except (TypeError, ValueError):
        expected_generation = 0
    if not expected_hash or not current_transfer["sha256"] \
            or expected_hash != current_transfer["sha256"] \
            or expected_generation != current_transfer["generation"] \
            or current_transfer["utf8_bytes"] <= 0:
        reason["reason"] = "private_transfer_generation_or_hash_changed"
        return None, reason

    arguments = {
        "pid": int(current_window.get("pid")),
        "window_id": int(current_window.get("window_id")),
        "delivery_mode": mode,
    }
    token = str(target.get("element_token", "") or "")
    if token:
        arguments["element_token"] = token
    else:
        try:
            arguments["element_index"] = int(target.get("element_index"))
        except (TypeError, ValueError):
            reason["reason"] = "fresh_target_has_no_driver_address"
            return None, reason
    original_arguments = {
        **arguments,
        "__worker_transfer_sha256": current_transfer["sha256"],
        "__worker_transfer_utf8_bytes": current_transfer["utf8_bytes"],
        "__worker_transfer_generation": current_transfer["generation"],
        "__worker_insert_method": "type_text",
    }
    grant_oracle = {
        "kind": "text_mutation",
        "address_mode": "element_ax",
        "text_write_semantics": "replace_exact",
        "transfer_generation": current_transfer["generation"],
        "transfer_sha256": current_transfer["sha256"],
        "expected_text_sha256": current_transfer["sha256"],
        "expected_char_count": current_transfer["char_count"],
        "expects_visual_change": True,
        "visually_silent": False,
        "non_idempotent": True,
        "replay_sensitive": True,
        "private_transfer": True,
        "delivery_method": "type_text",
    }
    grant_oracle = _bind_oracle_to_ax_target(
        grant_oracle, arguments, "element_ax", current_elements,
        original_arguments=original_arguments,
    )
    operation = _canonical_action_signature(
        "insert_captured_text", arguments, "element_ax", current_window,
        str(action.get("target_identity", "") or ""),
        elements=current_elements, original_arguments=original_arguments,
    )
    grant = {
        "grant_kind": f"private_insert_type_text_{mode}",
        "operation_signature": operation,
        "operation_signature_sha256": hashlib.sha256(
            repr(operation).encode("utf-8")
        ).hexdigest(),
        "pid": current_window.get("pid"),
        "window_id": current_window.get("window_id"),
        "post_snapshot_id": str(current_window.get("snapshot_id", "") or ""),
        "authorized_by_step": action.get("step"),
        "source_action_index": action.get("_action_index"),
        "effect_chain_id": str(action.get("effect_chain_id", "") or ""),
        "target_identity": str(action.get("target_identity", "") or ""),
        "address_mode": "element_ax",
        "arguments": arguments,
        "original_arguments": original_arguments,
        "oracle": grant_oracle,
        "private_transfer": current_transfer,
        "state_epoch": int(action.get("verified_state_epoch", 0) or 0),
        "consumed": False,
    }
    reason.update({
        "authorized": True,
        "reason": "fresh_unique_empty_ax_target",
        "authorized_by_step": action.get("step"),
        "target_selector_sha256": hashlib.sha256(
            repr(_ax_target_selector_signature(selector)).encode("utf-8")
        ).hexdigest(),
        "transfer_sha256": current_transfer["sha256"],
        "transfer_generation": current_transfer["generation"],
    })
    return grant, reason


def _action_was_delivered_unverified(action: dict) -> bool:
    """Accept explicit delivery truth, with a narrow legacy-log fallback."""
    if not isinstance(action, dict):
        return False
    delivery_outcome = action.get("delivery_outcome")
    if delivery_outcome not in (None, ""):
        return delivery_outcome == DELIVERY_DELIVERED_UNVERIFIED
    attempted = action.get("driver_attempted")
    if attempted is None:
        attempted = action.get("executed") is True
    return bool(attempted is True and action.get("is_error") is not True)


def _transient_foreground_authorized(
        grant: dict | None, name: str, arguments: dict,
        address_mode: str, window_context: dict,
        identity: str = "", original_arguments: dict | None = None) -> tuple[bool, dict]:
    """Validate one explicit grant; worker refusals and history never authorize it."""
    if str(arguments.get("delivery_mode", "background") or "background").lower() != "foreground":
        return True, {}
    if address_mode not in {"window_pixel", "key"}:
        return False, {"reason": "AX-addressed actions remain background-only."}
    if not isinstance(grant, dict) or grant.get("consumed") is True:
        return False, {
            "reason": "No fresh exact background no-effect grant is available.",
        }
    geometry = window_context.get("geometry") if isinstance(window_context.get("geometry"), dict) else {}
    desired = _canonical_action_signature(
        name, arguments, address_mode, window_context,
        identity or str(grant.get("target_identity", "") or ""),
        original_arguments=original_arguments,
    )
    geometry_ok = True
    if address_mode == "window_pixel":
        # Pixel replay needs trustworthy screen geometry. The key escalation is
        # coordinate-free by the driver docs (front <1ms, act, restore), so
        # Stage/thumbnail geometry must not veto it.
        geometry_ok = bool(
            str(geometry.get("classification", "")) == GEOMETRY_ALIGNED
            and int(window_context.get("geometry_stability", 0) or 0) >= 2
        )
    matches = bool(
        desired == grant.get("operation_signature")
        and window_context.get("pid") == grant.get("pid")
        and window_context.get("window_id") == grant.get("window_id")
        and window_context.get("geometry_epoch") == grant.get("geometry_epoch")
        and str(window_context.get("snapshot_id", "") or "") == str(grant.get("post_snapshot_id", "") or "")
        and geometry_ok
    )
    if not matches:
        return False, {
            "reason": "The requested foreground operation does not match the one fresh exact grant.",
            "operation_signature_sha256": hashlib.sha256(repr(desired).encode("utf-8")).hexdigest(),
        }
    return True, {
        "authorized_by_step": grant.get("authorized_by_step"),
        "authorized_by_effect_chain": grant.get("effect_chain_id", ""),
        "operation_signature_sha256": grant.get("operation_signature_sha256", ""),
    }


def _window_delivery_ladder_exhausted(actions: list[dict], window_context: dict) -> bool:
    required = {
        ("window_pixel", "background"),
        ("window_pixel", "foreground"),
    }
    pid = window_context.get("pid") if isinstance(window_context, dict) else None
    window_id = window_context.get("window_id") if isinstance(window_context, dict) else None
    relevant = []
    for item in reversed(actions or []):
        if not isinstance(item, dict):
            continue
        grounded = item.get("window") if isinstance(item.get("window"), dict) else {}
        if grounded.get("pid") != pid or grounded.get("window_id") != window_id:
            continue
        if item.get("effect_status") == EFFECT_CONFIRMED:
            # Confirmed progress on this window bars all OLDER no-effect
            # evidence: breakers may only consume evidence fresher than the
            # last proven effect (a task was once killed by two stale
            # no-effect clicks AFTER the final write had already confirmed).
            break
        if item.get("effect_status") != EFFECT_ABSENT \
                or not _action_was_delivered_unverified(item):
            continue
        relevant.append(item)
        if len(relevant) >= 6:
            break
    if not relevant:
        return False
    latest_tool = str(relevant[0].get("tool", "") or "")
    latest_oracle = str((relevant[0].get("oracle") or {}).get("kind", "") or "")
    latest_chain = str(relevant[0].get("effect_chain_id", "") or "")
    rungs = set()
    for item in relevant:
        item_chain = str(item.get("effect_chain_id", "") or "")
        if latest_chain and item_chain != latest_chain:
            continue
        if str(item.get("tool", "") or "") != latest_tool:
            continue
        if str((item.get("oracle") or {}).get("kind", "") or "") != latest_oracle:
            continue
        arguments = item.get("arguments") if isinstance(item.get("arguments"), dict) else {}
        delivery = str(arguments.get("delivery_mode", "background") or "background").lower()
        rungs.add((str(item.get("address_mode", "") or ""), delivery))
    return required <= rungs


def _verify_action_effect(
        action: dict, fingerprint_components: dict, window_context: dict,
        elements: list[dict]) -> tuple[str, dict]:
    """Evaluate one delivered action against its next fresh observation."""
    spec = action.get("oracle") if isinstance(action.get("oracle"), dict) else {}
    kind = str(spec.get("kind", "driver_only") or "driver_only")
    expected_text = str(spec.get("expected_text", "") or "")
    expected_text_sha256 = str(spec.get("expected_text_sha256", "") or "")
    before_window = action.get("window") if isinstance(action.get("window"), dict) else {}
    before_key = (before_window.get("pid"), before_window.get("window_id"))
    after_key = (window_context.get("pid"), window_context.get("window_id"))
    before_geometry = before_window.get("geometry") if isinstance(before_window.get("geometry"), dict) else {}
    after_geometry = window_context.get("geometry") if isinstance(window_context.get("geometry"), dict) else {}
    before_scope = (
        "desktop" if before_window.get("desktop_snapshot")
        or str(before_geometry.get("scope", "") or "") == "desktop" else "window"
    )
    after_scope = (
        "desktop" if window_context.get("desktop_snapshot")
        or str(after_geometry.get("scope", "") or "") == "desktop" else "window"
    )
    explicit_baseline = action.get("verification_fingerprint_components")
    has_explicit_baseline = isinstance(explicit_baseline, dict) and bool(explicit_baseline)
    baseline = explicit_baseline if has_explicit_baseline else action.get("fingerprint_components")
    baseline = baseline if isinstance(baseline, dict) else {}
    comparison_scope = str(
        action.get("verification_scope", before_scope if not has_explicit_baseline else "") or ""
    )
    before_oracle = str(baseline.get("oracle", "") or "")
    after_oracle = str(fingerprint_components.get("oracle", "") or "")
    before_basis = _fingerprint_basis(baseline)
    after_basis = _fingerprint_basis(fingerprint_components)
    evidence = {
        "kind": kind,
        "before_window": list(before_key),
        "after_window": list(after_key),
        "before_oracle": before_oracle,
        "after_oracle": after_oracle,
        "before_basis": before_basis,
        "after_basis": after_basis,
        "before_scope": before_scope,
        "after_scope": after_scope,
        "comparison_scope": comparison_scope,
        "expected_text_present": False,
        "expected_text_exact": False,
        "expected_text_hash_present": False,
    }
    if action.get("effect_confirmed") is True:
        evidence["driver_confirmed"] = True
        return EFFECT_CONFIRMED, evidence
    resolved_target_pid = action.get("resolved_target_pid")
    if resolved_target_pid in (None, ""):
        identity_key, _, identity_value = str(action.get("target_identity", "") or "").partition(":")
        if identity_key == "pid":
            resolved_target_pid = identity_value
    target_grounded = False
    if after_key[0] is not None:
        if resolved_target_pid in (None, ""):
            target_grounded = before_key == (None, None)
        else:
            try:
                target_grounded = int(after_key[0]) == int(resolved_target_pid)
            except (TypeError, ValueError):
                target_grounded = False
    if kind == "topology" and target_grounded:
        evidence["reason"] = "A fresh snapshot is grounded to the app-switch target."
        return EFFECT_CONFIRMED, evidence
    if kind == "topology":
        evidence["reason"] = (
            "The fresh window is not grounded to the requested app-switch target."
        )
        return EFFECT_INDETERMINATE, evidence
    if kind == "create_or_open" and before_key != after_key:
        evidence["reason"] = (
            "A different current window alone does not prove that this create/open action produced it."
        )
        return EFFECT_INDETERMINATE, evidence
    if kind in {"text_mutation", "paste"} and before_key != after_key:
        evidence["reason"] = (
            "Text destination verification requires the exact same grounded PID and window_id; "
            "another window's AX tree cannot prove this write."
        )
        return EFFECT_INDETERMINATE, evidence
    if kind in {"clipboard_copy", "selection", "driver_only"}:
        evidence["reason"] = "This action has no reliable window-visual oracle."
        return EFFECT_INDETERMINATE, evidence
    if before_key != after_key and after_key != (None, None) \
            and kind not in {"text_mutation", "paste", "create_or_open"}:
        if target_grounded:
            evidence["reason"] = "The action produced or selected another target-owned window."
            return EFFECT_CONFIRMED, evidence
        evidence["reason"] = (
            "A foreign current-window change cannot prove an effect in the grounded target app."
        )
        return EFFECT_INDETERMINATE, evidence
    target_selector = spec.get("target_selector") \
        if isinstance(spec.get("target_selector"), dict) else {}
    if expected_text or expected_text_sha256:
        target_proof = _target_text_postcondition(
            elements, target_selector,
            expected_text=expected_text, expected_sha256=expected_text_sha256,
            write_semantics=str(spec.get("text_write_semantics", "") or ""),
        )
        evidence.update(target_proof)
        if target_proof.get("expected_state_preexisting") is True \
                and target_proof.get("action_specific_text_transition") is not True:
            evidence["reason"] = (
                "The requested text state already existed in the bound AX destination before "
                "delivery, so the unchanged postcondition cannot prove this action landed."
            )
            return EFFECT_INDETERMINATE, evidence
        if target_proof.get("action_specific_text_transition") is True:
            evidence["reason"] = (
                "The uniquely bound writable AX destination made the exact expected text transition."
            )
            return EFFECT_CONFIRMED, evidence
        if target_proof.get("expected_text_hash_present") is True:
            evidence["reason"] = (
                "The exact AX text hash was read back from the one uniquely bound destination."
            )
            return EFFECT_CONFIRMED, evidence
        if target_proof.get("expected_text_present") is True:
            evidence["reason"] = (
                "The AX text postcondition is present on the one uniquely bound destination."
            )
            return EFFECT_CONFIRMED, evidence
        if target_selector:
            if int(target_proof.get("target_match_count", 0) or 0) == 1:
                evidence["reason"] = (
                    "The uniquely bound AX destination does not contain the expected text postcondition."
                )
                return EFFECT_ABSENT, evidence
            evidence["reason"] = (
                "The original AX destination has no unique semantic successor in the fresh tree; "
                "text verification refuses to use another element."
            )
            return EFFECT_INDETERMINATE, evidence
        if kind == "text_mutation":
            evidence["reason"] = (
                "No stable AX destination selector was captured, so a whole-tree text match cannot prove this write."
            )
            return EFFECT_INDETERMINATE, evidence
    if before_scope != after_scope and (
            not has_explicit_baseline or comparison_scope != after_scope):
        evidence["reason"] = (
            "The pre/post screenshots use different scopes and no comparable target-window baseline exists."
        )
        return EFFECT_INDETERMINATE, evidence
    before_semantic = str(baseline.get("semantic_elements_sha256", "") or "")
    after_semantic = str(fingerprint_components.get("semantic_elements_sha256", "") or "")
    before_geometry_class = str(before_geometry.get("classification", "") or "")
    after_geometry_class = str(after_geometry.get("classification", "") or "")
    if not (has_explicit_baseline and comparison_scope == after_scope) \
            and before_semantic and before_semantic == after_semantic \
            and before_geometry_class != after_geometry_class:
        evidence["reason"] = (
            "Only compositor/window geometry changed while the semantic AX state stayed identical; "
            "that does not prove the preceding action caused an application effect."
        )
        return EFFECT_INDETERMINATE, evidence
    if before_oracle and after_oracle and before_basis != after_basis:
        # A screenshot-backed oracle and an AX-only oracle always differ;
        # inequality across bases proves nothing about the UI.
        evidence["reason"] = (
            "The pre/post observations use different evidence bases "
            f"({before_basis or 'unknown'} vs {after_basis or 'unknown'}); "
            "oracle comparison across bases cannot prove or disprove the effect."
        )
        return EFFECT_INDETERMINATE, evidence
    if before_oracle and after_oracle and before_oracle != after_oracle:
        evidence["reason"] = "The semantic/perceptual observation changed."
        return EFFECT_CONFIRMED, evidence
    if before_oracle and after_oracle and before_oracle == after_oracle:
        if before_basis == "ax_only":
            evidence["reason"] = (
                "The next AX-only semantic observation is unchanged; no screenshot "
                "was available for perceptual comparison."
            )
        else:
            evidence["reason"] = "The next stable semantic/perceptual observation is unchanged."
        return EFFECT_ABSENT, evidence
    evidence["reason"] = "There is insufficient pre/post evidence to prove or disprove the effect."
    return EFFECT_INDETERMINATE, evidence


def _unknown_delivery_has_strong_confirmation(
        action: dict, status: str, effect_evidence: dict) -> bool:
    """Accept only action-specific postconditions after a lost driver reply.

    A generic screenshot/AX delta can be animation or unrelated compositor
    activity. Exact text/hash readback and exact topology/window postconditions
    are strong enough to prove that an ambiguous non-repeatable call landed.
    """
    if status != EFFECT_CONFIRMED:
        return False
    spec = action.get("oracle") if isinstance(action.get("oracle"), dict) else {}
    evidence = effect_evidence if isinstance(effect_evidence, dict) else {}
    if evidence.get("target_has_stable_identifier") is True \
            and evidence.get("target_writable") is True \
            and evidence.get("action_specific_text_transition") is True:
        return True
    kind = str(spec.get("kind", "") or "")
    if str(action.get("tool", "") or "").lower() in APP_BIND_TOOLS:
        # A lost launch reply cannot prove whether this call created/selected
        # the requested instance (especially with open -n).  Observing an
        # already-running target is not action-specific enough to replay.
        return False
    before_window = tuple(evidence.get("before_window") or ())
    after_window = tuple(evidence.get("after_window") or ())
    resolved_target_pid = action.get("resolved_target_pid")
    if resolved_target_pid in (None, ""):
        identity_key, _, identity_value = str(
            action.get("target_identity", "") or ""
        ).partition(":")
        if identity_key == "pid":
            resolved_target_pid = identity_value
    if kind == "topology" and after_window and after_window != (None, None) \
            and resolved_target_pid not in (None, ""):
        try:
            return int(after_window[0]) == int(resolved_target_pid)
        except (TypeError, ValueError, IndexError):
            return False
    # A different current window does not prove Cmd+N/Cmd+O created anything;
    # Stage Manager or the user may simply have switched to an existing app.
    # Without an explicit same-PID before/after window-set delta, keep the
    # UNKNOWN barrier active.
    if kind == "create_or_open":
        return False
    return False


def _reconcile_confirmed_retry(actions: list[dict], confirmed_index: int) -> None:
    if not (0 <= confirmed_index < len(actions)):
        return
    current = actions[confirmed_index]
    oracle = current.get("oracle") if isinstance(current.get("oracle"), dict) else {}
    kind = str(oracle.get("kind", "") or "")
    current_window = current.get("window") if isinstance(current.get("window"), dict) else {}
    current_pid = current_window.get("pid")
    # Downstream confirmation may settle only the exact transfer generation
    # that supplied it. A later AX capture/copy is a hard boundary even when an
    # older copy remains nearby in the action list.
    try:
        current_transfer_generation = int(oracle.get("transfer_generation", 0) or 0)
    except (TypeError, ValueError):
        current_transfer_generation = 0
    current_transfer_hash = str(oracle.get("transfer_sha256", "") or "")
    if kind in {"paste", "text_mutation"} \
            and current_transfer_generation > 0 and current_transfer_hash:
        for previous in reversed(actions[:confirmed_index]):
            previous_oracle = previous.get("oracle") if isinstance(previous.get("oracle"), dict) else {}
            previous_kind = str(previous_oracle.get("kind", "") or "")
            if previous_kind not in {"clipboard_copy", "transfer_capture"}:
                continue
            try:
                previous_generation = int(
                    previous_oracle.get("transfer_generation", 0) or 0
                )
            except (TypeError, ValueError):
                previous_generation = 0
            previous_hash = str(previous_oracle.get("transfer_sha256", "") or "")
            if (previous_generation, previous_hash) != (
                    current_transfer_generation, current_transfer_hash):
                break
            if previous_kind == "clipboard_copy" \
                    and previous.get("effect_status") == EFFECT_INDETERMINATE:
                previous["effect_status"] = EFFECT_CONFIRMED_DOWNSTREAM
                previous["effect_evidence"] = {
                    "reason": (
                        "A downstream destination mutation confirmed the exact "
                        "transfer generation and hash."
                    ),
                    "confirmed_by_action": confirmed_index,
                }
                authorization = previous.get("copy_selection_authorization") \
                    if isinstance(previous.get("copy_selection_authorization"), dict) else {}
                authorized_step = authorization.get("authorized_by_step")
                if authorized_step is not None:
                    for selection in reversed(actions[:confirmed_index]):
                        if selection.get("step") != authorized_step:
                            continue
                        if selection.get("effect_status") == EFFECT_INDETERMINATE:
                            selection["effect_status"] = EFFECT_CONFIRMED_DOWNSTREAM
                            selection["effect_evidence"] = {
                                "reason": (
                                    "The exact authorized copy and downstream transfer "
                                    "generation were confirmed."
                                ),
                                "confirmed_by_action": confirmed_index,
                            }
                        break
            break
    # A later confirmed rung supersedes an earlier no-effect delivery only in
    # the same explicit, non-empty logical chain. Forensic-only records carry no
    # chain and must never be merged by a pid/oracle fallback.
    current_chain = str(current.get("effect_chain_id", "") or "")
    if current_chain:
        for previous in reversed(actions[:confirmed_index]):
            # Quota-deferred calls never reached the driver. They are not delivery
            # rungs and may be reconciled only by the exact operation-hash pass
            # below, never merely because a nearby effect chain later succeeded.
            if previous.get("quota_deferred"):
                continue
            if not _action_was_delivered_unverified(previous):
                continue
            previous_oracle = previous.get("oracle") if isinstance(previous.get("oracle"), dict) else {}
            previous_window = previous.get("window") if isinstance(previous.get("window"), dict) else {}
            previous_chain = str(previous.get("effect_chain_id", "") or "")
            if previous_chain != current_chain:
                continue
            if previous_window.get("pid") != current_pid:
                continue
            if str(previous_oracle.get("kind", "") or "") != kind:
                continue
            if previous.get("effect_status") in {EFFECT_ABSENT, EFFECT_NOT_DELIVERED}:
                previous["effect_status"] = EFFECT_SUPERSEDED
                previous["superseded_by_action"] = confirmed_index

    # A mutation deferred solely because the model batched two calls never
    # reached the driver. A later confirmed retry resolves that forensic record
    # only when its canonical operation matches either the confirmed rung or a
    # real delivered rung in the same explicit escalation chain. This preserves
    # exactness across window->desktop coordinate/address remapping without ever
    # blessing an unrelated quota-deferred payload.
    current_operation = str(current.get("operation_signature_sha256", "") or "")
    current_quota_signature = str(
        current.get("quota_reconciliation_signature_sha256", "") or ""
    )
    confirmed_chain_operations = {current_operation} if current_operation else set()
    confirmed_chain_quota_signatures = (
        {current_quota_signature} if current_quota_signature else set()
    )
    if current_chain:
        for delivered in actions[:confirmed_index + 1]:
            if not isinstance(delivered, dict):
                continue
            if str(delivered.get("effect_chain_id", "") or "") != current_chain:
                continue
            if not _action_was_delivered_unverified(delivered):
                continue
            delivered_operation = str(
                delivered.get("operation_signature_sha256", "") or ""
            )
            if delivered_operation:
                confirmed_chain_operations.add(delivered_operation)
            delivered_quota_signature = str(
                delivered.get("quota_reconciliation_signature_sha256", "") or ""
            )
            if delivered_quota_signature:
                confirmed_chain_quota_signatures.add(delivered_quota_signature)
    if confirmed_chain_operations or confirmed_chain_quota_signatures:
        for previous in reversed(actions[:confirmed_index]):
            if not previous.get("quota_deferred"):
                continue
            previous_operation = str(
                previous.get("operation_signature_sha256", "") or ""
            )
            previous_quota_signature = str(
                previous.get("quota_reconciliation_signature_sha256", "") or ""
            )
            exact_match = bool(
                previous_operation
                and previous_operation in confirmed_chain_operations
            )
            stable_quota_match = bool(
                previous_quota_signature
                and previous_quota_signature in confirmed_chain_quota_signatures
            )
            if not exact_match and not stable_quota_match:
                continue
            if previous.get("effect_status") == EFFECT_NOT_DELIVERED:
                previous["effect_status"] = EFFECT_SUPERSEDED
                previous["superseded_by_action"] = confirmed_index
                previous["effect_evidence"] = {
                    "reason": "The exact quota-deferred operation was later delivered and confirmed.",
                    "confirmed_by_action": confirmed_index,
                }
            break


def _reconcile_private_insert_fallback(actions: list[dict], confirmed_index: int) -> None:
    """Supersede only explicit worker-owned private-insert ancestors."""
    if not (0 <= confirmed_index < len(actions)):
        return
    current = actions[confirmed_index]
    visited: set[int] = set()
    source = current.get("private_insert_source_action_index")
    while source is not None:
        try:
            source_index = int(source)
        except (TypeError, ValueError):
            return
        if source_index in visited or not (0 <= source_index < len(actions)):
            return
        visited.add(source_index)
        previous = actions[source_index]
        if str(previous.get("tool", "") or "") != "insert_captured_text":
            return
        previous["effect_status"] = EFFECT_SUPERSEDED
        previous["superseded_by_step"] = current.get("step")
        previous["superseded_by_action"] = confirmed_index
        previous["fallback_resolution"] = {
            "kind": "private_insert_type_text",
            "confirmed_step": current.get("step"),
            "transport_truth_preserved": True,
        }
        source = previous.get("private_insert_source_action_index")


def _reconcile_unknown_launch_routing(actions: list[dict], confirmed_index: int) -> None:
    """Settle routing usability without claiming a lost launch reply caused it."""
    if not (0 <= confirmed_index < len(actions)):
        return
    confirmed = actions[confirmed_index]
    confirmed_window = confirmed.get("window") \
        if isinstance(confirmed.get("window"), dict) else {}
    confirmed_pid = confirmed_window.get("pid")
    if confirmed_pid in (None, ""):
        return
    for previous in reversed(actions[:confirmed_index]):
        if str(previous.get("tool", "") or "").lower() not in APP_BIND_TOOLS:
            continue
        if previous.get("delivery_outcome") != DELIVERY_UNKNOWN_AFTER_ATTEMPT:
            continue
        if previous.get("effect_status") != EFFECT_INDETERMINATE:
            continue
        if previous.get("routing_binding_candidate_pid") in (None, ""):
            continue
        try:
            same_pid = int(previous.get("routing_binding_candidate_pid")) \
                == int(confirmed_pid)
        except (TypeError, ValueError):
            same_pid = False
        if not same_pid:
            continue
        previous["effect_status"] = EFFECT_CONFIRMED_DOWNSTREAM
        previous["effect_evidence"] = {
            "reason": (
                "A later confirmed user effect proves that the requested target process was "
                "successfully bound and usable. It does not prove that the lost launch reply "
                "created or selected that process."
            ),
            "confirmed_by_action": confirmed_index,
            "launch_causality_confirmed": False,
            "unknown_replay_barrier_preserved": True,
        }
        previous["routing_only_settled"] = True
        break


def _effect_report(actions: list[dict]) -> dict:
    completed = []
    unresolved = []
    failed = []
    for index, action in enumerate(actions or []):
        item = {
            "index": index,
            "step": action.get("step"),
            "tool": action.get("tool"),
            "target": action.get("resolved_target_label") \
                or (action.get("window") or {}).get("app") \
                or action.get("target_identity", ""),
            "status": action.get("effect_status", EFFECT_NOT_DELIVERED),
            "error_code": action.get("error_code", ""),
        }
        status = item["status"]
        if status in {EFFECT_CONFIRMED, EFFECT_CONFIRMED_DOWNSTREAM, EFFECT_SUPERSEDED}:
            completed.append(item)
        elif status in {EFFECT_PENDING, EFFECT_ABSENT, EFFECT_INDETERMINATE}:
            unresolved.append(item)
        elif status == EFFECT_NOT_DELIVERED:
            failed.append(item)
    return {
        "completed": completed,
        "unresolved": unresolved,
        "failed": failed,
        "partial": bool(unresolved or failed),
    }


def _completion_result(config: dict, evidence: dict, answer: str) -> dict:
    """Never turn a model completion claim into success beyond verified effects."""
    report = _effect_report(list(evidence.get("actions") or []))
    if report.get("partial"):
        evidence["failure_source"] = "progress"
    else:
        evidence["failure_source"] = ""
    metadata = _salvage_metadata(config, evidence, partial=bool(report.get("partial")))
    if report.get("partial"):
        metadata["unverified_model_answer"] = str(answer or "")
        completed = len(report.get("completed") or [])
        unresolved = len(report.get("unresolved") or [])
        failed = len(report.get("failed") or [])
        return {
            "ok": False,
            "error": (
                "CU_TASK_PARTIAL: completion was not accepted because one or more requested UI effects "
                "remain unverified or were not delivered."
            ),
            "answer": (
                f"Computer Use only partially completed the task: {completed} action effect(s) confirmed; "
                f"{unresolved} unverified; {failed} not delivered. "
                f"Unverified model report: {str(answer or '').strip()}"
            ).strip(),
            "metadata": metadata,
        }
    return {"ok": True, "answer": str(answer or "Computer Use task completed."), "metadata": metadata}


def _clip(text: str, limit: int) -> str:
    text = str(text or "").strip()
    return text if len(text) <= limit else text[:limit].rstrip() + "\n[...truncated]"


def _resize_screenshot(image_bytes: bytes) -> tuple[bytes, float, tuple[int, int]]:
    with Image.open(io.BytesIO(image_bytes)) as source:
        source.load()
        width, height = source.size
        ratio = min(1.0, 1280.0 / max(1, width))
        if ratio < 1:
            source = source.resize((round(width * ratio), round(height * ratio)), Image.Resampling.LANCZOS)
        output = io.BytesIO()
        source.convert("RGB").save(output, format="PNG", optimize=True)
        return output.getvalue(), ratio, (width, height)


def _save_final_screenshot(path: str, image_bytes: bytes) -> str:
    if not path or not image_bytes:
        return ""
    try:
        target = Path(path).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(image_bytes)
        return str(target)
    except Exception:
        return ""


def _openai_tools(tools: list[dict]) -> list[dict]:
    result = [
        {
            "type": "function",
            "function": {
                "name": item["name"],
                "description": item["description"],
                "parameters": _model_input_schema(item["inputSchema"]),
            },
        }
        for item in tools
    ]
    result.append({
        "type": "function",
        "function": {
            "name": "finish",
            "description": "Finish the desktop task and return the final answer.",
            "parameters": {
                "type": "object",
                "properties": {"answer": {"type": "string"}},
                "required": ["answer"],
            },
        },
    })
    return result


def _assistant_message_dict(message: Any) -> dict:
    tool_calls = []
    for call in getattr(message, "tool_calls", None) or []:
        tool_calls.append({
            "id": str(call.id),
            "type": "function",
            "function": {"name": str(call.function.name), "arguments": str(call.function.arguments or "{}")},
        })
    result = {"role": "assistant", "content": str(getattr(message, "content", "") or "")}
    if tool_calls:
        result["tool_calls"] = tool_calls
    return result


def _model_call(config: dict, messages: list[dict], tools: list[dict]) -> Any:
    client = OpenAI(
        api_key=str(config.get("api_key", "")),
        base_url=str(config.get("endpoint", "")),
        timeout=float(config.get("llm_timeout", 120) or 120),
        max_retries=1,
    )
    kwargs = {
        "model": str(config.get("model", "")),
        "messages": messages,
        "tools": tools,
        "tool_choice": "auto",
    }
    if not tools:
        # Plain-text calls (e.g. the visual arbiter): some relays reject an
        # empty tools array outright.
        kwargs.pop("tools", None)
        kwargs.pop("tool_choice", None)
    response = client.chat.completions.create(**kwargs)
    return response.choices[0].message


async def _call_tool(session: ClientSession, name: str, arguments: dict, timeout: float) -> Any:
    return await asyncio.wait_for(session.call_tool(name, arguments), timeout=timeout)


class _FatalTaskError(RuntimeError):
    """A verdict, not a transient failure — bypasses the per-step retry ladder."""


class _DesktopIsolationUnavailable(RuntimeError):
    """Private desktop capability failed before any model action; AX may downgrade."""


class _ClipboardBaselineUnavailable(RuntimeError):
    """The worker cannot safely install/restore its private copy probe."""


class _IsolatedCuaDaemon:
    """One task-private, LaunchServices-owned cua-driver 0.8.3 daemon.

    ``capture_scope`` is global inside a daemon *and* persisted under HOME in
    0.8.3.  A private socket alone is therefore not an isolation boundary.  We
    launch the signed app with both a unique socket and a unique HOME, force the
    MCP proxy to that exact socket, then prove the PID/argv before allowing any
    desktop capture.  The user's real ``~/.cua-driver/config.json`` is hashed
    before launch and again during cleanup; this class never writes it.
    """

    APP_BINARY = Path("/Applications/CuaDriver.app/Contents/MacOS/cua-driver")
    BUNDLE_ID = "com.trycua.driver"
    REQUIRED_VERSION = "0.8.3"
    ROOT_PREFIX = "broccoli-cua-task-"

    def __init__(self, driver_command: str, *, startup_timeout: float = 12.0):
        self.driver_command = str(Path(driver_command).resolve())
        self.startup_timeout = max(1.0, float(startup_timeout))
        self.root = Path(tempfile.mkdtemp(prefix=self.ROOT_PREFIX, dir="/private/tmp"))
        os.chmod(self.root, 0o700)
        self.private_home = self.root / "home"
        self.private_home.mkdir(mode=0o700)
        self.socket_path = self.root / "driver.sock"
        self.pid_file = self.private_home / "Library" / "Caches" / "cua-driver" / "cua-driver.pid"
        self.stdout_path = self.root / "serve.stdout.log"
        self.stderr_path = self.root / "serve.stderr.log"
        self.private_config = self.private_home / ".cua-driver" / "config.json"
        self.real_config = Path(os.path.expanduser("~/.cua-driver/config.json"))
        self.real_config_before = self._file_state(self.real_config)
        self.pid: int | None = None
        self.pid_command = ""
        self.started = False
        self.closed = False
        self.cleanup_error = ""

    @staticmethod
    def _file_state(path: Path) -> dict:
        try:
            data = path.read_bytes()
        except FileNotFoundError:
            return {"exists": False, "sha256": "", "size": 0}
        except Exception as exc:
            return {"exists": None, "sha256": "", "size": -1, "error": str(exc)}
        return {
            "exists": True,
            "sha256": hashlib.sha256(data).hexdigest(),
            "size": len(data),
        }

    @classmethod
    def supported(cls, driver_command: str) -> bool:
        if sys.platform != "darwin" or not cls.APP_BINARY.is_file():
            return False
        try:
            if Path(driver_command).resolve() != cls.APP_BINARY.resolve():
                return False
            probe = subprocess.run(
                [str(cls.APP_BINARY), "--version"], capture_output=True, text=True, timeout=4,
            )
        except Exception:
            return False
        version_text = (probe.stdout or "") + "\n" + (probe.stderr or "")
        return probe.returncode == 0 and f"cua-driver {cls.REQUIRED_VERSION}" in version_text

    def _environment(self) -> dict[str, str]:
        environment = dict(os.environ)
        environment["HOME"] = str(self.private_home)
        environment["CUA_DRIVER_RS_MCP_FORCE_PROXY"] = "1"
        return environment

    def _pid_command(self, pid: int) -> str:
        try:
            probe = subprocess.run(
                ["/bin/ps", "-p", str(int(pid)), "-o", "command="],
                capture_output=True, text=True, timeout=3,
            )
        except Exception:
            return ""
        return str(probe.stdout or "").strip() if probe.returncode == 0 else ""

    def _owns_pid(self, pid: int | None = None) -> bool:
        candidate = int(pid if pid is not None else (self.pid or 0))
        if candidate <= 0:
            return False
        command = self._pid_command(candidate)
        valid = bool(
            command
            and str(self.APP_BINARY) in command
            and re.search(r"(?:^|\s)serve(?:\s|$)", command)
            and str(self.socket_path) in command
        )
        if valid and self.pid_command and command != self.pid_command:
            return False
        return valid

    @staticmethod
    def _alive(pid: int | None) -> bool:
        if not pid or int(pid) <= 0:
            return False
        try:
            os.kill(int(pid), 0)
            return True
        except ProcessLookupError:
            return False
        except PermissionError:
            return True

    def start(self) -> None:
        if self.started:
            return
        if not self.supported(self.driver_command):
            raise _DesktopIsolationUnavailable(
                "CU_DESKTOP_SCOPE_NOT_ISOLATED: the installed driver is not the signed cua-driver 0.8.3 app."
            )
        argv = [
            "/usr/bin/open", "-n", "-g", "-b", self.BUNDLE_ID,
            "--env", f"HOME={self.private_home}",
            "--stdout", str(self.stdout_path), "--stderr", str(self.stderr_path),
            "--args", "serve", "--socket", str(self.socket_path),
        ]
        try:
            launched = subprocess.run(argv, capture_output=True, text=True, timeout=8)
            if launched.returncode != 0:
                detail = (launched.stderr or launched.stdout or "LaunchServices rejected the daemon").strip()
                raise RuntimeError(detail)
            deadline = time.monotonic() + self.startup_timeout
            while time.monotonic() < deadline:
                if self.socket_path.exists() and self.pid_file.is_file():
                    try:
                        candidate = int(self.pid_file.read_text(encoding="utf-8").strip())
                    except (OSError, TypeError, ValueError):
                        candidate = 0
                    if candidate > 0 and self._owns_pid(candidate):
                        self.pid = candidate
                        self.pid_command = self._pid_command(candidate)
                        self.started = True
                        return
                time.sleep(0.1)
            raise RuntimeError("the private socket/PID/argv attestation did not close")
        except BaseException as exc:
            cleanup_error = self.close()
            suffix = f"; cleanup: {cleanup_error}" if cleanup_error else ""
            raise _DesktopIsolationUnavailable(
                f"CU_DESKTOP_SCOPE_NOT_ISOLATED: isolated CuaDriver launch failed: {exc}{suffix}"
            ) from exc

    def stdio_parameters(self) -> StdioServerParameters:
        if not self.started or not self._owns_pid():
            raise _FatalTaskError(
                "CU_DESKTOP_SCOPE_NOT_ISOLATED: the task-private daemon identity is no longer valid."
            )
        return StdioServerParameters(
            command=self.driver_command,
            # FORCE_PROXY makes an unavailable socket fail closed instead of
            # auto-launching with the real HOME.  Do not pass
            # --no-daemon-relaunch here: in 0.8.3 that selects the in-process
            # caller TCC identity rather than the signed daemon.
            args=["mcp", "--socket", str(self.socket_path)],
            env=self._environment(),
        )

    def real_config_unchanged(self) -> bool:
        return self._file_state(self.real_config) == self.real_config_before

    def close(self) -> str:
        if self.closed:
            return self.cleanup_error
        self.closed = True
        errors: list[str] = []
        identity_unverified = self.socket_path.exists() and self.pid is None
        if self.pid is None and self.pid_file.is_file():
            try:
                candidate = int(self.pid_file.read_text(encoding="utf-8").strip())
            except (OSError, TypeError, ValueError):
                candidate = 0
            if candidate > 0 and self._owns_pid(candidate):
                self.pid = candidate
                self.pid_command = self._pid_command(candidate)
                identity_unverified = False
            elif candidate > 0 and self._alive(candidate):
                identity_unverified = True
        try:
            subprocess.run(
                [self.driver_command, "stop", "--socket", str(self.socket_path)],
                env=self._environment(), capture_output=True, text=True, timeout=1,
            )
        except Exception as exc:
            errors.append(f"stop request failed: {exc}")
        deadline = time.monotonic() + 1.2
        while self._alive(self.pid) and time.monotonic() < deadline:
            time.sleep(0.1)
        if self._alive(self.pid):
            if self._owns_pid():
                try:
                    os.kill(int(self.pid), signal.SIGTERM)
                except ProcessLookupError:
                    pass
                except Exception as exc:
                    errors.append(f"SIGTERM failed: {exc}")
                deadline = time.monotonic() + 1.0
                while self._alive(self.pid) and time.monotonic() < deadline:
                    time.sleep(0.1)
            else:
                errors.append("daemon PID ownership could not be re-attested")
        if self._alive(self.pid):
            if self._owns_pid():
                try:
                    os.kill(int(self.pid), signal.SIGKILL)
                except ProcessLookupError:
                    pass
                except Exception as exc:
                    errors.append(f"SIGKILL failed: {exc}")
                deadline = time.monotonic() + 0.3
                while self._alive(self.pid) and time.monotonic() < deadline:
                    time.sleep(0.05)
            else:
                errors.append("live daemon was not killed because PID ownership was not proven")
        if self._alive(self.pid):
            errors.append("CU_DESKTOP_DAEMON_CLEANUP_UNVERIFIED")
        unresolved_artifacts = identity_unverified and (
            self.socket_path.exists() or self.pid_file.exists()
        )
        if unresolved_artifacts:
            errors.append("CU_DESKTOP_DAEMON_CLEANUP_UNVERIFIED")
        if not self._alive(self.pid) and not unresolved_artifacts:
            try:
                # The exact task-private root was created by mkdtemp above; no
                # shell wildcard or unresolved environment variable is used.
                if self.root.parent == Path("/private/tmp") \
                        and self.root.name.startswith(self.ROOT_PREFIX):
                    shutil.rmtree(self.root, ignore_errors=False)
                else:
                    errors.append("temporary-root identity check failed")
            except FileNotFoundError:
                pass
            except Exception as exc:
                errors.append(f"temporary cleanup failed: {exc}")
        if not self.real_config_unchanged():
            errors.append("real ~/.cua-driver/config.json changed during isolated task")
        self.cleanup_error = "; ".join(dict.fromkeys(errors))
        return self.cleanup_error


def _cancelled_result(config: dict, evidence: dict, note: str = "Computer Use task was stopped.") -> dict:
    return {
        "cancelled": True,
        "answer": note,
        "metadata": _salvage_metadata(config, evidence, partial=True),
    }


def _stage_manager_enabled() -> bool | None:
    """Read the Stage Manager toggle; None when the state cannot be read."""
    try:
        probe = subprocess.run(
            ["/usr/bin/defaults", "read", "com.apple.WindowManager", "GloballyEnabled"],
            capture_output=True, text=True, timeout=4,
        )
    except Exception:
        return None
    if probe.returncode != 0:
        return None
    return probe.stdout.strip() == "1"


def _set_stage_manager(enabled: bool) -> bool:
    """Flip Stage Manager (defaults + Dock restart, the standard recipe).

    Stage-parked windows do not render, so their AX trees are empty shells and
    background input dies (proven repeatedly on this machine). The user asked
    (2026-07-21) for Computer Use to switch Stage Manager off for the duration
    of a task and restore it afterwards.
    """
    try:
        wrote = subprocess.run(
            ["/usr/bin/defaults", "write", "com.apple.WindowManager",
             "GloballyEnabled", "-bool", "true" if enabled else "false"],
            capture_output=True, text=True, timeout=4,
        )
        if wrote.returncode != 0:
            return False
        subprocess.run(
            ["/usr/bin/killall", "Dock"],
            capture_output=True, text=True, timeout=4,
        )
        return True
    except Exception:
        return False


async def _cli_driver_call(tool: str, arguments: dict, timeout: float = 8.0) -> str:
    """Invoke the signed driver binary once in a fresh CLI process.

    The task-private daemon's activation/foreground requests can be silently
    ignored by Stage Manager (upstream cua-driver #2206 family) while the exact
    same call from a fresh CLI context is honored - verified on this machine
    2026-07-21 (bring_to_front {pid, window_id}: daemon left the window parked,
    CLI expanded it). Used only for worker-owned routing transitions; never for
    capture or model-directed input.
    """
    argv = [
        str(_IsolatedCuaDaemon.APP_BINARY), "call", str(tool),
        json.dumps(arguments or {}, ensure_ascii=False),
    ]
    try:
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            out, err = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        except asyncio.TimeoutError:
            proc.kill()
            return f"cli {tool} timed out"
        return (out or err or b"").decode("utf-8", "replace").strip()[:400]
    except Exception as exc:
        return f"cli {tool} failed: {_flatten_error(exc)}"


class _Binding:
    """Current app grounding inside one already-approved multi-app task."""

    def __init__(self):
        self.identities: set[str] = set()
        self.label = ""
        self.pid: int | None = None
        self.window_id: int | None = None

    def clear(self):
        self.identities.clear()
        self.label = ""
        self.pid = None
        self.window_id = None

    def rebind(self, identity: str, entry: dict | None = None):
        self.clear()
        self.add(identity, entry)

    def add(self, identity: str, entry: dict | None = None):
        if identity:
            self.identities.add(identity)
            key, _, value = identity.partition(":")
            if key == "pid":
                try:
                    self.pid = int(value)
                except (TypeError, ValueError):
                    pass
        if entry:
            if entry.get("pid") is not None:
                try:
                    parsed_pid = int(entry["pid"])
                    # list_apps includes installed-but-not-running apps as
                    # pid=0. That is discovery metadata, never a targetable
                    # process identity. Keep pid unset so a successful launch
                    # forces a fresh app-map resolution before observation.
                    if parsed_pid > 0:
                        self.pid = parsed_pid
                        self.identities.add(f"pid:{self.pid}")
                except (TypeError, ValueError):
                    pass
            bundle_id = _usable_identity_text(entry.get("bundle_id"))
            if bundle_id:
                self.identities.add(f"bundle_id:{bundle_id}")
        human_label = (
            _usable_identity_text((entry or {}).get("name"))
            or _usable_identity_text((entry or {}).get("bundle_id"))
        )
        raw_label = any(self.label.startswith(key + ":") for key in TARGET_KEYS)
        identity_fallback_label = any(
            self.label == _usable_identity_text(str(bound).partition(":")[2])
            for bound in self.identities
        )
        replaceable_label = not _usable_identity_text(self.label) or raw_label \
            or str(self.label).startswith("PID ") or identity_fallback_label
        if human_label and replaceable_label:
            self.label = human_label
        elif not self.label:
            key, _, value = str(identity or "").partition(":")
            usable_value = _usable_identity_text(value)
            if usable_value and key != "pid":
                self.label = usable_value
            elif key == "pid" and usable_value:
                self.label = f"PID {usable_value}"


_PLACEHOLDER_IDENTITY_TEXT = {"?", "unknown", "<unknown>", "n/a", "none", "null"}


def _usable_identity_text(value: Any) -> str:
    """Return a human/app identity only when it is not a driver placeholder."""
    text = str(value or "").strip()
    return "" if text.lower() in _PLACEHOLDER_IDENTITY_TEXT else text


def _app_entry_for(identity: str, apps: list[dict]) -> dict | None:
    key, _, value = str(identity or "").partition(":")
    value = value.strip()
    if not value:
        return None
    if key == "pid":
        try:
            if int(value) <= 0:
                return None
        except (TypeError, ValueError):
            return None
    # list_apps may put an installed catalogue record (pid=0) before the
    # running record for the exact same bundle/name.  Exact PID lookup remains
    # exact; human/bundle lookup prefers a real process so a successful launch
    # can bind instead of getting stuck on the catalogue row forever.
    matches: list[dict] = []
    for entry in apps or []:
        if not isinstance(entry, dict):
            continue
        if key == "pid":
            try:
                entry_pid = int(entry.get("pid"))
                if entry_pid > 0 and entry_pid == int(value):
                    return entry
            except (TypeError, ValueError):
                continue
        elif key == "bundle_id":
            if str(entry.get("bundle_id", "")).lower() == value.lower():
                matches.append(entry)
        elif key in ("application", "application_name", "app", "app_name", "process_name", "target_app"):
            if str(entry.get("name", "")).lower() == value.lower():
                matches.append(entry)
    if not matches:
        return None

    def running_rank(entry: dict) -> tuple[int, int]:
        try:
            pid = int(entry.get("pid") or 0)
        except (TypeError, ValueError):
            pid = 0
        return (pid > 0, pid)

    return max(matches, key=running_rank)


def _same_app(identity: str, bound_identities: set[str], apps: list[dict]) -> dict | None:
    """Return the app entry when `identity` and at least one bound identity
    resolve to the SAME application (equal pid, or equal non-empty bundle_id);
    None otherwise."""
    entry = _app_entry_for(identity, apps)
    if entry is None:
        return None
    for bound in bound_identities:
        bound_entry = _app_entry_for(bound, apps)
        if bound_entry is None:
            continue
        try:
            if bound_entry.get("pid") is not None and entry.get("pid") is not None \
                    and int(bound_entry["pid"]) == int(entry["pid"]):
                return entry
        except (TypeError, ValueError):
            pass
        bundle_a = str(entry.get("bundle_id", "") or "").lower()
        bundle_b = str(bound_entry.get("bundle_id", "") or "").lower()
        if bundle_a and bundle_a == bundle_b:
            return entry
    return None


def _unwrap_structured(payload: Any) -> Any:
    """Undo transport wrapping: JSON strings become objects, and FastMCP-style
    structured output ({'result': ...} around scalar returns) is unwrapped."""
    if isinstance(payload, str):
        try:
            payload = json.loads(payload)
        except Exception:
            return None
    if isinstance(payload, dict) and "result" in payload and not ({"apps", "windows"} & set(payload.keys())):
        return _unwrap_structured(payload["result"])
    return payload


def _missing_permissions(payload: Any) -> list[str]:
    # cua-driver 0.8.3 check_permissions shape: {"accessibility": bool,
    # "screen_recording": bool, ...}. Only an explicit false counts as missing.
    payload = _unwrap_structured(payload)
    if not isinstance(payload, dict):
        return []
    missing = []
    for key, label in (("accessibility", "Accessibility"), ("screen_recording", "Screen Recording")):
        if payload.get(key) is False:
            missing.append(label)
    return missing


def _parse_app_map(payload: Any) -> list[dict]:
    payload = _unwrap_structured(payload)
    apps = payload.get("apps") if isinstance(payload, dict) else None
    if apps is None and isinstance(payload, list):
        apps = payload
    out = []
    for item in apps or []:
        if isinstance(item, dict):
            out.append({
                "pid": item.get("pid"),
                "bundle_id": str(item.get("bundle_id", "") or ""),
                "name": str(item.get("name", "") or ""),
            })
    return out


def _app_entry_from_action_result(payload: Any, request: dict | None = None) -> dict | None:
    """Extract a running app identity returned by launch/activate tools."""
    payload = _unwrap_structured(payload)
    candidates: list[Any] = [payload]
    if isinstance(payload, dict):
        candidates.extend(payload.get(key) for key in ("app", "application", "target"))
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        try:
            pid = int(candidate.get("pid") or 0)
        except (TypeError, ValueError):
            pid = 0
        if pid <= 0:
            continue
        window_name = ""
        windows = candidate.get("windows")
        if not isinstance(windows, list) and isinstance(payload, dict):
            windows = payload.get("windows")
        for window in windows if isinstance(windows, list) else []:
            if not isinstance(window, dict):
                continue
            window_name = (
                _usable_identity_text(window.get("app_name"))
                or _usable_identity_text(window.get("application_name"))
                or _usable_identity_text(window.get("owner_name"))
            )
            if window_name:
                break
        requested = request if isinstance(request, dict) else {}
        return {
            "pid": pid,
            "bundle_id": (
                _usable_identity_text(candidate.get("bundle_id"))
                or _usable_identity_text(requested.get("bundle_id"))
            ),
            "name": (
                _usable_identity_text(candidate.get("name"))
                or _usable_identity_text(candidate.get("application_name"))
                or window_name
                or _usable_identity_text(requested.get("name"))
                or _usable_identity_text(requested.get("application_name"))
            ),
        }
    return None


def _desktop_target_is_main(policy: dict, window_context: dict) -> bool | None:
    """Resolve the desktop fallback boundary without guessing a display.

    Explicit display mode uses the freshly resolved display record.  Automatic
    mode uses the fresh window-to-display assignment from the current snapshot.
    ``None`` means ambiguous/off-screen/unknown and is deliberately unsupported
    by cua-driver 0.8.3's main-display-only desktop tools.
    """
    if str((policy or {}).get("mode", "auto")) == "display":
        display = policy.get("display") if isinstance(policy.get("display"), dict) else {}
        value = display.get("is_main", display.get("main", display.get("primary")))
        return value if isinstance(value, bool) else None
    assignment = (
        window_context.get("display_assignment")
        if isinstance(window_context, dict) else None
    )
    if not isinstance(assignment, dict) or assignment.get("status") != "ASSIGNED":
        return None
    value = assignment.get("is_main")
    if isinstance(value, bool):
        return value
    display = assignment.get("display") if isinstance(assignment.get("display"), dict) else {}
    value = display.get("is_main", display.get("main", display.get("primary")))
    return value if isinstance(value, bool) else None


def _attest_private_desktop_daemon(
        permissions_payload: Any, config_payload: Any,
        daemon: _IsolatedCuaDaemon) -> tuple[bool, dict]:
    permissions = _unwrap_structured(permissions_payload)
    driver_config = _unwrap_structured(config_payload)
    source = permissions.get("source") if isinstance(permissions, dict) else None
    source = source if isinstance(source, dict) else {}
    try:
        source_pid = int(source.get("pid") or 0)
    except (TypeError, ValueError):
        source_pid = 0
    try:
        source_executable = str(Path(str(source.get("executable", "") or "")).resolve())
    except Exception:
        source_executable = ""
    attribution = str(source.get("attribution", "") or "").strip().lower()
    private_config_scope = ""
    try:
        private_payload = json.loads(daemon.private_config.read_text(encoding="utf-8"))
        if isinstance(private_payload, dict):
            private_config_scope = str(private_payload.get("capture_scope", "") or "")
    except Exception:
        private_config_scope = ""
    checks = {
        "accessibility": isinstance(permissions, dict) and permissions.get("accessibility") is True,
        "screen_recording": isinstance(permissions, dict) and permissions.get("screen_recording") is True,
        "screen_recording_capturable": (
            isinstance(permissions, dict) and permissions.get("screen_recording_capturable") is True
        ),
        "source_attribution": attribution == "driver-daemon",
        "source_executable": source_executable == str(daemon.APP_BINARY.resolve()),
        "source_pid": bool(daemon.pid and source_pid == int(daemon.pid)),
        "pid_argv": daemon._owns_pid(),
        "config_readback": (
            isinstance(driver_config, dict) and driver_config.get("capture_scope") == "desktop"
        ),
        "private_config": private_config_scope == "desktop",
        "real_config_unchanged": daemon.real_config_unchanged(),
    }
    return all(checks.values()), {
        "checks": checks,
        "source": _json_safe(source),
        "private_config_scope": private_config_scope,
    }


async def _run(config: dict, evidence: dict) -> dict:
    display_inventory = _runtime_display_inventory(config)
    target_display_policy = _target_display_policy(config, display_inventory)
    evidence["display_policy"] = _json_safe(target_display_policy)
    if target_display_policy.get("valid") is False:
        policy_failure = target_display_policy.get("error") or {}
        evidence["failure_source"] = "display"
        raise _FatalTaskError(
            f"{policy_failure.get('code', 'CU_TARGET_DISPLAY_UNRESOLVED')}: "
            f"{policy_failure.get('message', 'Target display could not be resolved.')}"
        )
    driver_command = os.path.expanduser(str(config.get("driver_command", "") or "~/.local/bin/cua-driver"))
    if not (os.path.isfile(driver_command) and os.access(driver_command, os.X_OK)):
        evidence["failure_source"] = "driver"
        raise RuntimeError(_driver_error())
    explicit_main = _desktop_target_is_main(target_display_policy, {})
    isolated_daemon: _IsolatedCuaDaemon | None = None
    isolation_unavailable = ""
    if explicit_main is not False and _IsolatedCuaDaemon.supported(driver_command):
        isolated_daemon = _IsolatedCuaDaemon(driver_command)
        evidence["failure_source"] = "driver"
        try:
            await _call_in_daemon_thread(isolated_daemon.start)
        except _DesktopIsolationUnavailable as exc:
            isolation_unavailable = str(exc)
            if isolated_daemon.cleanup_error:
                raise _FatalTaskError(
                    "CU_DESKTOP_DAEMON_CLEANUP_UNVERIFIED: " + isolated_daemon.cleanup_error
                ) from exc
            isolated_daemon = None
        else:
            params = isolated_daemon.stdio_parameters()
            evidence["desktop_isolation"] = {
                "started": True,
                "daemon_pid": isolated_daemon.pid,
                "socket": str(isolated_daemon.socket_path),
                "real_config_before": _json_safe(isolated_daemon.real_config_before),
            }
    if isolated_daemon is None:
        await _call_in_daemon_thread(_ensure_driver_daemon, driver_command)
        params = StdioServerParameters(command=driver_command, args=["mcp"])
        evidence["desktop_isolation"] = {
            "started": False,
            "reason": (
                "selected display is not main" if explicit_main is False
                else isolation_unavailable or "signed cua-driver 0.8.3 isolation path unavailable"
            ),
        }
    result: dict | None = None
    downgrade_after_attestation = ""
    active_daemon = isolated_daemon
    try:
        try:
            result = await _run_with_driver(
                config, evidence,
                display_inventory=display_inventory,
                target_display_policy=target_display_policy,
                driver_command=driver_command,
                params=params,
                isolated_daemon=active_daemon,
            )
        except _DesktopIsolationUnavailable as exc:
            if active_daemon is None or evidence.get("actions"):
                raise
            downgrade_after_attestation = str(exc)
    finally:
        if active_daemon is not None:
            cleanup_error = await _call_in_daemon_thread(active_daemon.close)
            isolation_log = evidence.setdefault("desktop_isolation", {})
            isolation_log["cleaned"] = not bool(cleanup_error)
            isolation_log["cleanup_error"] = cleanup_error
            isolation_log["real_config_after"] = _json_safe(
                active_daemon._file_state(active_daemon.real_config)
            )
            if cleanup_error:
                evidence["failure_source"] = "driver"
                raise _FatalTaskError(
                    "CU_DESKTOP_DAEMON_CLEANUP_UNVERIFIED: " + cleanup_error
                )

    if downgrade_after_attestation:
        # No snapshot was ever shown to the model and no action was attempted,
        # so an AX/window-only retry on the normal daemon cannot replay input.
        evidence["desktop_isolation"] = {
            **dict(evidence.get("desktop_isolation") or {}),
            "started": False,
            "available": False,
            "reason": downgrade_after_attestation,
        }
        evidence["driver_session"] = ""
        await _call_in_daemon_thread(_ensure_driver_daemon, driver_command)
        result = await _run_with_driver(
            config, evidence,
            display_inventory=display_inventory,
            target_display_policy=target_display_policy,
            driver_command=driver_command,
            params=StdioServerParameters(command=driver_command, args=["mcp"]),
            isolated_daemon=None,
        )

    if result is None:
        raise RuntimeError("Computer Use ended without a result.")
    metadata = result.get("metadata") if isinstance(result, dict) else None
    if isinstance(metadata, dict):
        metadata["desktop_isolation"] = _json_safe(evidence.get("desktop_isolation") or {})
        metadata["actions_log"] = _save_actions_log(config, evidence)
    return result


async def _run_with_driver(
        config: dict, evidence: dict, *, display_inventory: list[dict],
        target_display_policy: dict, driver_command: str,
        params: StdioServerParameters,
        isolated_daemon: _IsolatedCuaDaemon | None) -> dict:
    actions = evidence["actions"]
    visited_targets = evidence["visited_targets"]
    narratives = evidence["narratives"]
    binding = _Binding()
    app_map: list[dict] = []
    driver_session = "broccoli-" + uuid.uuid4().hex
    evidence["driver_session"] = driver_session
    max_steps = _positive_int(config.get("max_steps"), 25)
    step_timeout = _positive_int(config.get("step_timeout"), 180)
    max_failures = _positive_int(config.get("max_failures"), 3)
    failures = 0
    recent: list[list[dict]] = []
    pending_action_index: int | None = None
    no_effect_streak = 0
    no_effect_counts: dict[str, int] = {}
    NO_EFFECT_LIMIT = 3
    EFFECT_CALL_LIMIT = 6
    effect_calls_since_confirmation = 0
    attempted_rungs: set[tuple] = set()
    # One retry credit per logical operation whose settlement was INDETERMINATE:
    # an unverifiable result must not ban the operation until the state epoch
    # turns (which itself requires a confirmed effect somewhere).
    indeterminate_unburns: dict[str, int] = {}
    # Elements that returned a kAXError for an AX action (e.g. AXPress -25206 on
    # SwiftUI rows/cells). Repeats fail identically and burn the driver-failure
    # breaker, so identical retries are refused with routing guidance instead.
    ax_action_unsupported: set[tuple] = set()
    # User-approved (2026-07-21) controlled expand: a Stage-parked SwiftUI
    # window materializes its full AX tree only while actually rendered, so a
    # pending text write that is stuck on such a window may bring the
    # destination forward ONCE; the prior frontmost app is restored after the
    # write verifies (or at finish).
    expand_transition_pids: set[int] = set()
    expand_restore: dict = {}
    # One worker-owned cross-display relocation per app: the driver's own
    # title-bar drag (delivery_mode "foreground", verified 2026-07-21 to move
    # real windows and restore the prior frontmost) pulls the task window onto
    # the user-selected target display; background drags are unavailable.
    relocate_transition_pids: set[int] = set()
    # Stage Manager is switched off for the task's duration when found on
    # (user-requested 2026-07-21); restored in the session finally.
    stage_manager_was_on = False
    # One rescue before the no-effect breakers fire while a private text write
    # is pending: repeated focus clicks on an empty note body are oracle-silent
    # and must redirect the model to insert_captured_text instead of dying.
    insert_rescue_used = False
    insert_rescue_directive = ""
    # General second-opinion net (user directive 2026-07-22): before any
    # progress-class abort, let the model LOOK at the current screenshot and
    # veto the abort when the screen visibly contradicts the hash oracle.
    visual_arbiter_used = False
    # Experience rules (builtin + auto-learned + user-taught), compiled to
    # data-only forms by the main app; see computer_use_experience.py.
    experience_rules = [
        rule for rule in (config.get("experience_rules") or [])
        if isinstance(rule, dict)
    ] if _experience is not None else []
    experience_role_bans = (
        _experience.role_action_bans(experience_rules) if _experience is not None else set()
    )
    # A transport exception after an app-input call is ambiguous: the app may
    # have mutated even though no result came back. Keep an exact operation-level
    # barrier independent of state/geometry epochs so unrelated confirmations
    # can never make that input replayable.
    unknown_replay_barriers: dict[str, dict] = {}
    verified_state_epoch = 0
    observation_sequence = 0
    geometry_epoch = 0
    geometry_stability = 0
    last_geometry_signature: tuple = ()
    force_geometry_epoch = False
    unresolved_action_failure = False
    effect_chain_sequence = 0
    active_effect_chain: dict = {}
    foreground_grant: dict = {}
    foreground_grant_source_index: int | None = None
    # A foreground retry whose source no-effect verdict came only from the coarse
    # fingerprint. It runs only after the model, having seen the screenshot,
    # re-sends the identical operation: {"source_index", "rung", "label"}.
    weak_absence_retry: dict = {}
    insert_fallback_source_index: int | None = None
    private_insert_grant: dict = {}
    unknown_launch_binding: dict = {}
    copy_selection_grant: dict = {}
    transfer_generation = 0
    transfer_buffer: dict = {
        "text": "", "metadata": {}, "source": {},
        "generation": 0, "insert_verified": False, "destination": {},
    }

    def settle_clipboard_transfer(
            original_text: str, before: dict, probe: dict,
            oracle: dict, window_context: dict, source_kind: str) -> tuple[bool, bool, dict]:
        """Settle a copy attempt and update only the private transfer buffer."""
        nonlocal transfer_generation
        copied_text, clipboard_evidence = _clipboard_probe_result(
            original_text, before, probe,
        )
        changed = clipboard_evidence.get("changed") is True
        absence_proven = clipboard_evidence.get("absence_proven") is True
        transfer_updated = False
        if changed and copied_text:
            copied_bytes = copied_text.encode("utf-8")
            copied_meta = {
                "source_element_count": 0,
                "char_count": len(copied_text),
                "utf8_bytes": len(copied_bytes),
                "sha256": hashlib.sha256(copied_bytes).hexdigest(),
            }
            transfer_generation += 1
            transfer_buffer.clear()
            transfer_buffer.update({
                "text": copied_text,
                "metadata": copied_meta,
                "generation": transfer_generation,
                "source": {
                    "kind": source_kind,
                    "pid": window_context.get("pid"),
                    "window_id": window_context.get("window_id"),
                    "snapshot_id": window_context.get("snapshot_id", ""),
                },
                "insert_verified": False,
                "destination": {},
            })
            oracle["transfer_generation"] = transfer_generation
            oracle["transfer_sha256"] = copied_meta["sha256"]
            transfer_updated = True
        clipboard_evidence.update({
            "transfer_buffer_updated": transfer_updated,
            "transfer_char_count": len(copied_text) if transfer_updated else 0,
            "raw_text_logged": False,
        })
        return changed, absence_proven, clipboard_evidence
    desktop_fallback: dict = {
        "isolated_daemon": isolated_daemon is not None,
        "private_home_verified": False,
        "force_proxy": isolated_daemon is not None,
        "tcc_identity_verified": False,
        "capture_scope_desktop": False,
        "capture_verified": False,
        "authorized": False,
        "active": False,
        "fresh_snapshot_id": "",
        "target_is_main": (
            _desktop_target_is_main(target_display_policy, {})
            if str(target_display_policy.get("mode", "auto")) == "display"
            else None
        ),
        "last_window": {},
        "desktop_attempted": False,
        "pre_desktop_fingerprint_components": {},
        "grant_chain_id": "",
        "grant_tool": "",
        "grant_oracle": "",
        "grant_operation_signature": (),
        "grant_operation_semantics": (),
    }

    def allocate_effect_chain_id(
            name: str, arguments: dict, address_mode: str,
            oracle: dict, window_context: dict,
            original_arguments: dict | None = None) -> str:
        """Group only an unresolved delivery ladder for the same logical action.

        Routing/clipboard preparation never replaces the active visible-effect
        chain, while persistent foreground activation is outside this ladder.
        A different target within the same modality starts a new chain.
        """
        nonlocal effect_chain_sequence

        def fresh_id() -> str:
            nonlocal effect_chain_sequence
            effect_chain_sequence += 1
            return f"{driver_session}:e{effect_chain_sequence:04d}"

        kind = str((oracle or {}).get("kind", "driver_only") or "driver_only")
        if kind in {"topology", "driver_only", "clipboard_copy", "selection"}:
            return fresh_id()
        base = _effect_chain_base_signature(
            name, arguments, oracle, window_context,
            original_arguments=original_arguments,
        )
        address = _effect_chain_address_signature(arguments, address_mode, oracle)
        if active_effect_chain.get("base") == base:
            previous_mode = str(active_effect_chain.get("address_mode", "") or "")
            previous_address = tuple(active_effect_chain.get("address") or ())
            previous_epoch = active_effect_chain.get("geometry_epoch")
            current_mode = str(address_mode or "")
            same_target = bool(address is not None and previous_address) and \
                _effect_chain_target_matches(
                    previous_mode, previous_address, previous_epoch,
                    current_mode, address, window_context.get("geometry_epoch"),
                )
            if same_target:
                active_effect_chain.update({
                    "address_mode": str(address_mode or ""),
                    "address": address,
                    "geometry_epoch": window_context.get("geometry_epoch"),
                })
                return str(active_effect_chain.get("id", "") or fresh_id())
        chain_id = fresh_id()
        active_effect_chain.clear()
        active_effect_chain.update({
            "id": chain_id, "base": base,
            "address_mode": str(address_mode or ""), "address": address or (),
            "geometry_epoch": window_context.get("geometry_epoch"),
        })
        return chain_id

    def retire_effect_chain(action: dict) -> None:
        if str(active_effect_chain.get("id", "") or "") == str(
                action.get("effect_chain_id", "") or ""):
            active_effect_chain.clear()
    runtime_topologies = {
        str(item.get("topology_signature", "") or "").strip()
        for item in display_inventory
        if isinstance(item, dict) and str(item.get("topology_signature", "") or "").strip()
    }

    def refresh_display_topology() -> None:
        """Keep task grounding tied to the worker-start physical layout."""
        if not runtime_topologies:
            return
        current = _runtime_display_inventory(config)
        current_topologies = {
            str(item.get("topology_signature", "") or "").strip()
            for item in current
            if isinstance(item, dict) and str(item.get("topology_signature", "") or "").strip()
        }
        if current_topologies != runtime_topologies:
            raise _FatalTaskError(
                "CU_DISPLAY_TOPOLOGY_CHANGED: the physical display layout changed during the task; "
                "re-approve Computer Use against the current layout."
            )
        display_inventory[:] = current

    evidence["failure_source"] = "driver"
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
            evidence["failure_source"] = ""
            tools = [_tool_dict(item) for item in listed.tools]
            tools = [item for item in tools if item["name"]]
            by_name = {item["name"]: item for item in tools}
            synthetic_tools = _synthetic_transfer_descriptors()
            synthetic_by_name = {item["name"]: item for item in synthetic_tools}
            model_tools = [
                item for item in tools
                if not _worker_owned_tool(item["name"])
                and str(item["name"]).lower() not in PERSISTENT_FOREGROUND_TOOLS
            ] + synthetic_tools
            window_tool = by_name.get(WINDOW_OBSERVE_TOOL)
            apps_tool_name = next((name for name in APPS_OBSERVE_TOOLS if name in by_name), "")
            legacy_screenshot = next(
                (item for item in tools
                 if item["name"] != WINDOW_OBSERVE_TOOL
                 and ("screenshot" in item["name"].lower() or "capture" in item["name"].lower())),
                None,
            )
            if window_tool is None and legacy_screenshot is None:
                evidence["failure_source"] = "driver"
                raise RuntimeError(
                    "Driver tool surface has no observation tool "
                    f"(neither {WINDOW_OBSERVE_TOOL} nor a screenshot/capture tool); Computer Use cannot run."
                )
            async def call_checked(name: str, arguments: dict) -> tuple[Any, dict]:
                descriptor = by_name.get(name)
                if descriptor is None:
                    raise RuntimeError(f"Driver tool {name!r} is unavailable.")
                driver_arguments = _with_driver_session(
                    arguments, descriptor["inputSchema"], driver_session,
                )
                try:
                    result = await _call_tool(session, name, driver_arguments, step_timeout)
                except Exception:
                    evidence["failure_source"] = "driver"
                    raise
                if _result_is_error(result):
                    evidence["failure_source"] = "driver"
                    raise RuntimeError(f"{name} failed: {_result_summary(result)}")
                return result, driver_arguments

            async def position_agent_cursor(
                    action_arguments: dict, current_elements: list[dict],
                    window_context: dict, target_label: str) -> dict:
                """Best-effort overlay plumbing; never gate the real AX input."""
                if "move_cursor" not in by_name:
                    return {
                        "available": False, "mode": "worker_owned_overlay",
                        "reason": "driver_has_no_move_cursor", "real_pointer_moved": False,
                        "action_continued": True,
                    }
                evidence_record = _agent_cursor_target(
                    action_arguments, current_elements, display_inventory, target_display_policy,
                )
                if not evidence_record.get("available"):
                    return evidence_record
                point = dict(evidence_record.get("requested_position") or {})
                previous_failure_source = evidence.get("failure_source", "")
                try:
                    if "set_agent_cursor_motion" in by_name:
                        await call_checked("set_agent_cursor_motion", {
                            "cursor_id": driver_session,
                            "cursor_label": f"Broccoli · {target_label or 'target'} · background AX",
                            "dwell_after_click_ms": 220,
                            "idle_hide_ms": 0,
                        })
                    move_result, move_arguments = await call_checked("move_cursor", point)
                except asyncio.CancelledError:
                    raise
                except Exception as exc:
                    evidence["failure_source"] = previous_failure_source
                    return {
                        **evidence_record,
                        "available": False,
                        "reason": "overlay_error",
                        "error": _clip(_flatten_error(exc), 500),
                        "action_continued": True,
                    }
                evidence["failure_source"] = previous_failure_source
                evidence_record.update({
                    "driver_arguments": _json_safe(move_arguments),
                    "result": _clip(_result_summary(move_result), 500),
                    "action_continued": True,
                })
                if "get_agent_cursor_state" in by_name:
                    try:
                        state, _state_args = await call_checked("get_agent_cursor_state", {
                            "cursor_id": driver_session,
                        })
                        evidence_record["readback"] = _json_safe(_structured_payload(state))
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        evidence_record["readback_error"] = _clip(_flatten_error(exc), 500)
                        evidence["failure_source"] = previous_failure_source
                return evidence_record

            async def dispatch_private_type_text(
                    grant: dict, *, step: int, current_window: dict,
                    current_elements: list[dict], current_fingerprint: str,
                    fingerprint_components: dict) -> tuple[dict, tuple]:
                """Consume one private type_text grant and return a redacted action record."""
                delivery_mode = str(
                    (grant.get("arguments") or {}).get("delivery_mode", "background")
                ).lower()
                safe_arguments = copy.deepcopy(grant.get("arguments") or {})
                safe_original = copy.deepcopy(grant.get("original_arguments") or safe_arguments)
                oracle = copy.deepcopy(grant.get("oracle") or {})
                transfer_identity = copy.deepcopy(grant.get("private_transfer") or {})
                descriptor = by_name.get("type_text")
                current_transfer = _private_transfer_log_metadata(transfer_buffer)
                identity_matches = bool(
                    transfer_identity.get("generation") == current_transfer.get("generation")
                    and str(transfer_identity.get("sha256", "") or "")
                    == str(current_transfer.get("sha256", "") or "")
                    and int(transfer_identity.get("utf8_bytes", 0) or 0)
                    == int(current_transfer.get("utf8_bytes", 0) or 0)
                    and str(transfer_buffer.get("text", "") or "")
                )
                descriptor_properties = _schema_properties(
                    descriptor.get("inputSchema") if isinstance(descriptor, dict) else {}
                )
                preflight_error = ""
                if descriptor is None:
                    preflight_error = "CU_AX_TRANSFER_TYPE_TEXT_UNAVAILABLE"
                elif not identity_matches:
                    preflight_error = "CU_AX_TRANSFER_BUFFER_CHANGED"
                elif delivery_mode == "foreground" \
                        and "delivery_mode" not in descriptor_properties:
                    preflight_error = "CU_TRANSIENT_FOREGROUND_UNSUPPORTED"
                elif grant.get("consumed") is True:
                    preflight_error = "CU_PRIVATE_INSERT_GRANT_CONSUMED"

                logical_name = "insert_captured_text"
                address_mode = "element_ax"
                rung_key = _action_rung_key(
                    logical_name, safe_arguments, address_mode, oracle,
                    current_window, str(grant.get("target_identity", "") or ""),
                    elements=current_elements, original_arguments=safe_original,
                    state_epoch=int(grant.get("state_epoch", verified_state_epoch) or 0),
                )
                replay_hash = _unknown_replay_operation_sha256(
                    logical_name, safe_arguments, address_mode, current_window,
                    str(grant.get("target_identity", "") or ""),
                    elements=current_elements, original_arguments=safe_original,
                )
                cursor = {
                    "available": False,
                    "mode": "worker_owned_overlay",
                    "reason": "private_insert_preflight_not_delivered",
                    "real_pointer_moved": False,
                    "action_continued": False,
                }
                driver_attempted = False
                delivery_outcome = DELIVERY_NOT_ATTEMPTED
                is_error = bool(preflight_error)
                error_code = preflight_error
                result: Any = None
                driver_confirmed = False
                if preflight_error:
                    raw_summary = (
                        "Private AX text transfer was not delivered because its exact worker-owned "
                        "grant or driver capability was unavailable."
                    )
                else:
                    # Consume before any cosmetic cursor work or driver call.
                    # A timeout/exception can never authorize a replay.
                    grant["consumed"] = True
                    attempted_rungs.add(rung_key)
                    prepared = {
                        key: value for key, value in safe_arguments.items()
                        if key in descriptor_properties
                    }
                    prepared["text"] = str(transfer_buffer.get("text", "") or "")
                    if "delivery_mode" in descriptor_properties:
                        prepared["delivery_mode"] = delivery_mode
                    actual_arguments = _with_driver_session(
                        prepared, descriptor["inputSchema"], driver_session,
                    )
                    cursor = await position_agent_cursor(
                        safe_arguments, current_elements, current_window,
                        str(grant.get("target_identity", "") or binding.label),
                    )
                    driver_attempted = True
                    try:
                        result = await _call_tool(
                            session, "type_text", actual_arguments, step_timeout,
                        )
                        is_error = _result_is_error(result)
                        delivery_outcome = (
                            DELIVERY_DRIVER_ERROR if is_error
                            else DELIVERY_DELIVERED_UNVERIFIED
                        )
                        error_code = "CU_DRIVER_ERROR" if is_error else ""
                        driver_confirmed = bool(
                            not is_error and _driver_confirms_effect(result)
                        )
                        raw_summary = (
                            "CuaDriver type_text returned an explicit error during private AX transfer."
                            if is_error else
                            "CuaDriver type_text returned; exact fresh AX hash readback is still required."
                        )
                    except asyncio.CancelledError:
                        raise
                    except Exception:
                        # Never persist the exception string: an MCP/driver
                        # implementation may echo the request payload in it.
                        is_error = True
                        delivery_outcome = DELIVERY_UNKNOWN_AFTER_ATTEMPT
                        error_code = "CU_DRIVER_DELIVERY_UNKNOWN"
                        raw_summary = (
                            "Private AX text transfer lost its driver reply after dispatch; "
                            "the exact operation is blocked from replay."
                        )

                effect_status = (
                    EFFECT_PENDING
                    if driver_attempted and delivery_outcome == DELIVERY_DELIVERED_UNVERIFIED
                    else EFFECT_INDETERMINATE
                    if driver_attempted and delivery_outcome == DELIVERY_UNKNOWN_AFTER_ATTEMPT
                    else EFFECT_NOT_DELIVERED
                )
                effect_chain_id = ""
                if delivery_outcome == DELIVERY_DELIVERED_UNVERIFIED:
                    effect_chain_id = str(grant.get("effect_chain_id", "") or "") \
                        or allocate_effect_chain_id(
                            logical_name, safe_arguments, address_mode, oracle,
                            current_window, original_arguments=safe_original,
                        )
                driver_log = {
                    "driver_tool": "type_text",
                    "delivery_mode": delivery_mode,
                    "pid": safe_arguments.get("pid"),
                    "window_id": safe_arguments.get("window_id"),
                    "element_token": safe_arguments.get("element_token", ""),
                    "element_index": safe_arguments.get("element_index"),
                    "driver_confirmed": driver_confirmed,
                    "transfer_buffer": transfer_identity,
                    "raw_text_logged": False,
                }
                action_record = {
                    "step": step,
                    "tool": logical_name,
                    "arguments": _json_safe(safe_arguments),
                    "sanitized_arguments": _json_safe(safe_arguments),
                    "original_arguments": _json_safe(safe_original),
                    "original_args": _json_safe(safe_original),
                    "driver_arguments": _json_safe(driver_log),
                    "driver_args": _json_safe(driver_log),
                    "address_mode": address_mode,
                    "dropped_arguments": [],
                    "allowed": not bool(preflight_error),
                    "executed": driver_attempted,
                    "driver_attempted": driver_attempted,
                    "delivery_outcome": delivery_outcome,
                    "worker_local": False,
                    "quota_deferred": False,
                    "is_error": is_error,
                    "error_code": error_code,
                    "structured_error": (
                        _policy_error(
                            error_code, raw_summary,
                            stage="delivery" if driver_attempted else "routing",
                            retriable=False,
                        ) if error_code else None
                    ),
                    "result": raw_summary,
                    "raw_summary": raw_summary,
                    "structured": driver_log,
                    "structured_content": driver_log,
                    "structuredContent": driver_log,
                    "content_blocks": [],
                    # Driver verified:true is intentionally forensic only.
                    "effect_confirmed": False,
                    "effect_status": effect_status,
                    "oracle": _json_safe(oracle),
                    "effect_chain_id": effect_chain_id,
                    "rung_key": _json_safe(list(rung_key)),
                    "operation_signature_sha256": _rung_operation_sha256(rung_key),
                    "quota_reconciliation_signature_sha256": (
                        _quota_reconciliation_operation_sha256(
                            logical_name, safe_arguments, address_mode, oracle,
                            current_window,
                            str(grant.get("target_identity", "") or ""),
                            elements=current_elements,
                            original_arguments=safe_original,
                        )
                    ),
                    "unknown_replay_signature_sha256": replay_hash,
                    "transient_foreground_authorization": {
                        "grant_kind": grant.get("grant_kind", ""),
                        "authorized_by_step": grant.get("authorized_by_step"),
                        "operation_signature_sha256": grant.get(
                            "operation_signature_sha256", ""
                        ),
                        "consumed": grant.get("consumed") is True,
                    },
                    "copy_selection_authorization": {},
                    "cursor": _json_safe(cursor),
                    "clipboard": {},
                    "session": driver_session,
                    "target_identity": str(grant.get("target_identity", "") or ""),
                    "resolved_target_pid": current_window.get("pid"),
                    "resolved_target_label": binding.label,
                    "window": _json_safe(current_window),
                    "snapshot_id": current_window.get("snapshot_id", ""),
                    "geometry_epoch": current_window.get("geometry_epoch"),
                    "verified_state_epoch": int(
                        grant.get("state_epoch", verified_state_epoch) or 0
                    ),
                    "geometry": _json_safe(current_window.get("geometry") or {}),
                    "fingerprint": current_fingerprint,
                    "fingerprint_components": _json_safe(fingerprint_components),
                    "verification_fingerprint_components": _json_safe(
                        fingerprint_components
                    ),
                    "verification_scope": "window",
                }
                return action_record, rung_key

            session_started = False
            try:
                if "start_session" in by_name:
                    await call_checked("start_session", {})
                    session_started = True
                cursor_setup_errors: list[dict] = []
                previous_failure_source = evidence.get("failure_source", "")
                for cursor_tool, cursor_args in (
                    ("set_agent_cursor_enabled", {
                        "enabled": True, "cursor_id": driver_session,
                    }),
                    ("set_agent_cursor_motion", {
                        "cursor_id": driver_session,
                        "cursor_label": "Broccoli · background AX",
                        "cursor_opacity": 0.92,
                        "dwell_after_click_ms": 220,
                        "idle_hide_ms": 0,
                    }),
                ):
                    if cursor_tool not in by_name:
                        continue
                    try:
                        await call_checked(cursor_tool, cursor_args)
                    except asyncio.CancelledError:
                        raise
                    except Exception as exc:
                        cursor_setup_errors.append({
                            "tool": cursor_tool,
                            "error": _clip(_flatten_error(exc), 500),
                        })
                        evidence["failure_source"] = previous_failure_source
                evidence["cursor_setup"] = {
                    "available": not bool(cursor_setup_errors),
                    "errors": _json_safe(cursor_setup_errors),
                    "action_delivery_continues": True,
                }

                permissions_payload: Any = {}
                if "check_permissions" in by_name:
                    permission_args = (
                        {"prompt": False}
                        if "prompt" in _schema_properties(by_name["check_permissions"]["inputSchema"])
                        else {}
                    )
                    result, _driver_args = await call_checked("check_permissions", permission_args)
                    permissions_payload = _structured_payload(result)
                    missing = _missing_permissions(permissions_payload)
                    if missing:
                        evidence["failure_source"] = "driver"
                        raise RuntimeError(
                            "CuaDriver lacks macOS permissions: " + ", ".join(missing) + ". "
                            "Open System Settings > Privacy & Security and enable CuaDriver under "
                            "Accessibility and Screen Recording (or run `cua-driver permissions grant` "
                            "in Terminal), then retry."
                        )

                if isolated_daemon is not None:
                    required_private_tools = {"check_permissions", "set_config", "get_config", "get_desktop_state"}
                    missing_private_tools = sorted(required_private_tools - set(by_name))
                    if missing_private_tools:
                        raise _DesktopIsolationUnavailable(
                            "CU_DESKTOP_SCOPE_NOT_ISOLATED: private daemon lacks required tools: "
                            + ", ".join(missing_private_tools)
                        )
                    await call_checked("set_config", {"capture_scope": "desktop"})
                    config_result, _config_args = await call_checked("get_config", {})
                    attested, attestation = _attest_private_desktop_daemon(
                        permissions_payload, _structured_payload(config_result), isolated_daemon,
                    )
                    if not attested:
                        evidence["desktop_isolation"]["attestation"] = _json_safe(attestation)
                        raise _DesktopIsolationUnavailable(
                            "CU_DESKTOP_SCOPE_NOT_ISOLATED: private daemon TCC/config attestation failed."
                        )
                    cursor_hidden_for_probe = False
                    if "set_agent_cursor_enabled" in by_name:
                        try:
                            await call_checked("set_agent_cursor_enabled", {
                                "enabled": False, "cursor_id": driver_session,
                            })
                            cursor_hidden_for_probe = True
                        except Exception:
                            evidence["failure_source"] = ""
                    try:
                        capture_result, _capture_args = await call_checked("get_desktop_state", {})
                    finally:
                        if cursor_hidden_for_probe:
                            try:
                                await call_checked("set_agent_cursor_enabled", {
                                    "enabled": True, "cursor_id": driver_session,
                                })
                            except Exception:
                                evidence["failure_source"] = ""
                    capture_image = _image_from_blocks(_content_blocks(capture_result))
                    capture_payload = _unwrap_structured(_structured_payload(capture_result))
                    capture_size = _image_dimensions(capture_image)
                    dimensions_proven = (
                        isinstance(capture_payload, dict)
                        and _finite_number(capture_payload.get("screen_width")) is not None
                        and _finite_number(capture_payload.get("screen_height")) is not None
                    )
                    if not capture_image or capture_size == (0, 0) or not dimensions_proven:
                        raise _DesktopIsolationUnavailable(
                            "CU_DESKTOP_SCOPE_NOT_ISOLATED: private daemon full-desktop capture probe failed."
                        )
                    desktop_fallback.update({
                        "private_home_verified": True,
                        "tcc_identity_verified": True,
                        "capture_scope_desktop": True,
                        "capture_verified": True,
                    })
                    evidence["desktop_isolation"].update({
                        "attestation": _json_safe(attestation),
                        "capture_probe_size": list(capture_size),
                    })

                async def refresh_app_map() -> list[dict]:
                    nonlocal app_map
                    if not apps_tool_name:
                        return app_map
                    result, _driver_args = await call_checked(apps_tool_name, {})
                    parsed = _parse_app_map(_structured_payload(result))
                    app_map = parsed
                    return app_map

                async def pick_window(pid: int) -> dict | None:
                    """Resolve the frontmost usable window, including small dialogs.

                    The real schema accepts a pid filter. Icon-sized untitled
                    accessory windows rank below every real window. Current-Space/
                    on-screen state wins next; then z-order wins before area so a
                    modal does not lose to the larger main window behind it.
                    """
                    descriptor = by_name.get("list_windows")
                    if descriptor is None:
                        return None
                    request = {"pid": int(pid)} if "pid" in _schema_properties(descriptor["inputSchema"]) else {}
                    result, _driver_args = await call_checked("list_windows", request)
                    payload = _unwrap_structured(_structured_payload(result))
                    windows = payload.get("windows") if isinstance(payload, dict) else payload
                    candidates: list[tuple[tuple, dict]] = []
                    for item in windows if isinstance(windows, list) else []:
                        if not isinstance(item, dict):
                            continue
                        try:
                            if int(item.get("pid")) != int(pid):
                                continue
                            window_id = int(item.get("window_id"))
                        except (TypeError, ValueError):
                            continue
                        bounds = item.get("bounds") if isinstance(item.get("bounds"), dict) else {}
                        try:
                            area = float(bounds.get("width", 0) or 0) * float(bounds.get("height", 0) or 0)
                        except (TypeError, ValueError):
                            area = 0.0
                        try:
                            z_index = float(item.get("z_index", -1) if item.get("z_index") is not None else -1)
                        except (TypeError, ValueError):
                            z_index = -1.0
                        modal = _is_modal_window(item)
                        transition_auxiliary = _is_transition_auxiliary_window(item)
                        rank = (
                            modal,
                            not _is_accessory_window(item),
                            binding.window_id is not None and window_id == binding.window_id,
                            item.get("on_current_space") is True,
                            item.get("is_on_screen") is True,
                            z_index,
                            area,
                        )
                        selected = dict(item)
                        selected["window_id"] = window_id
                        selected["modal"] = modal
                        selected["transition_auxiliary"] = transition_auxiliary
                        candidates.append((rank, selected))
                    if not candidates:
                        return None
                    usable = [pair for pair in candidates if not pair[1].get("transition_auxiliary")]
                    if usable:
                        candidates = usable
                    else:
                        # Launch-time 30px off-screen helper bars are not app
                        # content.  Let the outer retry obtain the real window
                        # instead of binding AX/cursor state to the helper.
                        return None
                    candidates.sort(key=lambda pair: pair[0], reverse=True)
                    if str(target_display_policy.get("mode", "auto")) == "auto":
                        return candidates[0][1]

                    target_inventory = display_inventory or [
                        dict(target_display_policy.get("display") or {})
                    ]
                    for _rank, candidate in candidates:
                        ax_frame = None
                        try:
                            preflight_args: dict = {
                                "pid": int(pid),
                                "window_id": int(candidate["window_id"]),
                                "max_elements": min(WINDOW_OBSERVE_MAX_ELEMENTS, 80),
                            }
                            observe_properties = _schema_properties(window_tool["inputSchema"])
                            if "include_screenshot" in observe_properties:
                                preflight_args["include_screenshot"] = False
                            # Only the structured elements are read here (see tree_format
                            # note at the per-step observation).
                            if "tree_format" in observe_properties:
                                preflight_args["tree_format"] = "elements"
                            preflight, _preflight_driver_args = await call_checked(
                                WINDOW_OBSERVE_TOOL, preflight_args,
                            )
                            ax_frame = _ax_window_frame(
                                _structured_elements(_structured_payload(preflight))
                            )
                        except Exception:
                            # No AX proof means only the CG bounds can establish
                            # display ownership; failure never widens to auto.
                            ax_frame = None
                            evidence["failure_source"] = ""
                        address_frame = ax_frame or _rect(candidate.get("bounds"))
                        assignment = _assign_window_to_display(address_frame, target_inventory)
                        if candidate.get("modal") is True:
                            selected = dict(candidate)
                            selected["display_preflight"] = assignment
                            selected["display_address_frame"] = _json_safe(address_frame or {})
                            selected["display_policy_match"] = _display_matches_policy(
                                assignment, target_display_policy,
                            )
                            selected["ax_only_cross_display"] = not bool(
                                selected["display_policy_match"]
                            )
                            return selected
                        if _display_matches_policy(assignment, target_display_policy):
                            selected = dict(candidate)
                            selected["display_preflight"] = assignment
                            selected["display_address_frame"] = _json_safe(address_frame or {})
                            selected["display_policy_match"] = True
                            return selected
                    # AX is application-scoped and does not touch a physical
                    # display.  When no real content window belongs to the
                    # selected display, observe the best real window for AX
                    # only; the pixel guard below remains display-strict.
                    selected = dict(candidates[0][1])
                    selected["display_policy_match"] = False
                    selected["ax_only_cross_display"] = True
                    return selected

                async def observe(
                        _geometry_warmup_remaining: int = 2,
                ) -> tuple[str, bytes, float, tuple[int, int], dict, list[dict]]:
                    """Return text/image geometry plus the exact window and structured elements."""
                    nonlocal observation_sequence, geometry_epoch, geometry_stability
                    nonlocal last_geometry_signature, force_geometry_epoch
                    refresh_display_topology()
                    if desktop_fallback.get("active"):
                        if not all(desktop_fallback.get(key) is True for key in (
                                "isolated_daemon", "private_home_verified", "force_proxy",
                                "tcc_identity_verified", "capture_scope_desktop", "capture_verified",
                                "authorized", "target_is_main")):
                            raise _FatalTaskError(
                                "CU_DESKTOP_SCOPE_NOT_ISOLATED: desktop observation lost its isolation/display attestation."
                            )
                        grounded = dict(desktop_fallback.get("last_window") or {})
                        try:
                            grounded_pid = int(grounded.get("pid") or 0)
                        except (TypeError, ValueError):
                            grounded_pid = 0
                        main_display = _main_display_record(display_inventory, target_display_policy)
                        if grounded_pid <= 0 or main_display is None:
                            raise _FatalTaskError(
                                "CU_SELECTED_DISPLAY_UNSUPPORTED_083: desktop fallback lacks a fresh "
                                "grounded PID or unique main-display geometry."
                            )
                        list_descriptor = by_name.get("list_windows")
                        if list_descriptor is None:
                            raise _FatalTaskError(
                                "CU_DESKTOP_SCOPE_NOT_ISOLATED: list_windows is required to contain desktop input."
                            )
                        list_request = (
                            {"pid": grounded_pid}
                            if "pid" in _schema_properties(list_descriptor["inputSchema"])
                            else {}
                        )
                        windows_result, _windows_args = await call_checked("list_windows", list_request)
                        owner_windows = _desktop_owner_window_rects(
                            _structured_payload(windows_result), grounded_pid, main_display,
                            int(grounded.get("window_id")) if grounded.get("window_id") is not None else None,
                        )
                        cursor_hidden_for_capture = False
                        if "set_agent_cursor_enabled" in by_name:
                            try:
                                await call_checked("set_agent_cursor_enabled", {
                                    "enabled": False, "cursor_id": driver_session,
                                })
                                cursor_hidden_for_capture = True
                            except Exception:
                                evidence["failure_source"] = ""
                        try:
                            result, _driver_args = await call_checked("get_desktop_state", {})
                        finally:
                            if cursor_hidden_for_capture:
                                try:
                                    await call_checked("set_agent_cursor_enabled", {
                                        "enabled": True, "cursor_id": driver_session,
                                    })
                                except Exception:
                                    evidence["failure_source"] = ""
                        image = _image_from_blocks(_content_blocks(result))
                        image_size = _image_dimensions(image)
                        payload = _unwrap_structured(_structured_payload(result))
                        if not image or image_size == (0, 0) or not isinstance(payload, dict):
                            raise _FatalTaskError(
                                "CU_DESKTOP_SCOPE_NOT_ISOLATED: fresh full-desktop capture failed."
                            )
                        if not desktop_fallback.get("fresh_snapshot_id"):
                            geometry_epoch += 1
                            geometry_stability = 1
                        else:
                            geometry_stability += 1
                        observation_sequence += 1
                        snapshot_id = f"{driver_session}:d{observation_sequence:04d}"
                        geometry = {
                            "classification": "DESKTOP_MAIN",
                            "pixel_safe": True,
                            "reason": "Fresh task-private main-display capture from the isolated daemon.",
                            "image_size": list(image_size),
                            "scope": "desktop",
                        }
                        window_context = {
                            **grounded,
                            "geometry": geometry,
                            "snapshot_id": snapshot_id,
                            "geometry_epoch": geometry_epoch,
                            "geometry_stability": geometry_stability,
                            "desktop_snapshot": True,
                            "desktop_owner_windows": _json_safe(owner_windows),
                            "main_display_bounds": _json_safe(main_display.get("bounds") or {}),
                            "display_assignment": _json_safe(
                                (desktop_fallback.get("last_window") or {}).get("display_assignment") or {}
                            ),
                        }
                        desktop_fallback["fresh_snapshot_id"] = snapshot_id
                        desktop_fallback["owner_windows"] = _json_safe(owner_windows)
                        evidence["desktop_isolation"]["last_desktop_snapshot_id"] = snapshot_id
                        observed = (
                            f"Fresh MAIN-DISPLAY desktop snapshot: snapshot_id={snapshot_id}, "
                            f"geometry_epoch={geometry_epoch}. This is an explicit Stage/window fallback. "
                            "Coordinates refer to this displayed full-desktop image. A pixel action MUST include "
                            "scope='desktop' plus the grounded target pid/window_id shown below; the worker removes "
                            "those target fields only after validating the binding. Never reuse coordinates from a "
                            "window snapshot. The worker permits coordinates only inside the fresh visible-window "
                            f"union for this PID ({len(owner_windows)} window(s)); Dock, menu bar, and other apps are blocked. "
                            "AX handles are unavailable in this vision-only fallback.\n"
                            f"Grounded target: pid={grounded.get('pid')}, window_id={grounded.get('window_id')}, "
                            f"app={grounded.get('app', '')}.\n"
                        )
                        return observed, image, 1.0, (0, 0), window_context, []
                    if window_tool is not None and binding.identities:
                        if binding.pid is None:
                            await refresh_app_map()
                            for identity in list(binding.identities):
                                entry = _app_entry_for(identity, app_map)
                                if entry is not None and entry.get("pid") is not None:
                                    binding.add("", entry)
                                    break
                        if binding.pid is not None:
                            selected_window = None
                            for settling_attempt in range(3):
                                selected_window = await pick_window(binding.pid)
                                if selected_window is not None:
                                    break
                                if settling_attempt < 2:
                                    await asyncio.sleep(0.15)
                            if selected_window is None:
                                evidence["failure_source"] = "progress"
                                raise _FatalTaskError(
                                    "CU_WINDOW_SETTLING_TIMEOUT: no real application window replaced the "
                                    "launch/Stage transition helper after three bounded observations; no input "
                                    f"was sent to pid {binding.pid}."
                                )
                            binding.window_id = int(selected_window["window_id"])
                            observe_args: dict = {
                                "pid": binding.pid,
                                "window_id": binding.window_id,
                                "max_elements": WINDOW_OBSERVE_MAX_ELEMENTS,
                            }
                            # cua-driver 0.35 returns only tree_markdown by default. Without
                            # an explicit "both" the structured elements are empty, and
                            # token validation, geometry and the pixel path all fail.
                            if "tree_format" in _schema_properties(window_tool["inputSchema"]):
                                observe_args["tree_format"] = "both"
                            result, _driver_args = await call_checked(WINDOW_OBSERVE_TOOL, observe_args)
                            blocks = _content_blocks(result)
                            structured = _structured_payload(result)
                            elements = _structured_elements(structured)
                            unwrapped = _unwrap_structured(structured)
                            markdown = ""
                            if isinstance(unwrapped, dict):
                                markdown = str(unwrapped.get("tree_markdown", "") or "")
                            # Only the driver's own tree text: the summary-block fallback
                            # carries per-read snapshot ids and would differ every time.
                            # A walk cut short by a timeout ends at a random row (Photos:
                            # 45-77 elements across idle reads), so its text is no evidence.
                            timed_out_walk = isinstance(unwrapped, dict) \
                                and unwrapped.get("truncated") is True \
                                and "timeout" in str(unwrapped.get("truncation_reason", "") or "")
                            tree_text_sha256 = "" if timed_out_walk else _tree_text_signature(markdown)
                            if not markdown:
                                markdown = _text_from_blocks(blocks)
                            image = _image_from_blocks(blocks)
                            element_text, omitted_elements = _model_elements_json(elements)
                            geometry = _classify_window_geometry(
                                selected_window.get("bounds"), elements, _image_dimensions(image),
                                selected_window.get("is_on_screen"),
                                selected_window.get("on_current_space"),
                            )
                            display_address_frame = (
                                geometry.get("ax_frame")
                                if _rect(geometry.get("ax_frame")) is not None
                                else selected_window.get("bounds")
                            )
                            assignment_inventory = display_inventory
                            if not assignment_inventory and target_display_policy.get("mode") == "display":
                                assignment_inventory = [dict(target_display_policy.get("display") or {})]
                            display_assignment = _assign_window_to_display(
                                display_address_frame, assignment_inventory,
                            )
                            display_policy_match = bool(
                                str(target_display_policy.get("mode", "auto")) == "auto"
                                or _display_matches_policy(display_assignment, target_display_policy)
                            )
                            window_context = {
                                "pid": binding.pid,
                                "window_id": binding.window_id,
                                "app": binding.label,
                                "title": str(selected_window.get("title", "") or ""),
                                "on_current_space": selected_window.get("on_current_space"),
                                "is_on_screen": selected_window.get("is_on_screen"),
                                "z_index": selected_window.get("z_index"),
                                "bounds": _json_safe(selected_window.get("bounds") or {}),
                                "geometry": geometry,
                                "display_address_frame": _json_safe(display_address_frame or {}),
                                "display_assignment": display_assignment,
                                "display_policy_match": display_policy_match,
                                "ax_only_cross_display": bool(
                                    not display_policy_match
                                    and str(target_display_policy.get("mode", "auto")) == "display"
                                ),
                            }
                            signature = _geometry_signature(window_context)
                            if force_geometry_epoch or not last_geometry_signature \
                                    or signature != last_geometry_signature:
                                geometry_epoch += 1
                                geometry_stability = 1
                                last_geometry_signature = signature
                                force_geometry_epoch = False
                            else:
                                geometry_stability += 1
                            observation_sequence += 1
                            window_context.update({
                                "snapshot_id": f"{driver_session}:s{observation_sequence:04d}",
                                "geometry_epoch": geometry_epoch,
                                "geometry_stability": geometry_stability,
                                "tree_text_sha256": tree_text_sha256,
                            })
                            if geometry.get("pixel_safe") is True \
                                    and display_policy_match \
                                    and geometry_stability < 2 \
                                    and _geometry_warmup_remaining > 0:
                                # Pixel safety requires two matching real
                                # observations.  Perform that bounded read-only
                                # warm-up inside the worker instead of asking the
                                # model to burn a NOT_DELIVERED action merely to
                                # obtain another snapshot.
                                await asyncio.sleep(0.08)
                                return await observe(_geometry_warmup_remaining - 1)
                            header = (
                                f"Bound window snapshot: pid={binding.pid}, window_id={binding.window_id}, "
                                f"snapshot_id={window_context['snapshot_id']}, geometry_epoch={geometry_epoch}, "
                                f"geometry={geometry.get('classification')}, stable_observations={geometry_stability}. "
                                "Structured elements are authoritative for addressing. Always use AX "
                                "element_token/index first when the target exists in the tree. Use window x/y only "
                                "when geometry is ALIGNED and the target is absent from AX.\n"
                            )
                            if not geometry.get("pixel_safe"):
                                header += (
                                    "WINDOW PIXEL INPUT IS CURRENTLY PROHIBITED: "
                                    f"{geometry.get('reason', 'geometry is not safe')}. AX actions remain available.\n"
                                )
                            elif not display_policy_match:
                                header += (
                                    "WINDOW PIXEL INPUT IS CURRENTLY PROHIBITED: the real app window is outside "
                                    "the explicitly selected display. Background AX remains available and the "
                                    "window will not be moved.\n"
                                )
                            if not image:
                                header += (
                                    "NO WINDOW SCREENSHOT THIS TURN: the driver returned no composited pixels for "
                                    "this window (typical for a freshly launched or Stage-hidden window). Only the "
                                    "AX tree below is fresh evidence; pixel coordinates and visual claims are "
                                    "unavailable until a screenshot returns. Effect verification runs on the AX "
                                    "tree alone this turn.\n"
                                )
                            observed = header
                            if elements:
                                if omitted_elements:
                                    observed += (
                                        f"Model snapshot includes {len(elements) - omitted_elements}/{len(elements)} "
                                        "elements (interactive roles first; full list remains authoritative in the worker).\n"
                                    )
                                observed += "Structured elements:\n" + element_text + "\n"
                            if markdown:
                                observed += "Tree markdown (back-compat):\n" + _clip(markdown, TREE_TEXT_LIMIT)
                            return observed, image, 1.0, (0, 0), window_context, elements
                    if window_tool is not None and apps_tool_name:
                        apps = await refresh_app_map()
                        listing = json.dumps({"apps": apps}, ensure_ascii=False) if apps else ""
                        return (
                            "Running apps snapshot (choose or launch the target; every state-changing call "
                            "needs an explicit bundle_id/pid and may explicitly switch apps within this approved task):\n"
                            + _clip(listing, APPS_TEXT_LIMIT),
                            b"", 1.0, (0, 0), {}, [],
                        )
                    if legacy_screenshot is not None:
                        result, _driver_args = await call_checked(legacy_screenshot["name"], {})
                        image = _image_from_blocks(_content_blocks(result))
                        if not image:
                            raise RuntimeError("Driver screenshot tool returned no image content.")
                        observation_sequence += 1
                        return "", image, 1.0, (0, 0), {
                            "snapshot_id": f"{driver_session}:s{observation_sequence:04d}",
                            "geometry_epoch": 0,
                            "geometry_stability": observation_sequence,
                            "geometry": {
                                "classification": GEOMETRY_LEGACY,
                                "pixel_safe": True,
                                "reason": "Legacy screenshot-only driver surface.",
                                "image_size": list(_image_dimensions(image)),
                            },
                        }, []
                    raise RuntimeError("Driver offers no usable observation for the current state.")

                async def restore_expanded_front() -> None:
                    """Best-effort restore of the app that was frontmost before a
                    worker-owned destination expand. Safe to call repeatedly."""
                    if not expand_restore or expand_restore.get("restored"):
                        return
                    expand_restore["restored"] = True
                    previous = expand_restore.get("previous") or {}
                    try:
                        previous_pid = int(previous.get("pid") or 0)
                    except (TypeError, ValueError):
                        previous_pid = 0
                    if previous_pid <= 0 or "bring_to_front" not in by_name:
                        return
                    try:
                        await call_checked("bring_to_front", {"pid": previous_pid})
                    except Exception:
                        try:
                            await _cli_driver_call("bring_to_front", {"pid": previous_pid})
                        except Exception:
                            pass

                if _stage_manager_enabled() is True:
                    if _set_stage_manager(False):
                        stage_manager_was_on = True
                        _emit_progress({
                            "step": 0,
                            "actions": ["stage_manager_off"],
                            "target": "Stage Manager",
                            "mode": "environment prep",
                            "outcome": EFFECT_CONFIRMED,
                            "notice": (
                                "Stage Manager was on: temporarily disabled for this task (restored at the end). "
                                "Parked windows do not render, which silently breaks background input."
                            ),
                        })
                        # Dock restarts; give the desktop a moment to settle.
                        await asyncio.sleep(2.0)

                for step in range(1, max_steps + 1):
                    if _cancelled(config):
                        return _cancelled_result(config, evidence)
                    try:
                        if unknown_launch_binding:
                            unknown_launch_binding["attempts"] = int(
                                unknown_launch_binding.get("attempts", 0) or 0
                            ) + 1
                            launch_identity = str(
                                unknown_launch_binding.get("identity", "") or ""
                            )
                            try:
                                launch_action_index = int(
                                    unknown_launch_binding.get("action_index", -1)
                                )
                            except (TypeError, ValueError):
                                launch_action_index = -1
                            candidate_entry = None
                            try:
                                await refresh_app_map()
                                candidate_entry = _app_entry_for(
                                    launch_identity, app_map,
                                )
                            except Exception:
                                # This is a bounded read-only recovery probe;
                                # the exact launch replay barrier remains active.
                                candidate_entry = None
                            candidate_pid = None
                            if isinstance(candidate_entry, dict):
                                try:
                                    parsed_pid = int(candidate_entry.get("pid") or 0)
                                except (TypeError, ValueError):
                                    parsed_pid = 0
                                if parsed_pid > 0:
                                    candidate_pid = parsed_pid
                            if candidate_pid is not None:
                                binding.rebind(launch_identity, candidate_entry)
                                binding.window_id = None
                                force_geometry_epoch = True
                                geometry_stability = 0
                                last_geometry_signature = ()
                                if 0 <= launch_action_index < len(actions):
                                    launch_record = actions[launch_action_index]
                                    launch_record["routing_binding_candidate_pid"] = candidate_pid
                                    launch_record["routing_binding_candidate_label"] = str(
                                        candidate_entry.get("name")
                                        or candidate_entry.get("bundle_id")
                                        or launch_identity
                                    )
                                    launch_record["routing_binding_observation"] = {
                                        "fresh_app_map": True,
                                        "candidate_available": True,
                                        "launch_causality_confirmed": False,
                                        "unknown_replay_barrier_preserved": True,
                                    }
                                unknown_launch_binding = {}
                            elif int(unknown_launch_binding.get("attempts", 0) or 0) >= 3:
                                if 0 <= launch_action_index < len(actions):
                                    actions[launch_action_index][
                                        "routing_binding_observation"
                                    ] = {
                                        "fresh_app_map": True,
                                        "candidate_available": False,
                                        "attempts": int(
                                            unknown_launch_binding.get("attempts", 0) or 0
                                        ),
                                        "unknown_replay_barrier_preserved": True,
                                    }
                                unknown_launch_binding = {}
                        observed_text, image_bytes, ratio, original_size, window_context, elements = await observe()
                        current_fingerprint = ""
                        data_url = ""
                        # The semantic half of the fingerprint needs only the AX
                        # tree. A hidden/freshly launched window with no composited
                        # pixels must still yield a comparable effect baseline, or
                        # every background action settles INDETERMINATE forever.
                        fingerprint_components: dict = _observation_fingerprint(
                            image_bytes, elements,
                            str((window_context or {}).get("tree_text_sha256", "") or ""),
                        )
                        if str(fingerprint_components.get("basis", "") or "") == "none":
                            # No pixels and no AX elements: zero evidence. An empty
                            # dict keeps effect verification at INDETERMINATE instead
                            # of comparing two constant hashes into a false ABSENT.
                            fingerprint_components = {}
                        else:
                            current_fingerprint = str(fingerprint_components.get("combined", "") or "")
                            evidence["latest_fingerprint"] = current_fingerprint
                            evidence["latest_window"] = dict(window_context)
                        if image_bytes:
                            evidence["latest_original"] = image_bytes
                            resized, ratio, original_size = _resize_screenshot(image_bytes)
                            data_url = "data:image/png;base64," + base64.b64encode(resized).decode("ascii")
                        if pending_action_index is not None and 0 <= pending_action_index < len(actions):
                            pending_record = actions[pending_action_index]
                            observed_effect_status, effect_evidence = _verify_action_effect(
                                pending_record, fingerprint_components, window_context, elements,
                            )
                            unknown_delivery = str(
                                pending_record.get("delivery_outcome", "") or ""
                            ) == DELIVERY_UNKNOWN_AFTER_ATTEMPT
                            strong_unknown_confirmation = bool(
                                unknown_delivery
                                and _unknown_delivery_has_strong_confirmation(
                                    pending_record, observed_effect_status, effect_evidence,
                                )
                            )
                            if unknown_delivery and not strong_unknown_confirmation:
                                effect_evidence = dict(effect_evidence or {})
                                effect_evidence["candidate_observation_status"] = observed_effect_status
                                effect_evidence["observation_reason"] = str(
                                    effect_evidence.get("reason", "") or ""
                                )
                                effect_evidence["reason"] = (
                                    "The driver reply was lost after dispatch and the next observation did not "
                                    "prove an action-specific exact postcondition; exact replay remains blocked."
                                )
                                effect_status = EFFECT_INDETERMINATE
                            else:
                                effect_status = observed_effect_status
                            pending_record["effect_status"] = effect_status
                            pending_record["effect_evidence"] = _json_safe(effect_evidence)
                            pending_record["post_snapshot_id"] = window_context.get("snapshot_id", "")
                            pending_record["post_window"] = _json_safe(window_context)
                            pending_record["post_fingerprint_components"] = _json_safe(fingerprint_components)
                            pending_replay_hash = str(
                                pending_record.get("unknown_replay_signature_sha256", "") or ""
                            )
                            if strong_unknown_confirmation and pending_replay_hash:
                                unknown_replay_barriers.pop(pending_replay_hash, None)
                                pending_record["unknown_replay_barrier"] = {
                                    "active": False,
                                    "unknown_replay_signature_sha256": pending_replay_hash,
                                    "operation_signature_sha256": str(
                                        pending_record.get("operation_signature_sha256", "") or ""
                                    ),
                                    "source_step": pending_record.get("step"),
                                    "resolved_by_snapshot_id": window_context.get("snapshot_id", ""),
                                }
                            elif unknown_delivery and pending_replay_hash:
                                pending_record["unknown_replay_barrier"] = {
                                    "active": pending_replay_hash in unknown_replay_barriers,
                                    "unknown_replay_signature_sha256": pending_replay_hash,
                                    "operation_signature_sha256": str(
                                        pending_record.get("operation_signature_sha256", "") or ""
                                    ),
                                    "source_step": pending_record.get("step"),
                                    "candidate_observation_status": observed_effect_status,
                                }
                            if effect_status == EFFECT_CONFIRMED:
                                if pending_record.get("pixel_insert_rescue") is True:
                                    # The px-form write landed: the next snapshot's
                                    # visual+semantic oracle changed. No AX read-back
                                    # exists for a non-AX body; disclose the method.
                                    transfer_buffer["insert_verified"] = True
                                    transfer_buffer["destination"] = {
                                        "pid": window_context.get("pid"),
                                        "window_id": window_context.get("window_id"),
                                        "snapshot_id": window_context.get("snapshot_id", ""),
                                        "method": "pixel_type_text_visual_confirmation",
                                    }
                                    if binding.label:
                                        app_slug = re.sub(
                                            r"[^a-z0-9]+", "-", binding.label.lower(),
                                        ).strip("-")
                                        evidence.setdefault("experience_candidates", []).append({
                                            "fact_key": f"nonaxbody-{app_slug}",
                                            "app": binding.label,
                                            "name": f"{binding.label} body is a non-AX surface",
                                            "steps_nl": (
                                                f"The {binding.label} body area is not in the accessibility tree; "
                                                "a pixel-path write was confirmed by visual+semantic change."
                                            ),
                                            "rule_nl": "Write this app's body via the pixel path directly; skip focus clicks.",
                                            "kind": "hook_params",
                                            "payload": {"hook": "non_ax_body"},
                                            "evidence": (
                                                f"pixel write CONFIRMED at snapshot "
                                                f"{window_context.get('snapshot_id', '')}"
                                            ),
                                        })
                                if str(pending_record.get("tool", "") or "").lower() in {
                                        "drag", "drag_mouse", "mouse_drag",
                                } and str(pending_record.get("address_mode", "") or "") in PIXEL_ADDRESS_MODES:
                                    copy_selection_grant = {
                                        "pid": window_context.get("pid"),
                                        "window_id": window_context.get("window_id"),
                                        "snapshot_id": str(window_context.get("snapshot_id", "") or ""),
                                        "geometry_epoch": window_context.get("geometry_epoch"),
                                        "authorized_by_step": pending_record.get("step"),
                                        "state_epoch": verified_state_epoch + 1,
                                        "consumed": False,
                                    }
                                else:
                                    copy_selection_grant = {}
                                if str(pending_record.get("tool", "") or "") == "insert_captured_text":
                                    pending_oracle = pending_record.get("oracle") \
                                        if isinstance(pending_record.get("oracle"), dict) else {}
                                    buffer_metadata = transfer_buffer.get("metadata") \
                                        if isinstance(transfer_buffer.get("metadata"), dict) else {}
                                    expected_hash = str(
                                        pending_oracle.get("expected_text_sha256", "") or ""
                                    )
                                    if expected_hash and expected_hash == str(
                                            buffer_metadata.get("sha256", "") or ""
                                    ):
                                        transfer_buffer["insert_verified"] = True
                                        transfer_buffer["destination"] = {
                                            "pid": window_context.get("pid"),
                                            "window_id": window_context.get("window_id"),
                                            "snapshot_id": window_context.get("snapshot_id", ""),
                                            "element_token": str(
                                                (pending_record.get("arguments") or {}).get(
                                                    "element_token", ""
                                                ) or ""
                                            ),
                                        }
                                    _reconcile_private_insert_fallback(
                                        actions, pending_action_index,
                                    )
                                    private_insert_grant = {}
                                    insert_fallback_source_index = None
                                foreground_grant = {}
                                weak_absence_retry = {}
                                no_effect_streak = 0
                                no_effect_counts.clear()
                                effect_calls_since_confirmation = 0
                                verified_state_epoch += 1
                                desktop_fallback["desktop_attempted"] = False
                                unresolved_action_failure = False
                                _reconcile_confirmed_retry(actions, pending_action_index)
                                _reconcile_unknown_launch_routing(
                                    actions, pending_action_index,
                                )
                                retire_effect_chain(pending_record)
                            elif effect_status == EFFECT_ABSENT:
                                copy_selection_grant = {}
                                operation_hash = str(
                                    pending_record.get("effect_chain_id", "")
                                    or pending_record.get("operation_signature_sha256", "")
                                    or f"step:{pending_record.get('step')}"
                                )
                                no_effect_counts[operation_hash] = no_effect_counts.get(operation_hash, 0) + 1
                                no_effect_streak = no_effect_counts[operation_hash]
                                pending_record["error_code"] = "CU_ACTION_NO_EFFECT"
                                pending_record["structured_error"] = _policy_error(
                                    "CU_ACTION_NO_EFFECT",
                                    "The next fresh semantic/perceptual observation proves no effect.",
                                    stage="verification", retriable=True,
                                    snapshot_id=window_context.get("snapshot_id", ""),
                                )
                                pending_driver_meta = pending_record.get("driver_arguments") \
                                    if isinstance(pending_record.get("driver_arguments"), dict) else {}
                                pending_insert_method = str(
                                    pending_driver_meta.get("driver_tool", "") or ""
                                ).lower()
                                if str(pending_record.get("tool", "") or "") \
                                        == "insert_captured_text" \
                                        and pending_insert_method == "set_value":
                                    # The set_value call was unambiguously
                                    # delivered, and this fresh exact AX readback
                                    # proves it had no effect. The next worker-
                                    # owned rung may now use background type_text.
                                    insert_fallback_source_index = pending_action_index
                                    private_insert_grant = {}
                                    foreground_grant = {}
                                elif str(pending_record.get("tool", "") or "") \
                                        == "insert_captured_text" \
                                        and pending_insert_method == "type_text" \
                                        and str(
                                            (pending_record.get("arguments") or {}).get(
                                                "delivery_mode", "background"
                                            )
                                        ).lower() == "background":
                                    candidate, grant_evidence = \
                                        _build_private_insert_type_text_grant(
                                            pending_record, window_context, elements,
                                            _private_transfer_log_metadata(transfer_buffer),
                                            delivery_mode="foreground",
                                        )
                                    pending_record["private_insert_foreground_grant"] = \
                                        _json_safe(grant_evidence)
                                    if candidate is not None:
                                        candidate["source_action_index"] = pending_action_index
                                        private_insert_grant = candidate
                                    else:
                                        private_insert_grant = {}
                                    foreground_grant = {}
                                else:
                                    foreground_grant = _build_transient_foreground_grant(
                                        pending_record, window_context,
                                    ) or {}
                                    if foreground_grant and not _absence_proven_exactly(pending_record):
                                        # Only the coarse fingerprint stayed the same. An automatic
                                        # re-send would duplicate input whenever the effect was just
                                        # too small to register, so the model decides from the
                                        # screenshot; an identical re-send then runs this rung.
                                        foreground_grant = {}
                                        weak_absence_retry = {
                                            "source_index": pending_action_index,
                                            "rung": _rung_tuple(pending_record.get("rung_key")),
                                            "label": _weak_absence_label(pending_record),
                                        }
                                        pending_record["foreground_retry"] = "awaiting_model_confirmation"
                                # A coarse-only verdict is handed to the model, which may judge
                                # from the screenshot that the effect is there and finish; the
                                # action still reports as unverified. Exact absences keep
                                # blocking completion.
                                unresolved_action_failure = not (
                                    weak_absence_retry
                                    and weak_absence_retry.get("source_index") == pending_action_index
                                )
                            else:
                                copy_selection_grant = {}
                                foreground_grant = {}
                                private_insert_grant = {}
                                # Clipboard copy/selection and other visually
                                # silent actions do not burn the no-progress breaker.
                                unresolved_action_failure = False
                                if not unknown_delivery:
                                    # An unverifiable settlement must not ban the
                                    # operation until the next epoch (which itself
                                    # needs a confirmed effect): grant one retry.
                                    pending_rung = _rung_tuple(pending_record.get("rung_key"))
                                    if pending_rung and pending_rung in attempted_rungs:
                                        pending_op_hash = _rung_operation_sha256(pending_rung)
                                        if indeterminate_unburns.get(pending_op_hash, 0) < 1:
                                            indeterminate_unburns[pending_op_hash] = \
                                                indeterminate_unburns.get(pending_op_hash, 0) + 1
                                            attempted_rungs.discard(pending_rung)
                                            pending_record["indeterminate_retry_unlocked"] = True
                            _emit_progress({
                                "step": pending_record.get("step"),
                                "actions": [f"{pending_record.get('tool', 'action')} verification"],
                                "target": pending_record.get("resolved_target_label") or binding.label,
                                "mode": "verification",
                                "outcome": effect_status,
                                "notice": "The previous action was settled by the fresh window/AX observation.",
                            })
                            pending_action_index = None

                        if insert_fallback_source_index is not None:
                            source_index = insert_fallback_source_index
                            insert_fallback_source_index = None
                            if 0 <= source_index < len(actions):
                                source_action = actions[source_index]
                                source_delivery = str(
                                    source_action.get("delivery_outcome", "") or ""
                                )
                                if source_delivery == DELIVERY_DRIVER_ERROR:
                                    # Even an explicit driver rejection is
                                    # observed once before changing methods: a
                                    # buggy driver may have partially written.
                                    fallback_status, fallback_effect = \
                                        _verify_action_effect(
                                            source_action, fingerprint_components,
                                            window_context, elements,
                                        )
                                    source_action["post_snapshot_id"] = \
                                        window_context.get("snapshot_id", "")
                                    source_action["post_window"] = _json_safe(window_context)
                                    source_action["post_fingerprint_components"] = \
                                        _json_safe(fingerprint_components)
                                    source_action["effect_evidence"] = _json_safe(
                                        fallback_effect
                                    )
                                    exact_transition = bool(
                                        fallback_status == EFFECT_CONFIRMED
                                        and fallback_effect.get(
                                            "action_specific_text_transition"
                                        ) is True
                                    )
                                    if exact_transition:
                                        source_action["effect_status"] = EFFECT_CONFIRMED
                                        source_action[
                                            "transport_error_superseded_by_exact_readback"
                                        ] = True
                                        source_action["result"] = (
                                            "Fresh exact AX readback confirmed the private transfer despite "
                                            "the driver's earlier explicit error response."
                                        )
                                        buffer_metadata = transfer_buffer.get("metadata") \
                                            if isinstance(
                                                transfer_buffer.get("metadata"), dict
                                            ) else {}
                                        source_oracle = source_action.get("oracle") \
                                            if isinstance(source_action.get("oracle"), dict) else {}
                                        if str(source_oracle.get(
                                                "expected_text_sha256", ""
                                        ) or "") == str(buffer_metadata.get("sha256", "") or ""):
                                            transfer_buffer["insert_verified"] = True
                                            transfer_buffer["destination"] = {
                                                "pid": window_context.get("pid"),
                                                "window_id": window_context.get("window_id"),
                                                "snapshot_id": window_context.get(
                                                    "snapshot_id", ""
                                                ),
                                            }
                                        if failures > 0:
                                            failures -= 1
                                        unresolved_action_failure = False
                                        evidence["failure_source"] = ""
                                        no_effect_streak = 0
                                        no_effect_counts.clear()
                                        effect_calls_since_confirmation = 0
                                        verified_state_epoch += 1
                                        _reconcile_confirmed_retry(actions, source_index)
                                        _reconcile_unknown_launch_routing(
                                            actions, source_index,
                                        )
                                        retire_effect_chain(source_action)
                                        _emit_progress({
                                            "step": source_action.get("step"),
                                            "actions": ["insert_captured_text verification"],
                                            "target": source_action.get(
                                                "resolved_target_label"
                                            ) or binding.label,
                                            "mode": "verification",
                                            "outcome": EFFECT_CONFIRMED,
                                            "notice": (
                                                "The driver returned an error, but a fresh exact AX hash read-back proves the "
                                                "write landed; no other input channel will be tried."
                                            ),
                                        })
                                    elif fallback_status == EFFECT_ABSENT:
                                        source_action["effect_status"] = EFFECT_ABSENT
                                    else:
                                        source_action["private_insert_fallback"] = {
                                            "authorized": False,
                                            "reason": (
                                                "set_value rejection could not be settled as exact success "
                                                "or exact absence on the next fresh AX observation"
                                            ),
                                            "candidate_status": fallback_status,
                                        }
                                if source_action.get("effect_status") == EFFECT_ABSENT:
                                    candidate, grant_evidence = \
                                        _build_private_insert_type_text_grant(
                                            source_action, window_context, elements,
                                            _private_transfer_log_metadata(transfer_buffer),
                                            delivery_mode="background",
                                        )
                                    source_action["private_insert_fallback"] = \
                                        _json_safe(grant_evidence)
                                    if candidate is not None:
                                        candidate["source_action_index"] = source_index
                                        private_insert_grant = candidate

                        if private_insert_grant:
                            insert_grant = private_insert_grant
                            private_insert_grant = {}
                            insert_record, insert_rung = await dispatch_private_type_text(
                                insert_grant, step=step,
                                current_window=window_context,
                                current_elements=elements,
                                current_fingerprint=current_fingerprint,
                                fingerprint_components=fingerprint_components,
                            )
                            insert_record["private_insert_source_action_index"] = \
                                insert_grant.get("source_action_index")
                            actions.append(insert_record)
                            insert_index = len(actions) - 1
                            insert_replay_hash = str(
                                insert_record.get("unknown_replay_signature_sha256", "") or ""
                            )
                            if insert_replay_hash \
                                    and insert_record.get("delivery_outcome") \
                                    == DELIVERY_UNKNOWN_AFTER_ATTEMPT:
                                unknown_replay_barriers[insert_replay_hash] = {
                                    "action_index": insert_index,
                                    "delivery_outcome": DELIVERY_UNKNOWN_AFTER_ATTEMPT,
                                }
                                insert_record["unknown_replay_barrier"] = {
                                    "active": True,
                                    "unknown_replay_signature_sha256": insert_replay_hash,
                                    "operation_signature_sha256": insert_record.get(
                                        "operation_signature_sha256", ""
                                    ),
                                    "source_step": insert_record.get("step"),
                                }
                            insert_delivery = str(
                                insert_record.get("delivery_outcome", "") or ""
                            )
                            if insert_delivery in {
                                    DELIVERY_DELIVERED_UNVERIFIED,
                                    DELIVERY_UNKNOWN_AFTER_ATTEMPT}:
                                pending_action_index = insert_index
                                effect_calls_since_confirmation += 1
                            if insert_delivery == DELIVERY_DELIVERED_UNVERIFIED:
                                failures = 0
                                unresolved_action_failure = False
                                evidence["failure_source"] = ""
                            elif insert_delivery == DELIVERY_UNKNOWN_AFTER_ATTEMPT:
                                failures += 1
                                unresolved_action_failure = True
                                evidence["failure_source"] = "driver"
                            else:
                                failures += 1
                                unresolved_action_failure = True
                                evidence["failure_source"] = (
                                    "driver" if insert_record.get("driver_attempted") else "progress"
                                )
                            insert_mode = str(
                                (insert_record.get("arguments") or {}).get(
                                    "delivery_mode", "background"
                                )
                            ).lower()
                            _emit_progress({
                                "step": step,
                                "actions": ["insert_captured_text" + (
                                    "" if insert_record.get("is_error") is not True
                                    else " (failed/refused)"
                                )],
                                "target": binding.label,
                                "mode": (
                                    "transient foreground retry" if insert_mode == "foreground"
                                    else "background AX text fallback"
                                ),
                                "outcome": insert_record.get("effect_status"),
                                "notice": (
                                    "Background AX type_text proved ineffective; performing one exact transient-"
                                    "foreground retry (the driver restores the prior app afterwards)."
                                    if insert_mode == "foreground" else
                                    "set_value proved ineffective in the fresh AX observation; trying one background "
                                    "type_text on the same empty text target only."
                                ),
                            })
                            continue

                        if foreground_grant_source_index is not None:
                            source_index = foreground_grant_source_index
                            foreground_grant_source_index = None
                            if 0 <= source_index < len(actions):
                                foreground_grant = _build_transient_foreground_grant(
                                    actions[source_index], window_context,
                                ) or {}

                        # A foreground retry is worker-owned routing, not a
                        # model suggestion.  Execute the one exact grant on the
                        # same fresh post-observation, consume it before the
                        # call, and verify it on the next loop like any action.
                        if foreground_grant:
                            grant = dict(foreground_grant)
                            foreground_grant = {}
                            foreground_name = str(grant.get("tool", "") or "")
                            foreground_descriptor = by_name.get(foreground_name)
                            foreground_arguments = copy.deepcopy(grant.get("arguments") or {})
                            foreground_arguments["delivery_mode"] = "foreground"
                            foreground_address_mode = str(grant.get("address_mode", "direct") or "direct")
                            foreground_allowed, foreground_authorization = \
                                _transient_foreground_authorized(
                                    grant, foreground_name, foreground_arguments,
                                    foreground_address_mode,
                                    window_context,
                                    identity=str(grant.get("target_identity", "") or ""),
                                    original_arguments=grant.get("original_arguments") or foreground_arguments,
                                )
                            if foreground_descriptor is None or not foreground_allowed:
                                evidence["failure_source"] = "progress"
                                raise _FatalTaskError(
                                    "CU_FOREGROUND_GRANT_INVALIDATED: the worker-created one-shot foreground "
                                    "grant no longer matches the fresh window/tool state; it was consumed without "
                                    "sending input."
                                )
                            if foreground_descriptor is not None and foreground_allowed:
                                foreground_properties = _schema_properties(
                                    foreground_descriptor["inputSchema"]
                                )
                                if "delivery_mode" not in foreground_properties:
                                    evidence["failure_source"] = "driver"
                                    raise _FatalTaskError(
                                        "CU_TRANSIENT_FOREGROUND_UNSUPPORTED: the exact driver tool has no "
                                        "delivery_mode field, so the worker cannot truthfully execute a transient "
                                        "foreground retry."
                                    )
                                foreground_oracle = dict(grant.get("oracle") or {})
                                foreground_rung = _action_rung_key(
                                    foreground_name, foreground_arguments, foreground_address_mode,
                                    foreground_oracle, window_context,
                                    str(grant.get("target_identity", "") or ""),
                                    elements=elements,
                                    original_arguments=grant.get("original_arguments") or foreground_arguments,
                                    state_epoch=int(grant.get("state_epoch", verified_state_epoch) or 0),
                                )
                                foreground_driver_arguments = copy.deepcopy(grant.get("driver_arguments") or {})
                                foreground_driver_arguments["delivery_mode"] = "foreground"
                                foreground_driver_arguments = _with_driver_session(
                                    foreground_driver_arguments,
                                    foreground_descriptor["inputSchema"], driver_session,
                                )
                                foreground_replay_arguments = (
                                    foreground_driver_arguments
                                    if foreground_address_mode in PIXEL_ADDRESS_MODES
                                    else foreground_arguments
                                )
                                foreground_replay_hash = _unknown_replay_operation_sha256(
                                    foreground_name, foreground_replay_arguments,
                                    foreground_address_mode, window_context,
                                    str(grant.get("target_identity", "") or ""),
                                    elements=elements,
                                    original_arguments=(
                                        grant.get("original_arguments") or foreground_arguments
                                    ),
                                )
                                foreground_error = ""
                                foreground_structured: Any = None
                                foreground_blocks: list[dict] = []
                                foreground_summary = ""
                                foreground_driver_error = False
                                foreground_delivery = DELIVERY_UNKNOWN_AFTER_ATTEMPT
                                foreground_result: Any = None
                                foreground_clipboard_evidence: dict = {}
                                foreground_clipboard_before: dict = {}
                                foreground_clipboard_original_text = ""
                                foreground_clipboard_probe: dict = {}
                                foreground_preflight_blocked = False
                                foreground_copy = str(
                                    foreground_oracle.get("kind", "") or ""
                                ) == "clipboard_copy"
                                if foreground_copy:
                                    _emit_progress({
                                        "step": step,
                                        "actions": ["clipboard_overwrite_notice"],
                                        "target": binding.label,
                                        "mode": "system_clipboard",
                                        "notice": (
                                            "About to perform one transient-foreground real copy: the system clipboard may be "
                                            "overwritten; the copied text stays task-private and logs keep only hash and length."
                                        ),
                                    })
                                    foreground_clipboard_original_text, foreground_clipboard_before = \
                                        _clipboard_text_snapshot()
                                    if foreground_clipboard_before.get("available") is True:
                                        foreground_clipboard_probe = _clipboard_write_text(
                                            "__BROCCOLI_CU_COPY_PROBE_" + uuid.uuid4().hex + "__"
                                        )
                                    else:
                                        # Never send an unverifiable foreground
                                        # copy or install a sentinel that cannot
                                        # be restored.
                                        foreground_clipboard_probe = {
                                            "available": False,
                                            "reason": "clipboard_baseline_unavailable",
                                        }
                                        foreground_clipboard_evidence = {
                                            "overwrite_disclosed": True,
                                            "before": foreground_clipboard_before,
                                            "probe": foreground_clipboard_probe,
                                            "changed": False,
                                            "absence_proven": False,
                                            "raw_text_logged": False,
                                        }
                                        foreground_preflight_blocked = True
                                        foreground_delivery = DELIVERY_NOT_ATTEMPTED
                                        foreground_error = "CU_CLIPBOARD_BASELINE_UNAVAILABLE"
                                        foreground_summary = (
                                            "The system clipboard could not be read, so no foreground "
                                            "copy or private probe was sent."
                                        )
                                if not foreground_preflight_blocked:
                                    try:
                                        # The exact rung is consumed immediately before
                                        # delivery. A timeout/driver exception is an
                                        # unknown result, never permission to replay it.
                                        attempted_rungs.add(foreground_rung)
                                        effect_calls_since_confirmation += 1
                                        foreground_result = await _call_tool(
                                            session, foreground_name,
                                            foreground_driver_arguments, step_timeout,
                                        )
                                        foreground_driver_error = _result_is_error(foreground_result)
                                        foreground_delivery = (
                                            DELIVERY_DRIVER_ERROR if foreground_driver_error
                                            else DELIVERY_DELIVERED_UNVERIFIED
                                        )
                                        foreground_summary = _result_summary(foreground_result)
                                        foreground_structured = _json_safe(_structured_payload(foreground_result))
                                        foreground_blocks = _log_content_blocks(foreground_result)
                                    except asyncio.CancelledError:
                                        if foreground_copy:
                                            _clipboard_probe_result(
                                                foreground_clipboard_original_text,
                                                foreground_clipboard_before,
                                                foreground_clipboard_probe,
                                            )
                                        raise
                                    except Exception as exc:
                                        foreground_summary = _flatten_error(exc)
                                        foreground_error = "CU_DRIVER_DELIVERY_UNKNOWN"
                                        foreground_driver_error = True
                                foreground_confirmed = bool(
                                    foreground_result is not None
                                    and not foreground_driver_error
                                    and _driver_confirms_effect(foreground_result)
                                )
                                foreground_copy_absent = False
                                if foreground_copy and not foreground_preflight_blocked:
                                    await asyncio.sleep(0.12)
                                    changed, foreground_copy_absent, \
                                        foreground_clipboard_evidence = \
                                        settle_clipboard_transfer(
                                            foreground_clipboard_original_text,
                                            foreground_clipboard_before,
                                            foreground_clipboard_probe,
                                            foreground_oracle,
                                            window_context,
                                            "verified_foreground_clipboard_copy",
                                        )
                                    foreground_confirmed = changed
                                    if changed:
                                        foreground_driver_error = False
                                        foreground_error = ""
                                        foreground_summary = (
                                            "Transient foreground copy replaced the private clipboard probe and "
                                            "captured a non-empty payload into the private transfer buffer."
                                        )
                                    elif foreground_copy_absent:
                                        foreground_driver_error = False
                                        foreground_summary = (
                                            "Transient foreground copy left the private clipboard probe unchanged; "
                                            "the prior clipboard text was restored."
                                        )
                                foreground_effect = (
                                    EFFECT_CONFIRMED if foreground_confirmed
                                    else EFFECT_ABSENT if foreground_copy_absent
                                    else EFFECT_INDETERMINATE
                                    if foreground_delivery == DELIVERY_UNKNOWN_AFTER_ATTEMPT
                                    else EFFECT_NOT_DELIVERED
                                    if foreground_driver_error or foreground_preflight_blocked
                                    else EFFECT_PENDING
                                )
                                if foreground_copy_absent:
                                    foreground_error = "CU_CLIPBOARD_UNCHANGED"
                                if foreground_preflight_blocked:
                                    unresolved_action_failure = True
                                    evidence["failure_source"] = "progress"
                                elif foreground_driver_error and not foreground_confirmed:
                                    failures += 1
                                    unresolved_action_failure = True
                                    evidence["failure_source"] = "driver"
                                    if not foreground_error:
                                        foreground_error = "CU_DRIVER_ERROR"
                                else:
                                    failures = 0
                                    unresolved_action_failure = False
                                    evidence["failure_source"] = ""
                                foreground_record = {
                                    "step": step,
                                    "tool": foreground_name,
                                    "arguments": _json_safe(foreground_arguments),
                                    "sanitized_arguments": _json_safe(foreground_arguments),
                                    "original_arguments": _json_safe(
                                        grant.get("original_arguments") or foreground_arguments
                                    ),
                                    "driver_arguments": _json_safe(foreground_driver_arguments),
                                    "address_mode": foreground_address_mode,
                                    "allowed": not foreground_preflight_blocked,
                                    "executed": not foreground_preflight_blocked,
                                    "driver_attempted": not foreground_preflight_blocked,
                                    "delivery_outcome": foreground_delivery,
                                    "worker_local": False,
                                    "is_error": foreground_driver_error,
                                    "error_code": foreground_error,
                                    "structured_error": (
                                        _policy_error(
                                            foreground_error,
                                            foreground_summary or "Transient foreground delivery failed.",
                                            stage="delivery", retriable=False,
                                        ) if foreground_error else None
                                    ),
                                    "result": _clip(foreground_summary, 2000),
                                    "raw_summary": _clip(foreground_summary, 2000),
                                    "structured": foreground_structured,
                                    "structured_content": foreground_structured,
                                    "content_blocks": foreground_blocks,
                                    "effect_confirmed": foreground_confirmed,
                                    "effect_status": foreground_effect,
                                    "oracle": _json_safe(foreground_oracle),
                                    "effect_chain_id": (
                                        str(grant.get("effect_chain_id", "") or "")
                                        if (
                                            foreground_delivery == DELIVERY_DELIVERED_UNVERIFIED
                                            or (foreground_copy and foreground_confirmed)
                                        )
                                        else ""
                                    ),
                                    "rung_key": _json_safe(list(foreground_rung)),
                                    "operation_signature_sha256": _rung_operation_sha256(
                                        foreground_rung
                                    ),
                                    "quota_reconciliation_signature_sha256": (
                                        _quota_reconciliation_operation_sha256(
                                            foreground_name, foreground_arguments,
                                            foreground_address_mode, foreground_oracle,
                                            window_context,
                                            str(grant.get("target_identity", "") or ""),
                                            elements=elements,
                                            original_arguments=(
                                                grant.get("original_arguments")
                                                or foreground_arguments
                                            ),
                                        )
                                    ),
                                    "unknown_replay_signature_sha256": foreground_replay_hash,
                                    "transient_foreground_authorization": _json_safe(foreground_authorization),
                                    "copy_selection_authorization": _json_safe(
                                        grant.get("copy_selection_authorization")
                                        if isinstance(grant.get("copy_selection_authorization"), dict)
                                        else {}
                                    ),
                                    "cursor": {
                                        "available": foreground_address_mode == "window_pixel",
                                        "mode": "driver_pixel_session_overlay",
                                        "real_pointer_moved": False,
                                    },
                                    "clipboard": _json_safe(foreground_clipboard_evidence),
                                    "session": driver_session,
                                    "target_identity": str(grant.get("target_identity", "") or ""),
                                    "resolved_target_pid": binding.pid,
                                    "resolved_target_label": binding.label,
                                    "window": _json_safe(window_context),
                                    "snapshot_id": window_context.get("snapshot_id", ""),
                                    "geometry_epoch": window_context.get("geometry_epoch"),
                                    "verified_state_epoch": int(
                                        grant.get("state_epoch", verified_state_epoch) or 0
                                    ),
                                    "geometry": _json_safe(window_context.get("geometry") or {}),
                                    "fingerprint": current_fingerprint,
                                    "fingerprint_components": _json_safe(fingerprint_components),
                                    "verification_fingerprint_components": _json_safe(fingerprint_components),
                                    "verification_scope": "window",
                                }
                                actions.append(foreground_record)
                                foreground_index = len(actions) - 1
                                foreground_operation_hash = str(
                                    foreground_record.get("operation_signature_sha256", "") or ""
                                )
                                if foreground_replay_hash \
                                        and foreground_oracle.get("replay_sensitive") is True \
                                        and foreground_delivery == DELIVERY_UNKNOWN_AFTER_ATTEMPT:
                                    unknown_replay_barriers[foreground_replay_hash] = {
                                        "action_index": foreground_index,
                                        "delivery_outcome": foreground_delivery,
                                    }
                                    foreground_record["unknown_replay_barrier"] = {
                                        "active": True,
                                        "unknown_replay_signature_sha256": foreground_replay_hash,
                                        "operation_signature_sha256": foreground_operation_hash,
                                        "source_step": foreground_record.get("step"),
                                    }
                                _emit_progress({
                                    "step": step,
                                    "actions": [foreground_name + (
                                        "" if not foreground_driver_error else " (failed/refused)"
                                    )],
                                    "target": binding.label,
                                    "mode": "transient foreground retry",
                                    "outcome": foreground_effect,
                                    "notice": "Background delivery proved ineffective; performing one exact transient-foreground retry and restoring the prior app.",
                                })
                                if foreground_effect in {EFFECT_PENDING, EFFECT_INDETERMINATE}:
                                    pending_action_index = foreground_index
                                elif foreground_effect == EFFECT_CONFIRMED:
                                    verified_state_epoch += 1
                                    no_effect_streak = 0
                                    no_effect_counts.clear()
                                    effect_calls_since_confirmation = 0
                                    _reconcile_confirmed_retry(actions, len(actions) - 1)
                                    _reconcile_unknown_launch_routing(
                                        actions, len(actions) - 1,
                                    )
                                    retire_effect_chain(foreground_record)
                                continue

                        if expand_restore and not expand_restore.get("restored") \
                                and transfer_buffer.get("insert_verified") is True:
                            restore_previous = expand_restore.get("previous") or {}
                            await restore_expanded_front()
                            _emit_progress({
                                "step": step,
                                "actions": ["bring_to_front (restore)"],
                                "target": str(
                                    restore_previous.get("name", "")
                                    or f"pid {restore_previous.get('pid', '')}"
                                ),
                                "mode": "restore foreground",
                                "outcome": EFFECT_CONFIRMED,
                                "notice": "The write is verified; the previously frontmost app has been restored.",
                            })

                        expand_geometry = window_context.get("geometry") \
                            if isinstance(window_context.get("geometry"), dict) else {}
                        expand_parked = str(expand_geometry.get("classification", "")) in {
                            GEOMETRY_STAGE_TRANSFORMED, GEOMETRY_OFFSCREEN,
                        }
                        expand_needs_materialization = False
                        if _transfer_buffer_pending(transfer_buffer) and expand_parked:
                            # A parked SwiftUI window renders (and therefore exposes)
                            # only its sidebar: folder-name AXTextFields may look
                            # writable, but the note-body text AREA the pending write
                            # needs simply is not in the tree. That structural gap is
                            # the expand trigger - not wasted no-effect attempts.
                            expand_needs_materialization = not any(
                                any(
                                    marker in str(target.get("role", "")).replace("_", "").lower()
                                    for marker in ("textarea", "textview", "editabletext")
                                )
                                for target in _writable_ax_targets(elements)
                            )
                        if (
                                binding.pid is not None
                                and expand_parked
                                and (
                                    # Write phase: the destination's body text area is
                                    # structurally absent from the parked tree.
                                    expand_needs_materialization
                                    # Any phase: delivered actions keep having no
                                    # effect on an unrendered window (e.g. the app
                                    # lives on an inactive display/Space).
                                    or sum(no_effect_counts.values()) >= 2
                                )
                                and "bring_to_front" in by_name
                        ):
                            if int(binding.pid) in expand_transition_pids:
                                evidence["failure_source"] = "progress"
                                raise _FatalTaskError(
                                    "CU_DESTINATION_UI_NOT_MATERIALIZED: the target window is still "
                                    "Stage-parked/off-screen after the authorized expand transition tried "
                                    "BOTH the daemon and fresh-CLI activation paths, so its content UI is "
                                    "not rendered into the AX tree and no further input can honestly help. "
                                    "Expand the target window manually and rerun."
                                )
                            expand_transition_pids.add(int(binding.pid))
                            previous_front: dict = {}
                            try:
                                if "list_apps" in by_name:
                                    apps_result, _apps_args = await call_checked("list_apps", {})
                                    apps_payload = _unwrap_structured(_structured_payload(apps_result))
                                    for app_item in (
                                            apps_payload.get("apps")
                                            if isinstance(apps_payload, dict) else None
                                    ) or []:
                                        if not isinstance(app_item, dict):
                                            continue
                                        try:
                                            app_pid = int(app_item.get("pid") or 0)
                                        except (TypeError, ValueError):
                                            continue
                                        if app_item.get("active") is True and app_pid > 0 \
                                                and app_pid != int(binding.pid):
                                            previous_front = {
                                                "pid": app_pid,
                                                "name": str(app_item.get("name", "") or ""),
                                            }
                                            break
                            except Exception:
                                previous_front = {}
                            front_arguments: dict = {"pid": int(binding.pid)}
                            if binding.window_id is not None:
                                front_arguments["window_id"] = int(binding.window_id)

                            async def _expand_unparked() -> bool:
                                """Did some real (non-thumbnail) window of the pid appear on screen?"""
                                try:
                                    check_result, _check_args = await call_checked("list_windows", {})
                                    payload = _unwrap_structured(_structured_payload(check_result))
                                    windows = payload.get("windows") \
                                        if isinstance(payload, dict) else None
                                    for item in windows or []:
                                        if not isinstance(item, dict) \
                                                or item.get("pid") != int(binding.pid):
                                            continue
                                        bounds = item.get("bounds") or {}
                                        if item.get("is_on_screen") \
                                                and float(bounds.get("width", 0) or 0) >= 400 \
                                                and float(bounds.get("height", 0) or 0) >= 300:
                                            return True
                                except Exception:
                                    return False
                                return False

                            expand_summary = ""
                            expand_error = ""
                            expand_path = ""
                            try:
                                expand_result, _front_args = await call_checked(
                                    "bring_to_front", front_arguments,
                                )
                                expand_summary = _clip(_result_summary(expand_result), 500)
                                expand_path = "daemon"
                            except Exception as exc:
                                expand_error = _flatten_error(exc)
                            await asyncio.sleep(1.0)
                            if not await _expand_unparked():
                                # Daemon-context activation is silently ignored by
                                # Stage Manager on this machine; the same call from
                                # a fresh CLI process is honored (verified). Escalate
                                # before giving up.
                                cli_summary = await _cli_driver_call(
                                    "bring_to_front", front_arguments,
                                )
                                await asyncio.sleep(1.2)
                                if await _expand_unparked():
                                    expand_error = ""
                                    expand_path = "cli"
                                    expand_summary = _clip(cli_summary, 300)
                                else:
                                    expand_error = expand_error or (
                                        "activation was accepted but the window stayed parked "
                                        "after both the daemon and CLI attempts"
                                    )
                                    if not expand_summary:
                                        expand_summary = _clip(cli_summary, 300)
                            # A later expand (e.g. Notes after News) must keep the
                            # FIRST recorded frontmost app: that is the user's own
                            # app; the intermediate one is a window we fronted.
                            original_previous = (
                                expand_restore.get("previous")
                                if isinstance(expand_restore.get("previous"), dict)
                                and expand_restore.get("previous") else previous_front
                            )
                            expand_restore.clear()
                            expand_restore.update({
                                "expanded_pid": int(binding.pid),
                                "expanded_label": binding.label,
                                "previous": original_previous,
                                "restored": False,
                            })
                            actions.append({
                                "step": step,
                                "tool": "bring_to_front",
                                "worker_owned_expand": True,
                                "expand_path": expand_path,
                                "arguments": _json_safe(front_arguments),
                                "address_mode": "topology",
                                "allowed": True,
                                "executed": not expand_error,
                                "driver_attempted": True,
                                "is_error": bool(expand_error),
                                "error_code": "CU_DRIVER_ERROR" if expand_error else "",
                                "result": expand_summary or expand_error,
                                "raw_summary": expand_summary or expand_error,
                                "previous_frontmost": _json_safe(previous_front),
                                "target_identity": f"pid:{binding.pid}",
                                "resolved_target_pid": binding.pid,
                                "resolved_target_label": binding.label,
                                "session": driver_session,
                                "effect_status": (
                                    EFFECT_CONFIRMED if not expand_error else EFFECT_NOT_DELIVERED
                                ),
                            })
                            _emit_progress({
                                "step": step,
                                "actions": ["bring_to_front (worker expand)"],
                                "target": binding.label,
                                "mode": "foreground expand",
                                "outcome": str(actions[-1]["effect_status"]),
                                "notice": (
                                    "The target window renders no operable content while Stage-parked/off-screen; "
                                    "expanded it once under standing authorization; the prior app is restored after the write."
                                ),
                            })
                            if not expand_error:
                                binding.window_id = None
                                force_geometry_epoch = True
                                geometry_stability = 0
                                last_geometry_signature = ()
                            continue

                        if (
                                binding.pid is not None
                                and window_context.get("ax_only_cross_display") is True
                                and str(expand_geometry.get("classification", "")) == GEOMETRY_ALIGNED
                                and int(window_context.get("geometry_stability", 0) or 0) >= 2
                                and int(binding.pid) not in relocate_transition_pids
                                and "drag" in by_name
                        ):
                            # The task window lives on a different display than the
                            # user-selected target. The driver's own title-bar drag
                            # (foreground mode; background is "background_unavailable")
                            # physically relocates the window; verified on this
                            # machine by bounds read-back. One attempt per app.
                            relocate_transition_pids.add(int(binding.pid))
                            relocate_display = dict(target_display_policy.get("display") or {})
                            relocate_display_bounds = _rect(relocate_display.get("bounds"))
                            relocate_window_bounds = _rect(window_context.get("bounds"))
                            relocate_scale_x = float(expand_geometry.get("png_scale_x") or 1.0) or 1.0
                            relocate_scale_y = float(expand_geometry.get("png_scale_y") or 1.0) or 1.0
                            if relocate_display_bounds is not None and relocate_window_bounds is not None:
                                relocate_from_x = relocate_window_bounds["width"] * relocate_scale_x / 2.0
                                relocate_from_y = 12.0 * relocate_scale_y
                                # Aim gently: window horizontally centered on the
                                # target display (side-margin minimum), top edge just
                                # inside, and the WHOLE window contained - never flung
                                # toward an edge. Margins are experience-rule tunable.
                                relocate_top_margin, relocate_side_margin = 60.0, 24.0
                                if _experience is not None and experience_rules:
                                    try:
                                        relocate_top_margin, relocate_side_margin = \
                                            _experience.relocate_margins(
                                                experience_rules, binding.label,
                                            )
                                    except Exception:
                                        relocate_top_margin, relocate_side_margin = 60.0, 24.0
                                relocate_dest_x = relocate_display_bounds["x"] + max(
                                    relocate_side_margin,
                                    (relocate_display_bounds["width"]
                                     - relocate_window_bounds["width"]) / 2.0,
                                )
                                relocate_dest_y = relocate_display_bounds["y"] + max(
                                    0.0,
                                    min(
                                        relocate_top_margin,
                                        relocate_display_bounds["height"]
                                        - relocate_window_bounds["height"] - 12.0,
                                    ),
                                )
                                relocate_delta_x = relocate_dest_x - relocate_window_bounds["x"]
                                relocate_delta_y = relocate_dest_y - relocate_window_bounds["y"]
                                relocate_arguments: dict = {
                                    "pid": int(binding.pid),
                                    "from_x": relocate_from_x,
                                    "from_y": relocate_from_y,
                                    "to_x": relocate_from_x + relocate_delta_x * relocate_scale_x,
                                    "to_y": relocate_from_y + relocate_delta_y * relocate_scale_y,
                                    "duration_ms": 700,
                                    "steps": 28,
                                    "delivery_mode": "foreground",
                                }
                                if binding.window_id is not None:
                                    relocate_arguments["window_id"] = int(binding.window_id)
                                async def _relocated_to_target() -> bool:
                                    """Is a real window of the pid now inside the target display?"""
                                    try:
                                        check_result, _check_args = await call_checked("list_windows", {})
                                        payload = _unwrap_structured(_structured_payload(check_result))
                                        windows = payload.get("windows") \
                                            if isinstance(payload, dict) else None
                                        for item in windows or []:
                                            if not isinstance(item, dict) \
                                                    or item.get("pid") != int(binding.pid):
                                                continue
                                            bounds = _rect(item.get("bounds"))
                                            if bounds is None or bounds["width"] < 400 \
                                                    or bounds["height"] < 300:
                                                continue
                                            if (relocate_display_bounds["x"] <= bounds["x"]
                                                    < relocate_display_bounds["x"]
                                                    + relocate_display_bounds["width"]
                                                    and relocate_display_bounds["y"] <= bounds["y"]
                                                    < relocate_display_bounds["y"]
                                                    + relocate_display_bounds["height"]):
                                                return True
                                    except Exception:
                                        return False
                                    return False

                                async def _relocate_origin_now() -> tuple | None:
                                    """Fresh CG origin of this exact window, or None."""
                                    try:
                                        check_result, _check_args = await call_checked("list_windows", {})
                                        payload = _unwrap_structured(_structured_payload(check_result))
                                        windows = payload.get("windows") \
                                            if isinstance(payload, dict) else None
                                        for item in windows or []:
                                            if isinstance(item, dict) \
                                                    and item.get("pid") == int(binding.pid) \
                                                    and item.get("window_id") == binding.window_id:
                                                bounds = _rect(item.get("bounds"))
                                                if bounds is not None:
                                                    return (bounds["x"], bounds["y"])
                                    except Exception:
                                        return None
                                    return None

                                relocate_origin_before = (
                                    relocate_window_bounds["x"], relocate_window_bounds["y"],
                                )
                                relocate_summary = ""
                                relocate_error = ""
                                relocate_path = ""
                                try:
                                    relocate_result, _relocate_args = await call_checked(
                                        "drag", relocate_arguments,
                                    )
                                    relocate_summary = _clip(_result_summary(relocate_result), 500)
                                    relocate_path = "daemon"
                                except Exception as exc:
                                    relocate_error = _flatten_error(exc)
                                relocate_verified = False
                                for _relocate_poll in range(3):
                                    await asyncio.sleep(1.0)
                                    if await _relocated_to_target():
                                        relocate_verified = True
                                        break
                                if not relocate_verified:
                                    # Before ANY re-drag, check whether the first drag
                                    # actually moved the window: re-applying the same
                                    # window-local delta to an already-moved window
                                    # doubles the displacement and flings it off the
                                    # display (observed on this machine).
                                    origin_now = await _relocate_origin_now()
                                    moved_already = bool(
                                        origin_now is not None
                                        and (abs(origin_now[0] - relocate_origin_before[0]) >= 80.0
                                             or abs(origin_now[1] - relocate_origin_before[1]) >= 80.0)
                                    )
                                    if moved_already:
                                        # The daemon drag landed somewhere; accept the
                                        # partial move rather than doubling it. The next
                                        # observation re-derives geometry honestly.
                                        relocate_error = ""
                                        relocate_path = relocate_path or "daemon"
                                        relocate_summary = relocate_summary or (
                                            "window moved but target-display containment is unverified"
                                        )
                                    else:
                                        # Same silent-degradation escape hatch as the
                                        # expand transition: one retry via a fresh CLI
                                        # process of the same signed binary.
                                        cli_summary = await _cli_driver_call(
                                            "drag", relocate_arguments, timeout=12.0,
                                        )
                                        await asyncio.sleep(1.2)
                                        if await _relocated_to_target():
                                            relocate_error = ""
                                            relocate_path = "cli"
                                            relocate_summary = _clip(cli_summary, 300)
                                        else:
                                            relocate_error = relocate_error or (
                                                "the window did not land on the target display "
                                                "after both the daemon and CLI drag attempts"
                                            )
                                            if not relocate_summary:
                                                relocate_summary = _clip(cli_summary, 300)
                                actions.append({
                                    "step": step,
                                    "tool": "drag",
                                    "worker_owned_relocate": True,
                                    "relocate_path": relocate_path,
                                    "arguments": _json_safe(relocate_arguments),
                                    "address_mode": "window_pixel",
                                    "allowed": True,
                                    "executed": not relocate_error,
                                    "driver_attempted": True,
                                    "is_error": bool(relocate_error),
                                    "error_code": "CU_DRIVER_ERROR" if relocate_error else "",
                                    "result": relocate_summary or relocate_error,
                                    "raw_summary": relocate_summary or relocate_error,
                                    "target_identity": f"pid:{binding.pid}",
                                    "resolved_target_pid": binding.pid,
                                    "resolved_target_label": binding.label,
                                    "session": driver_session,
                                    "relocate_target_display": _json_safe(relocate_display),
                                    "effect_status": (
                                        EFFECT_CONFIRMED if not relocate_error else EFFECT_NOT_DELIVERED
                                    ),
                                })
                                _emit_progress({
                                    "step": step,
                                    "actions": ["drag (worker relocate)"],
                                    "target": binding.label,
                                    "mode": "cross-display move",
                                    "outcome": str(actions[-1]["effect_status"]),
                                    "notice": (
                                        "The task window was not on the selected target display; moved it there with a "
                                        "driver title-bar drag (the driver restores the prior app); the next observation verifies the new position."
                                    ),
                                })
                                if not relocate_error:
                                    binding.window_id = None
                                    force_geometry_epoch = True
                                    geometry_stability = 0
                                    last_geometry_signature = ()
                                continue
                        isolation_ready = all(desktop_fallback.get(key) is True for key in (
                            "isolated_daemon", "private_home_verified", "force_proxy",
                            "tcc_identity_verified", "capture_scope_desktop", "capture_verified",
                        ))
                        geometry = window_context.get("geometry") \
                            if isinstance(window_context.get("geometry"), dict) else {}
                        ladder_exhausted = _window_delivery_ladder_exhausted(actions, window_context)
                        can_desktop_rescue = bool(
                            ladder_exhausted
                            and not desktop_fallback.get("desktop_attempted")
                            and not desktop_fallback.get("active")
                            and str(geometry.get("classification", "")) == GEOMETRY_ALIGNED
                            and int(window_context.get("geometry_stability", 0) or 0) >= 2
                            and _desktop_target_is_main(target_display_policy, window_context) is True
                            and isolation_ready
                        )
                        if can_desktop_rescue:
                            authorizer = next(
                                (
                                    item for item in reversed(actions)
                                    if isinstance(item, dict)
                                    and item.get("effect_status") == EFFECT_ABSENT
                                    and _action_was_delivered_unverified(item)
                                    and item.get("is_error") is not True
                                    and str((item.get("arguments") or {}).get(
                                        "delivery_mode", "background"
                                    ) or "background").lower() == "foreground"
                                    and str(item.get("address_mode", "")) == "window_pixel"
                                    and str(item.get("effect_chain_id", "") or "")
                                    == str(active_effect_chain.get("id", "") or "")
                                    and (item.get("window") or {}).get("pid") == window_context.get("pid")
                                    and (item.get("window") or {}).get("window_id") == window_context.get("window_id")
                                ),
                                None,
                            )
                            if authorizer is not None:
                                authorizer_args = authorizer.get("arguments") \
                                    if isinstance(authorizer.get("arguments"), dict) else {}
                                desktop_fallback.update({
                                    "authorized": True,
                                    "active": True,
                                    "fresh_snapshot_id": "",
                                    "target_is_main": True,
                                    "last_window": copy.deepcopy(window_context),
                                    "desktop_attempted": True,
                                    "pre_desktop_fingerprint_components": copy.deepcopy(
                                        fingerprint_components
                                    ),
                                    "grant_chain_id": str(authorizer.get("effect_chain_id", "") or ""),
                                    "grant_tool": str(authorizer.get("tool", "") or ""),
                                    "grant_oracle": str(
                                        (authorizer.get("oracle") or {}).get("kind", "") or ""
                                    ),
                                    "grant_operation_signature": _operation_signature(
                                        str(authorizer.get("tool", "") or ""),
                                        authorizer_args,
                                        "window_pixel",
                                    ),
                                    "grant_operation_semantics": _desktop_operation_semantics(
                                        str(authorizer.get("tool", "") or ""),
                                        authorizer_args,
                                    ),
                                })
                                evidence["desktop_isolation"]["transition"] = {
                                    "from_snapshot_id": window_context.get("snapshot_id", ""),
                                    "from_geometry": GEOMETRY_ALIGNED,
                                    "authorized_by_step": authorizer.get("step"),
                                    "authorized_by_effect_chain": authorizer.get("effect_chain_id", ""),
                                    "state": "aligned_exact_ladder_exhausted_desktop_snapshot_required",
                                }
                                # Desktop authorization is independent of persistent
                                # foreground activation. The next turn alone creates
                                # the single fresh desktop coordinate frame.
                                continue
                        latest_desktop_no_effect = next(
                            (
                                item for item in reversed(actions)
                                if isinstance(item, dict)
                                and item.get("effect_status") == EFFECT_ABSENT
                                and str(item.get("address_mode", "") or "") == "desktop_pixel"
                                and _action_was_delivered_unverified(item)
                                and str(item.get("effect_chain_id", "") or "")
                                == str(active_effect_chain.get("id", "") or "")
                            ),
                            None,
                        )
                        def _insert_rescue_target() -> dict | None:
                            """A unique body-class writable target for the pending write.

                            Repeated focus clicks on an empty note body are
                            oracle-silent (a caret is deliberately not progress), so
                            before the no-effect breakers kill the task, redirect
                            the model to the exact-write tool instead.
                            """
                            if insert_rescue_used or not _transfer_buffer_pending(transfer_buffer):
                                return None
                            for target in _writable_ax_targets(elements):
                                if target.get("search_like"):
                                    continue
                                role_lowered = str(target.get("role", "")).replace("_", "").lower()
                                if any(marker in role_lowered for marker in (
                                        "textarea", "textview", "editabletext")):
                                    return target
                            return None

                        def _grant_insert_rescue(target: dict) -> None:
                            nonlocal insert_rescue_used, insert_rescue_directive
                            nonlocal no_effect_streak, effect_calls_since_confirmation
                            nonlocal unresolved_action_failure
                            insert_rescue_used = True
                            insert_rescue_directive = (
                                "\nMANDATORY NEXT CALL: insert_captured_text with element_token="
                                f"{target.get('element_token')} (role {target.get('role')}, label "
                                f"{str(target.get('label', ''))[:60]!r}). Your recent no-effect clicks were "
                                "focus attempts on an empty body; a caret is not observable progress. The "
                                "write itself establishes focus and is verified by exact AX read-back. Do "
                                "NOT click, double-click, or press keys first.\n"
                            )
                            no_effect_streak = 0
                            no_effect_counts.clear()
                            effect_calls_since_confirmation = 0
                            unresolved_action_failure = False
                            _emit_progress({
                                "step": step,
                                "actions": ["insert_rescue"],
                                "target": binding.label,
                                "mode": "write rescue",
                                "outcome": EFFECT_PENDING,
                                "notice": (
                                    "Repeated focus clicks on an empty body are unobservable; breakers were reset and "
                                    "the model is now required to call insert_captured_text directly."
                                ),
                            })

                        async def _perform_pixel_insert_rescue() -> bool:
                            """Driver-doc escalation for a body that is NOT in AX at all.

                            Notes' note body is a non-AX surface on this machine (the
                            driver itself reports ax_tree_empty/degraded and recommends
                            the pixel path). type_text's px form pixel-clicks to focus
                            and types in ONE call; a multi-kilobyte write is then judged
                            by the ordinary visual+semantic oracle on the next snapshot.
                            """
                            nonlocal insert_rescue_used, insert_rescue_directive
                            nonlocal no_effect_streak, effect_calls_since_confirmation
                            nonlocal unresolved_action_failure, pending_action_index
                            if insert_rescue_used or not _transfer_buffer_pending(transfer_buffer):
                                return False
                            if "type_text" not in by_name:
                                return False
                            rescue_geometry = window_context.get("geometry") \
                                if isinstance(window_context.get("geometry"), dict) else {}
                            if rescue_geometry.get("pixel_safe") is not True \
                                    or int(window_context.get("geometry_stability", 0) or 0) < 2:
                                return False
                            rescue_text = str(transfer_buffer.get("text", "") or "")
                            if not rescue_text:
                                return False
                            # Ground the focus point in the model's own last body
                            # click on this exact window; fall back to the typical
                            # body area (right pane, upper third).
                            pixel_focus = None
                            for item in reversed(actions):
                                if not isinstance(item, dict) \
                                        or item.get("effect_status") != EFFECT_ABSENT \
                                        or str(item.get("address_mode", "")) != "window_pixel" \
                                        or str(item.get("tool", "")).lower() not in {"click", "double_click"}:
                                    continue
                                grounded = item.get("window") \
                                    if isinstance(item.get("window"), dict) else {}
                                if grounded.get("pid") != window_context.get("pid") \
                                        or grounded.get("window_id") != window_context.get("window_id"):
                                    continue
                                item_driver_args = item.get("driver_arguments") \
                                    if isinstance(item.get("driver_arguments"), dict) else {}
                                if item_driver_args.get("x") is not None \
                                        and item_driver_args.get("y") is not None:
                                    try:
                                        pixel_focus = (
                                            float(item_driver_args["x"]),
                                            float(item_driver_args["y"]),
                                        )
                                    except (TypeError, ValueError):
                                        continue
                                    break
                            if pixel_focus is None:
                                image_size = rescue_geometry.get("image_size") or []
                                if isinstance(image_size, (list, tuple)) and len(image_size) == 2:
                                    try:
                                        pixel_focus = (
                                            float(image_size[0]) * 0.65,
                                            float(image_size[1]) * 0.3,
                                        )
                                    except (TypeError, ValueError):
                                        pixel_focus = None
                            if pixel_focus is None:
                                return False
                            descriptor = by_name.get("type_text")
                            rescue_driver_args = _with_driver_session({
                                "pid": window_context.get("pid"),
                                "window_id": window_context.get("window_id"),
                                "x": pixel_focus[0],
                                "y": pixel_focus[1],
                                "text": rescue_text,
                                "delivery_mode": "background",
                            }, descriptor["inputSchema"], driver_session)
                            insert_rescue_used = True
                            insert_rescue_directive = ""
                            rescue_error = ""
                            rescue_summary = ""
                            try:
                                rescue_result, _rescue_sent = await call_checked(
                                    "type_text", rescue_driver_args,
                                )
                                rescue_summary = _clip(_result_summary(rescue_result), 400)
                            except Exception as exc:
                                rescue_error = _flatten_error(exc)
                            buffer_metadata = _private_transfer_log_metadata(transfer_buffer)
                            redacted = f"[task-private transfer {buffer_metadata.get('char_count', 0)} chars]"
                            actions.append({
                                "step": step,
                                "tool": "type_text",
                                "pixel_insert_rescue": True,
                                "arguments": _json_safe({
                                    "pid": window_context.get("pid"),
                                    "window_id": window_context.get("window_id"),
                                    "x": pixel_focus[0], "y": pixel_focus[1],
                                    "delivery_mode": "background",
                                    "text": redacted,
                                }),
                                "driver_arguments": _json_safe({
                                    key: (value if key != "text" else redacted)
                                    for key, value in rescue_driver_args.items()
                                }),
                                "address_mode": "window_pixel",
                                "allowed": True,
                                "executed": not rescue_error,
                                "driver_attempted": True,
                                "delivery_outcome": (
                                    DELIVERY_DRIVER_ERROR if rescue_error
                                    else DELIVERY_DELIVERED_UNVERIFIED
                                ),
                                "is_error": bool(rescue_error),
                                "error_code": "CU_DRIVER_ERROR" if rescue_error else "",
                                "result": rescue_summary or rescue_error,
                                "raw_summary": rescue_summary or rescue_error,
                                "oracle": {
                                    "kind": "visual_mutation",
                                    "address_mode": "window_pixel",
                                    "expected_text": "",
                                    "expects_visual_change": True,
                                    "visually_silent": False,
                                    "non_idempotent": False,
                                    "replay_sensitive": False,
                                },
                                "transfer": _json_safe(buffer_metadata),
                                "target_identity": f"pid:{window_context.get('pid')}",
                                "resolved_target_pid": window_context.get("pid"),
                                "resolved_target_label": binding.label,
                                "session": driver_session,
                                "window": _json_safe(window_context),
                                "snapshot_id": window_context.get("snapshot_id", ""),
                                "geometry_epoch": window_context.get("geometry_epoch"),
                                "fingerprint_components": _json_safe(fingerprint_components),
                                "verification_fingerprint_components": _json_safe(fingerprint_components),
                                "verification_scope": "window",
                                "effect_status": (
                                    EFFECT_PENDING if not rescue_error else EFFECT_NOT_DELIVERED
                                ),
                            })
                            no_effect_streak = 0
                            no_effect_counts.clear()
                            effect_calls_since_confirmation += 1
                            unresolved_action_failure = False
                            if not rescue_error:
                                pending_action_index = len(actions) - 1
                            _emit_progress({
                                "step": step,
                                "actions": ["type_text (pixel insert rescue)"],
                                "target": binding.label,
                                "mode": "write rescue",
                                "outcome": str(actions[-1]["effect_status"]),
                                "notice": (
                                    "The body area is not in the accessibility tree (driver: non-AX surface, pixel path "
                                    "recommended); performed the documented one-call pixel focus+type; the next observation verifies the effect."
                                ),
                            })
                            return not rescue_error

                        async def _visual_progress_arbiter(boundary_reason: str) -> bool:
                            """Ask the model to LOOK before a progress-class abort.

                            The hash oracle can call \"no progress\" while the screen
                            plainly shows the article open or the note written. One
                            screenshot verdict per task may veto the abort; a STUCK
                            verdict lets the abort proceed unchanged.
                            """
                            nonlocal visual_arbiter_used, insert_rescue_directive
                            nonlocal no_effect_streak, effect_calls_since_confirmation
                            nonlocal unresolved_action_failure
                            if visual_arbiter_used or not data_url:
                                return False
                            visual_arbiter_used = True
                            arbiter_messages = [{
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": (
                                        "You are a visual arbiter for a desktop-automation worker. "
                                        "The worker's hash-based effect oracle believes the task is stuck ("
                                        + boundary_reason + ") and is about to abort. Judge the ACTUAL "
                                        "visible state of this task from the current screenshot alone:\n"
                                        + str(config.get("task", "")).strip()
                                        + "\nReply with EXACTLY one line starting with one of "
                                        "TASK_COMPLETE / PROGRESS_VISIBLE / STUCK, then one short "
                                        "sentence of on-screen evidence."
                                    )},
                                    {"type": "image_url", "image_url": {"url": data_url}},
                                ],
                            }]
                            try:
                                verdict_message = await asyncio.wait_for(
                                    _call_in_daemon_thread(
                                        _model_call, config, arbiter_messages, [],
                                    ),
                                    timeout=float(config.get("llm_timeout", 120) or 120) + 5,
                                )
                            except Exception:
                                return False
                            verdict_text = str(getattr(verdict_message, "content", "") or "").strip()
                            evidence["visual_arbiter"] = _clip(verdict_text, 400)
                            verdict_head = verdict_text.upper()[:40]
                            if "TASK_COMPLETE" not in verdict_head \
                                    and "PROGRESS_VISIBLE" not in verdict_head:
                                return False
                            no_effect_streak = 0
                            no_effect_counts.clear()
                            effect_calls_since_confirmation = 0
                            unresolved_action_failure = False
                            insert_rescue_directive = (
                                "\nVISUAL ARBITER VERDICT: " + _clip(verdict_text, 300) + "\n"
                                "The screen visibly contradicts the stuck diagnosis. If the task is "
                                "visibly complete, call finish with an honest summary; otherwise take "
                                "the next useful action based on what the screenshot shows.\n"
                            )
                            _emit_progress({
                                "step": step,
                                "actions": ["visual_arbiter"],
                                "target": binding.label,
                                "mode": "visual arbiter",
                                "outcome": EFFECT_PENDING,
                                "notice": _clip("Hash oracle saw no progress but the visual arbiter disagrees: " + verdict_text, 220),
                            })
                            return True

                        if ladder_exhausted and (
                                latest_desktop_no_effect is not None
                                or not isolation_ready
                                or _desktop_target_is_main(target_display_policy, window_context) is not True
                                or str(geometry.get("classification", "")) != GEOMETRY_ALIGNED):
                            rescue_target = _insert_rescue_target()
                            if rescue_target is not None:
                                _grant_insert_rescue(rescue_target)
                            elif await _perform_pixel_insert_rescue():
                                continue
                            elif await _visual_progress_arbiter(
                                    "background and transient-foreground rungs both settled no-effect"):
                                pass
                            else:
                                evidence["failure_source"] = "progress"
                                if latest_desktop_no_effect is not None:
                                    boundary = "the one authorized main-display desktop rescue also had no effect"
                                elif not isolation_ready:
                                    boundary = "the task-private desktop isolation path is unavailable"
                                elif _desktop_target_is_main(target_display_policy, window_context) is not True:
                                    boundary = "the grounded target is not proven to be on the main display"
                                else:
                                    boundary = "the window is no longer pixel-aligned"
                                raise _FatalTaskError(
                                    "CU_ACTION_NO_EFFECT: the exact background-window and transient-foreground "
                                    "delivery rungs produced no visible progress or semantic progress; " + boundary + ". "
                                    "No additional input was sent. This evidence does not identify an application "
                                    "framework as the cause."
                                )
                        if no_effect_streak >= NO_EFFECT_LIMIT:
                            if desktop_fallback.get("active") and desktop_fallback.get("desktop_attempted"):
                                # The one rescue snapshot still needs its single
                                # delivery attempt; preserve the original streak
                                # so a no-effect result becomes terminal.
                                pass
                            else:
                                rescue_target = _insert_rescue_target()
                                if rescue_target is not None:
                                    _grant_insert_rescue(rescue_target)
                                elif await _perform_pixel_insert_rescue():
                                    continue
                                elif await _visual_progress_arbiter(
                                        f"{no_effect_streak} delivered actions with no observable effect"):
                                    pass
                                else:
                                    evidence["failure_source"] = "progress"
                                    raise _FatalTaskError(
                                        "CU_ACTION_NO_EFFECT: Computer Use observed no visible progress in "
                                        f"{binding.label or 'the target app'}: {no_effect_streak} delivered, visibly-effectful "
                                        "actions were each followed by the same semantic/perceptual observation. The driver "
                                        "returned no delivery error, but the action-specific oracle did not confirm an effect. "
                                        "Re-ground the target/window and inspect the action log; this evidence does not identify "
                                        "an application framework as the cause."
                                    )
                        if effect_calls_since_confirmation >= EFFECT_CALL_LIMIT:
                            if await _visual_progress_arbiter(
                                    "the action-delivery budget ran out without a confirmed effect"):
                                pass
                            else:
                                evidence["failure_source"] = "progress"
                                raise _FatalTaskError(
                                    "CU_LADDER_EXHAUSTED: the six-call action-delivery budget was exhausted without a "
                                    "confirmed semantic effect."
                                )
                        experience_text = ""
                        if _experience is not None and experience_rules:
                            try:
                                experience_lines = _experience.prompt_notes(
                                    experience_rules, binding.label,
                                )
                                experience_lines += _experience.evaluate_dsl(experience_rules, {
                                    "app_label": binding.label,
                                    "geometry_class": str(
                                        (window_context.get("geometry") or {}).get("classification", "")
                                    ),
                                    "transfer_pending": _transfer_buffer_pending(transfer_buffer),
                                    "phase": (
                                        "write" if _transfer_buffer_pending(transfer_buffer)
                                        else "navigation"
                                    ),
                                    "last_error_code": str(
                                        actions[-1].get("error_code", "")
                                        if actions and isinstance(actions[-1], dict) else ""
                                    ),
                                })
                            except Exception:
                                experience_lines = []
                            seen_lines: set[str] = set()
                            deduped_lines = []
                            for line in experience_lines:
                                if line not in seen_lines:
                                    seen_lines.add(line)
                                    deduped_lines.append(line)
                            if deduped_lines:
                                experience_text = (
                                    "\nEXPERIENCE RULES (learned/user guidance; safety gates still apply):\n"
                                    + "\n".join(f"- {line}" for line in deduped_lines[:8])
                                    + "\n"
                                )
                        instruction = (
                            "You are Broccoli's local desktop automation agent. All policy and task instructions are in this user message; "
                            "do not rely on a system role. The worker owns every observation/list/get tool and gives you one fresh snapshot per turn. "
                            "You may explicitly switch among applications required by this already-approved task. Never operate Broccoli. "
                            "Every state-changing call must include the explicit target accepted by the tool (normally pid/window_id, or bundle_id for launch_app). "
                            "Make at most ONE state-changing call this turn; after it, wait for the next fresh snapshot. Do not call finish in the same turn as an action. "
                            "Prefer structured element_token addressing, then element_index; use x/y only for surfaces absent from the element list. "
                            "Clicks report verified:false by design, so verify effects only in the NEXT snapshot/tree. "
                            "Use this strict ladder across fresh snapshots: background AX element_token/index first. Only when the target is absent "
                            "from AX, or the next fresh observation proves that AX delivery had no effect, and the worker reports ALIGNED geometry, "
                            "may you use window x/y. After one exact background window-pixel or key action has a fresh EFFECT_ABSENT result "
                            "(an element-addressed press_key/hotkey counts: the worker drops the stale focus handle per the driver docs), "
                            "one exact transient-foreground retry that restores the prior app is available: the worker runs it by itself "
                            "when an exact check proved no effect; when only its coarse check saw no change, it asks you to look at the "
                            "screenshot first, and only your identical re-send runs that retry. Never request "
                            "delivery_mode='foreground' and never call bring_to_front. "
                            "Some SwiftUI rows/cells/generic elements reject AX actions with a kAXError; after a CU_AX_ACTION_UNSUPPORTED "
                            "refusal never resend that element - use the app's MENU-BAR items instead (menu items support AXPress reliably "
                            "in the background, e.g. File > New Note, Edit > Copy/Paste), or a different element. "
                            "Never combine AX handles with coordinates; omit unused schema-default fields. A Stage-parked or inactive-display/Space "
                            "window may expose only a PARTIAL, non-rendered AX tree (delivered actions settle EFFECT_ABSENT). When the pending "
                            "private text write needs a missing body area, or delivered actions keep settling EFFECT_ABSENT on such a window, "
                            "the WORKER itself performs one disclosed expand of that window (once per app) and restores the user's prior app at the "
                            "end - never call bring_to_front yourself; after the expand, act from the fresh full tree. If the window sits on a "
                            "different display than the user-selected target display, the worker relocates it there with one disclosed title-bar "
                            "drag - never attempt window-moving drags yourself. "
                            "Otherwise Stage Manager, hidden, minimized, or "
                            "off-Space geometry NEVER authorizes foregrounding and does not disable AX. When such geometry makes pixels unsafe, "
                            "continue with AX; if the required content is absent from AX, report the hidden-pixel boundary instead of trying blind "
                            "Cmd+A/C or coordinates. After an ALIGNED window's exact background-pixel and transient-foreground rungs both have fresh "
                            "EFFECT_ABSENT evidence, the worker may independently transition to one task-private MAIN-DISPLAY snapshot. "
                            "Only after that header appears may you use screenshot coordinates with "
                            "scope='desktop' and the stated grounded pid/window_id; never reuse coordinates across window/desktop snapshots. "
                            "For text transfer, prefer capture_ax_text plus insert_captured_text when the exact source text is exposed by fresh AX; "
                            "a value_preview_only/label_preview_only field is still an addressable exact source because the full value remains in worker memory. "
                            "In native destinations such as Notes, use the fresh AX New Note button and an AX text area with insert_captured_text; "
                            "do not use Cmd+N or Cmd+V when those AX targets exist. "
                            "If it is not exposed, use a visible, ALIGNED pixel drag with the agent cursor; never substitute blind selection hotkeys. "
                            "After that visible selection, a real Cmd+C may overwrite the user's system clipboard; the worker will disclose and "
                            "fingerprint it, then keep newly copied text only in the same task-private transfer buffer for insert_captured_text. "
                            "A secondary or ambiguous display has no desktop fallback in cua-driver 0.8.3. Never change driver configuration/recordings. "
                            f"Task:\n{str(config.get('task', '')).strip()}\n\nStep {step}/{max_steps}. "
                            f"Current target: {binding.label or '[not bound yet]'}. Driver session: {driver_session}. "
                            + (
                                f"Original screenshot size: {original_size[0]}x{original_size[1]}; display scale ratio: {ratio:.6f}. "
                                "Coordinates must refer to the displayed screenshot. "
                                if data_url else ""
                            )
                            + (f"\n\n{observed_text}\n\n" if observed_text else "")
                            + (
                                "\nONE FRESH VISIBLE-SELECTION COPY GRANT IS AVAILABLE: a confirmed pixel drag "
                                "in this exact window authorizes one real Cmd+C. It will overwrite the system "
                                "clipboard and the worker will verify only its hash/length.\n"
                                if copy_selection_grant else ""
                            )
                            + (
                                f"\nNO CHANGE DETECTED AFTER YOUR {weak_absence_retry.get('label') or 'previous action'}: "
                                "the worker's change check is coarse and can miss small changes (a digit, the text "
                                "caret, focus, a small icon). Look at the screenshot. If the effect is there, continue "
                                "and do NOT repeat it. Only if it clearly did not happen, send the identical call "
                                "again; the worker will then deliver it once in the transient foreground.\n"
                                if weak_absence_retry else ""
                            )
                            + (
                                "\nAN AMBIGUOUS APP-INPUT DELIVERY REMAINS UNRESOLVED: do not replay that exact "
                                "click/key/paste/create/write operation. Inspect the visible state and use a "
                                "different grounded recovery path; the worker will refuse an exact replay.\n"
                                if unknown_replay_barriers else ""
                            )
                            + _transfer_prompt(transfer_buffer, elements)
                            + experience_text
                            + insert_rescue_directive
                            + "Call exactly one available action tool, or call finish(answer) only when the fresh observation proves completion."
                        )
                        content: list[dict] = [{"type": "text", "text": instruction}]
                        if data_url:
                            content.append({"type": "image_url", "image_url": {"url": data_url}})
                        user_message = {"role": "user", "content": content}
                        messages = [item for turn in recent[-3:] for item in turn] + [user_message]
                        try:
                            message = await asyncio.wait_for(
                                _call_in_daemon_thread(_model_call, config, messages, _openai_tools(model_tools)),
                                timeout=float(config.get("llm_timeout", 120) or 120) + 5,
                            )
                        except Exception:
                            evidence["failure_source"] = "model"
                            raise
                        narrative = str(getattr(message, "content", "") or "").strip()
                        if narrative:
                            narratives.append(narrative)
                        calls = list(getattr(message, "tool_calls", None) or [])
                        assistant_record = _assistant_message_dict(message)
                        tool_records: list[dict] = []
                        step_actions: list[str] = []
                        progress_mode = ""
                        progress_outcome = ""
                        progress_notice = ""
                        if not calls:
                            if unresolved_action_failure:
                                evidence["failure_source"] = "progress"
                                raise _FatalTaskError(
                                    "The model stopped without resolving the most recent refused or failed desktop action."
                                )
                            answer = narrative or "Computer Use task completed."
                            await restore_expanded_front()
                            return _completion_result(config, evidence, answer)

                        has_state_call = any(
                            str(call.function.name or "") != "finish"
                            and (
                                str(call.function.name or "") not in by_name
                                or not _worker_owned_tool(str(call.function.name or ""))
                            )
                            for call in calls
                        )
                        state_call_seen = False
                        state_call_succeeded = False
                        for call in calls:
                            name = str(call.function.name or "")
                            try:
                                arguments = json.loads(call.function.arguments or "{}")
                            except Exception:
                                arguments = {}
                            if not isinstance(arguments, dict):
                                arguments = {}
                            model_arguments = copy.deepcopy(arguments)
                            if name == "insert_captured_text":
                                insert_rescue_directive = ""
                                transfer_metadata = transfer_buffer.get("metadata") \
                                    if isinstance(transfer_buffer.get("metadata"), dict) else {}
                                # Worker-only replay identity: safe metadata is
                                # logged, but private transfer text is never put
                                # into arguments or a durable action record.
                                model_arguments["__worker_transfer_sha256"] = str(
                                    transfer_metadata.get("sha256", "") or ""
                                )
                                model_arguments["__worker_transfer_utf8_bytes"] = int(
                                    transfer_metadata.get("utf8_bytes", 0) or 0
                                )
                                model_arguments["__worker_transfer_generation"] = int(
                                    transfer_buffer.get("generation", 0) or 0
                                )
                                model_arguments["__worker_insert_method"] = (
                                    "set_value" if "set_value" in by_name else "type_text"
                                )
                            if name == "finish":
                                if has_state_call or state_call_seen or unresolved_action_failure \
                                        or _transfer_buffer_pending(transfer_buffer):
                                    summary = (
                                        "finish was deferred: completion cannot be accepted in the same turn as a "
                                        "state-changing call, while the latest action is refused/failed, or while a "
                                        "task-private text buffer has not been inserted and read back exactly. Inspect "
                                        "a fresh snapshot and resolve the pending postcondition before finishing."
                                    )
                                    tool_records.append({"role": "tool", "tool_call_id": str(call.id), "content": summary})
                                    step_actions.append("finish (deferred)")
                                    continue
                                answer = str(arguments.get("answer", "") or narrative or "Computer Use task completed.")
                                await restore_expanded_front()
                                return _completion_result(config, evidence, answer)

                            descriptor = by_name.get(name) or synthetic_by_name.get(name)
                            allowed = False
                            executed = False
                            driver_attempted = False
                            delivery_outcome = DELIVERY_NOT_ATTEMPTED
                            is_error = False
                            structured_log: Any = None
                            content_blocks_log: list[dict] = []
                            effect_confirmed = False
                            driver_arguments: dict = {}
                            raw_summary = ""
                            address_mode = "direct"
                            dropped_arguments: list[str] = []
                            error_code = ""
                            structured_error: dict | None = None
                            identity = ""
                            oracle_spec: dict = {}
                            rung_key: tuple = ()
                            unknown_replay_signature_sha256 = ""
                            effect_chain_id = ""
                            authorized_effect_chain_id = ""
                            quota_deferred = False
                            foreground_retry_scheduled = False
                            transient_foreground_evidence: dict = {}
                            copy_selection_evidence: dict = {}
                            cursor_evidence: dict = {}
                            clipboard_evidence: dict = {}
                            effect_absent_immediate = False
                            if descriptor is None:
                                state_call_seen = True
                                summary = f"Unknown driver tool {name!r}; refused."
                                unresolved_action_failure = True
                                evidence["failure_source"] = "progress"
                            elif name.lower() in MODEL_BLOCKED_DRIVER_TOOLS:
                                summary = (
                                    f"{name} bundles actions inside one driver call, outside per-action "
                                    "verification, and was refused. Call each action tool directly."
                                )
                            elif _worker_owned_tool(name):
                                summary = f"{name} is worker-owned observation/session plumbing and was refused."
                            elif state_call_seen:
                                quota_deferred = True
                                arguments, address_mode, dropped_arguments, structured_error = \
                                    _sanitize_action_arguments(
                                        name, arguments, descriptor["inputSchema"], desktop_fallback,
                                    )
                                if structured_error is None:
                                    arguments, _filled_target = _fill_target_from_bound_token(
                                        arguments, address_mode, descriptor["inputSchema"],
                                        elements, window_context,
                                    )
                                identity = _target_identity(arguments, descriptor["inputSchema"])
                                oracle_spec = _bind_oracle_to_ax_target(
                                    _action_oracle_spec(name, arguments, address_mode),
                                    arguments, address_mode, elements,
                                    original_arguments=model_arguments,
                                )
                                if structured_error is None:
                                    rung_key = _action_rung_key(
                                        name, arguments, address_mode, oracle_spec,
                                        window_context, identity,
                                        elements=elements, original_arguments=model_arguments,
                                        state_epoch=verified_state_epoch,
                                    )
                                error_code = "CU_ACTION_QUOTA_DEFERRED"
                                structured_error = _policy_error(
                                    error_code,
                                    "Only one state-changing call is allowed per fresh observation.",
                                    stage="routing", retriable=True,
                                    snapshot_id=window_context.get("snapshot_id", ""),
                                )
                                summary = (
                                    "Action deferred: only one state-changing call is allowed per fresh observation. "
                                    "Wait for the next snapshot before issuing this action."
                                )
                                unresolved_action_failure = True
                                evidence["failure_source"] = "progress"
                            else:
                                state_call_seen = True
                                arguments, address_mode, dropped_arguments, structured_error = \
                                    _sanitize_action_arguments(
                                        name, arguments, descriptor["inputSchema"], desktop_fallback,
                                    )
                                if structured_error is None:
                                    arguments, _filled_target = _fill_target_from_bound_token(
                                        arguments, address_mode, descriptor["inputSchema"],
                                        elements, window_context,
                                    )
                                if structured_error is not None:
                                    verdict = "refuse"
                                    identity = ""
                                    error_code = str(structured_error.get("code", "CU_ADDRESS_MODE_CONFLICT"))
                                    refusal = str(structured_error.get("message", "Unsafe action payload refused."))
                                else:
                                    verdict, identity, refusal = guard_action(
                                        name, arguments, descriptor["inputSchema"], binding.identities,
                                    )
                                entry = _app_entry_for(identity, app_map) if identity else None
                                rebind = False
                                identity_key, _, _identity_value = identity.partition(":")

                                # PID/window identities are opaque: even the first
                                # action of a task must resolve them through a fresh
                                # driver app map before execution. This closes two
                                # otherwise serious first-bind escapes: an unknown
                                # PID and Broccoli's real PID used before a binding
                                # exists. A window_id alone cannot be proven to own
                                # an app from this map, so it is conservatively
                                # refused (normal driver actions include pid).
                                if verdict in {"allow", "resolve"} and identity \
                                        and identity_key in {"pid", "window_id"}:
                                    await refresh_app_map()
                                    entry = _app_entry_for(identity, app_map)
                                    if entry is None:
                                        verdict = "refuse"
                                        refusal = (
                                            f"Target process {identity} could not be resolved from the fresh driver app map."
                                        )
                                if verdict in {"allow", "resolve"} and entry is not None and (
                                        _is_broccoli_text(entry.get("name", ""))
                                        or _is_broccoli_text(entry.get("bundle_id", ""))):
                                    verdict = "refuse"
                                    refusal = "Operating Broccoli itself is forbidden to prevent a feedback loop."

                                if verdict == "resolve":
                                    await refresh_app_map()
                                    same_entry = _same_app(identity, binding.identities, app_map)
                                    if same_entry is not None:
                                        entry = same_entry
                                        verdict = "allow"
                                    else:
                                        entry = _app_entry_for(identity, app_map)
                                        key, _, _value = identity.partition(":")
                                        if entry is not None and (
                                                _is_broccoli_text(entry.get("name", ""))
                                                or _is_broccoli_text(entry.get("bundle_id", ""))):
                                            refusal = "Operating Broccoli itself is forbidden to prevent a feedback loop."
                                        elif key in {"pid", "window_id"} and entry is None:
                                            refusal = f"Target process {identity} could not be resolved from the driver app map."
                                        elif str(name).lower() not in APP_BIND_TOOLS:
                                            refusal = (
                                                f"Switching from {binding.label or 'the current app'} to {identity} requires "
                                                "an explicit background launch_app action followed by a fresh snapshot."
                                            )
                                        else:
                                            verdict = "allow"
                                            rebind = True
                                elif verdict == "allow" and binding.identities and identity not in binding.identities:
                                    rebind = True

                                addressed_from_snapshot = any(
                                    key in arguments for key in (*ELEMENT_ADDRESS_KEYS, *COORDINATE_KEYS)
                                )
                                if verdict == "allow" and window_tool is not None and not window_context \
                                        and str(name).lower() not in APP_SWITCH_TOOLS:
                                    verdict = "refuse"
                                    refusal = (
                                        "No fresh target-window snapshot exists for this action. First use an explicit "
                                        "background launch_app action, then act from the next fresh snapshot."
                                    )
                                # Every window-targeted action must match the
                                # exact fresh snapshot, including actions such
                                # as hotkey/type_text that carry no x/y or
                                # element handle. Otherwise a same-process
                                # second window could receive input grounded in
                                # a different window's observation.
                                if verdict == "allow" and window_context \
                                        and str(name).lower() not in APP_SWITCH_TOOLS:
                                    for target_key in ("pid", "window_id"):
                                        grounded_value = window_context.get(target_key)
                                        supplied_value = arguments.get(target_key)
                                        if grounded_value is None or supplied_value in (None, ""):
                                            continue
                                        try:
                                            matches = int(supplied_value) == int(grounded_value)
                                        except (TypeError, ValueError):
                                            matches = False
                                        if not matches:
                                            verdict = "refuse"
                                            refusal = (
                                                f"Stale grounding refused: {target_key}={supplied_value} does not match "
                                                f"the current fresh snapshot ({grounded_value})."
                                            )
                                            break
                                    if verdict == "allow" and elements and arguments.get("element_token"):
                                        current_tokens = {
                                            str(item.get("element_token")) for item in elements
                                            if item.get("element_token") not in (None, "")
                                        }
                                        if str(arguments.get("element_token")) not in current_tokens:
                                            verdict = "refuse"
                                            refusal = "Stale element_token refused: it is not present in the current fresh snapshot."
                                    if verdict == "allow" and elements and "element_index" in arguments \
                                            and "element_token" not in arguments:
                                        try:
                                            supplied_index = int(arguments.get("element_index"))
                                        except (TypeError, ValueError):
                                            supplied_index = -1
                                        current_indices = set()
                                        for item in elements:
                                            try:
                                                current_indices.add(int(item.get("element_index")))
                                            except (TypeError, ValueError):
                                                continue
                                        if supplied_index not in current_indices:
                                            verdict = "refuse"
                                            refusal = "Stale element_index refused: it is not present in the current fresh snapshot."
                                    if verdict == "allow" and name == "capture_ax_text":
                                        requested_tokens = arguments.get("element_tokens")
                                        requested_tokens = requested_tokens if isinstance(requested_tokens, list) else []
                                        current_tokens = {
                                            str(item.get("element_token")) for item in elements
                                            if isinstance(item, dict) and item.get("element_token") not in (None, "")
                                        }
                                        if not requested_tokens or any(
                                                str(token) not in current_tokens for token in requested_tokens):
                                            verdict = "refuse"
                                            error_code = "CU_AX_TRANSFER_TOKEN_STALE"
                                            refusal = (
                                                "capture_ax_text requires one or more element_tokens from the current fresh snapshot."
                                            )
                                    if verdict == "allow" and name == "insert_captured_text" \
                                            and transfer_buffer.get("insert_verified") is True:
                                        verdict = "refuse"
                                        error_code = "CU_AX_TRANSFER_ALREADY_VERIFIED"
                                        refusal = "The current task-private text buffer was already inserted and read back exactly."
                                    if verdict == "allow" and name == "insert_captured_text" \
                                            and not str(transfer_buffer.get("text", "") or ""):
                                        verdict = "refuse"
                                        error_code = "CU_AX_TRANSFER_BUFFER_EMPTY"
                                        refusal = "No task-private text has been captured or verified-copied for insertion."
                                    if verdict == "allow" and name == "insert_captured_text":
                                        destination_token = str(
                                            arguments.get("element_token", "") or ""
                                        )
                                        destination = next(
                                            (
                                                item for item in elements
                                                if isinstance(item, dict)
                                                and str(item.get("element_token", "") or "")
                                                == destination_token
                                            ),
                                            None,
                                        )
                                        if not _is_writable_ax_element(destination or {}):
                                            verdict = "refuse"
                                            error_code = "CU_AX_TRANSFER_TARGET_NOT_WRITABLE"
                                            refusal = (
                                                "insert_captured_text requires a fresh writable AX text field/area "
                                                "or an element that exposes a set-value action."
                                            )
                                        elif "set_value" not in by_name \
                                                and "type_text" in by_name \
                                                and (
                                                    not isinstance(destination.get("value"), str)
                                                    or destination.get("value") != ""
                                                ):
                                            verdict = "refuse"
                                            error_code = "CU_AX_TRANSFER_TYPE_TEXT_REQUIRES_EMPTY_TARGET"
                                            refusal = (
                                                "Exact private type_text insertion is allowed only when the fresh "
                                                "writable AX destination exposes an exactly empty value; the worker "
                                                "will not guess or append to an existing selection."
                                            )
                                    if verdict == "allow" and _transfer_buffer_pending(transfer_buffer) \
                                            and _is_paste_shortcut(name, arguments):
                                        verdict = "refuse"
                                        error_code = "CU_TRANSFER_BUFFER_REQUIRES_AX_INSERT"
                                        refusal = (
                                            "Cmd+V is disabled while task-private text is pending. Use "
                                            "insert_captured_text on a fresh writable AX destination and verify its "
                                            "exact hash on the next snapshot."
                                        )
                                    if verdict == "allow" and _transfer_buffer_pending(transfer_buffer) \
                                            and _is_copy_shortcut(name, arguments):
                                        verdict = "refuse"
                                        error_code = "CU_TRANSFER_BUFFER_COPY_OVERWRITE_REFUSED"
                                        refusal = (
                                            "A task-private transfer is already pending; another copy would replace "
                                            "its source before verified insertion."
                                        )
                                    if verdict == "allow" and _is_select_all_shortcut(name, arguments):
                                        verdict = "refuse"
                                        error_code = "CU_BLIND_SELECT_ALL_REFUSED"
                                        refusal = (
                                            "Blind Cmd+A selection is disabled. Use fresh AX text capture, or a "
                                            "visible ALIGNED pixel drag followed by the one verified-selection copy grant."
                                        )
                                    if verdict == "allow" and _is_copy_shortcut(name, arguments):
                                        copy_focus_addressed = bool(
                                            any(
                                                _finite_number(model_arguments.get(key)) is not None
                                                for key in COORDINATE_KEYS
                                            )
                                            or str(model_arguments.get("element_token", "") or "").strip()
                                            or model_arguments.get("element_index") is not None
                                        )
                                        if copy_focus_addressed:
                                            # The model may echo the drag endpoint
                                            # into the following Cmd+C.  A focused
                                            # hotkey would click first and destroy
                                            # the verified selection, so narrow this
                                            # one authorized copy to a coordinate-
                                            # free key event and record the rewrite.
                                            for focus_key in (
                                                    *ELEMENT_ADDRESS_KEYS,
                                                    *COORDINATE_KEYS,
                                                    "scope", "from_zoom"):
                                                if focus_key in arguments:
                                                    arguments.pop(focus_key, None)
                                                    if focus_key not in dropped_arguments:
                                                        dropped_arguments.append(focus_key)
                                            address_mode = "key"
                                        copy_authorized = bool(
                                            verdict == "allow"
                                            and copy_selection_grant
                                            and copy_selection_grant.get("consumed") is not True
                                            and copy_selection_grant.get("pid") == window_context.get("pid")
                                            and copy_selection_grant.get("window_id") == window_context.get("window_id")
                                            and str(copy_selection_grant.get("snapshot_id", "") or "")
                                            == str(window_context.get("snapshot_id", "") or "")
                                            and copy_selection_grant.get("geometry_epoch")
                                            == window_context.get("geometry_epoch")
                                            and int(copy_selection_grant.get("state_epoch", -1) or -1)
                                            == int(verified_state_epoch)
                                        )
                                        if verdict == "allow" and not copy_authorized:
                                            verdict = "refuse"
                                            error_code = "CU_CLIPBOARD_COPY_REQUIRES_VERIFIED_SELECTION"
                                            refusal = (
                                                "Cmd+C requires one fresh, confirmed visible pixel-drag selection in "
                                                "this exact window. Prefer capture_ax_text when AX exposes the source."
                                            )
                                        elif verdict == "allow":
                                            # Consume before the key-event call. A timeout may
                                            # have copied; it must never authorize replay.
                                            copy_selection_evidence = copy.deepcopy(copy_selection_grant)
                                            copy_selection_evidence["focus_address_stripped"] = \
                                                copy_focus_addressed
                                            copy_selection_evidence["stripped_fields"] = sorted(
                                                key for key in (
                                                    *ELEMENT_ADDRESS_KEYS, *COORDINATE_KEYS,
                                                    "scope", "from_zoom",
                                                ) if key in model_arguments
                                            )
                                            copy_selection_grant = {}
                                    if verdict == "allow" and copy_selection_grant \
                                            and not _is_copy_shortcut(name, arguments):
                                        # Any intervening state-changing action can
                                        # collapse or replace the visible selection.
                                        copy_selection_grant = {}

                                if verdict == "allow":
                                    display_surface_allowed, display_surface_evidence = \
                                        _explicit_display_ax_only(
                                            name, address_mode, window_context, target_display_policy,
                                        )
                                    if not display_surface_allowed:
                                        error_code = "CU_TARGET_DISPLAY_AX_ONLY"
                                        structured_error = _policy_error(
                                            error_code,
                                            "The target app is outside the explicitly selected display. Only "
                                            "background AX element actions are allowed; key/direct/pixel input will "
                                            "not be redirected to another display.",
                                            stage="display", retriable=True,
                                            **display_surface_evidence,
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])

                                if verdict == "allow" and address_mode == "window_pixel" \
                                        and window_tool is not None:
                                    geometry = window_context.get("geometry") \
                                        if isinstance(window_context.get("geometry"), dict) else {}
                                    classification = str(geometry.get("classification", GEOMETRY_AMBIGUOUS))
                                    if desktop_fallback.get("active"):
                                        error_code = "CU_DESKTOP_SCOPE_REQUIRED"
                                        structured_error = _policy_error(
                                            error_code,
                                            "The current image is a desktop snapshot; retry with scope='desktop'.",
                                            stage="geometry", retriable=True,
                                            snapshot_id=window_context.get("snapshot_id"),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                    elif str(target_display_policy.get("mode", "auto")) == "display" \
                                            and window_context.get("display_policy_match") is not True:
                                        error_code = "CU_TARGET_DISPLAY_PIXEL_OUTSIDE_SELECTED"
                                        structured_error = _policy_error(
                                            error_code,
                                            "The real app window is outside the selected display. Background AX remains "
                                            "available, but window pixels will not be redirected across displays.",
                                            stage="display", retriable=True,
                                            snapshot_id=window_context.get("snapshot_id"),
                                            display_assignment=window_context.get("display_assignment") or {},
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                    elif not geometry.get("pixel_safe"):
                                        error_code = (
                                            "CU_STAGE_HIDDEN_PIXEL_UNAVAILABLE"
                                            if classification in {
                                                GEOMETRY_STAGE_TRANSFORMED, GEOMETRY_OFFSCREEN, GEOMETRY_AMBIGUOUS,
                                            }
                                            else "CU_WINDOW_NOT_PIXEL_ADDRESSABLE"
                                        )
                                        message = (
                                            "This hidden/Stage/off-screen window is not safely pixel-addressable. "
                                            "AX actions remain available, but neither persistent foregrounding nor a "
                                            "desktop thumbnail may be used as a substitute for hidden window content. "
                                            "If the required text is absent from AX, report that boundary; use cursor "
                                            "drag selection only after a fresh ALIGNED visible snapshot exists."
                                        )
                                        structured_error = _policy_error(
                                            error_code, message,
                                            stage="geometry", retriable=False,
                                            classification=classification,
                                            geometry_epoch=window_context.get("geometry_epoch"),
                                            snapshot_id=window_context.get("snapshot_id"),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                    elif int(window_context.get("geometry_stability", 0) or 0) < 2:
                                        error_code = "CU_WINDOW_GEOMETRY_UNSTABLE"
                                        structured_error = _policy_error(
                                            error_code,
                                            "Window pixel input requires two consecutive observations with identical geometry.",
                                            stage="geometry", retriable=True,
                                            geometry_epoch=window_context.get("geometry_epoch"),
                                            snapshot_id=window_context.get("snapshot_id"),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                    elif arguments.get("from_zoom") is True:
                                        error_code = "CU_GEOMETRY_EPOCH_STALE"
                                        structured_error = _policy_error(
                                            error_code,
                                            "from_zoom was refused because the worker cannot prove a zoom image from this snapshot epoch.",
                                            stage="geometry", retriable=True,
                                            geometry_epoch=window_context.get("geometry_epoch"),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])

                                if verdict == "allow" and str(
                                        arguments.get("delivery_mode", "background") or "background"
                                ).lower() == "foreground":
                                    foreground_allowed, transient_foreground_evidence = \
                                        _transient_foreground_authorized(
                                            foreground_grant, name, arguments, address_mode, window_context,
                                            identity=identity, original_arguments=model_arguments,
                                        )
                                    if not foreground_allowed:
                                        error_code = "CU_TRANSIENT_FOREGROUND_NOT_AUTHORIZED"
                                        structured_error = _policy_error(
                                            error_code,
                                            str(transient_foreground_evidence.get(
                                                "reason", "No exact background no-effect action authorizes this retry."
                                            )),
                                            stage="routing", retriable=True,
                                            **{
                                                key: value for key, value in transient_foreground_evidence.items()
                                                if key != "reason"
                                            },
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                    else:
                                        # Consume before any cursor/driver call.  A timeout or
                                        # unknown result must never replay the foreground input.
                                        foreground_grant = {}

                                if verdict == "allow" and address_mode == "desktop_pixel":
                                    refresh_display_topology()
                                    fresh_desktop_id = str(desktop_fallback.get("fresh_snapshot_id", "") or "")
                                    grounded_snapshot_id = str(window_context.get("snapshot_id", "") or "")
                                    if not window_context.get("desktop_snapshot") \
                                            or not fresh_desktop_id \
                                            or grounded_snapshot_id != fresh_desktop_id:
                                        error_code = "CU_DESKTOP_SNAPSHOT_REQUIRED"
                                        structured_error = _policy_error(
                                            error_code,
                                            "Desktop coordinates were not grounded in the current fresh desktop snapshot.",
                                            stage="geometry", retriable=True,
                                            snapshot_id=grounded_snapshot_id,
                                            expected_snapshot_id=fresh_desktop_id,
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])

                                if verdict == "allow" and address_mode in PIXEL_ADDRESS_MODES \
                                        and original_size != (0, 0):
                                    displayed_width = max(1, round(original_size[0] * ratio))
                                    displayed_height = max(1, round(original_size[1] * ratio))
                                    coordinate_pairs = [
                                        (key, arguments.get(key)) for key in COORDINATE_KEYS
                                        if key in arguments
                                    ]
                                    for coordinate_key, coordinate_value in coordinate_pairs:
                                        numeric = _finite_number(coordinate_value)
                                        horizontal = coordinate_key.endswith("x") or coordinate_key == "x"
                                        limit = displayed_width if horizontal else displayed_height
                                        if numeric is None or numeric < 0 or numeric >= limit:
                                            error_code = "CU_COORDINATE_OUT_OF_BOUNDS"
                                            structured_error = _policy_error(
                                                error_code,
                                                f"{coordinate_key}={coordinate_value!r} is outside the current displayed screenshot.",
                                                stage="address", retriable=True,
                                                displayed_size=[displayed_width, displayed_height],
                                                snapshot_id=window_context.get("snapshot_id"),
                                            )
                                            verdict = "refuse"
                                            refusal = str(structured_error["message"])
                                            break

                                if verdict == "allow" and address_mode == "window_pixel":
                                    points_allowed, points_evidence = \
                                        _window_pixel_points_on_selected_display(
                                            scale_coordinates(arguments, ratio),
                                            window_context,
                                            target_display_policy,
                                        )
                                    if not points_allowed:
                                        error_code = "CU_WINDOW_PIXEL_OUTSIDE_SELECTED_DISPLAY"
                                        structured_error = _policy_error(
                                            error_code,
                                            "One or more window-pixel endpoints fall outside the explicitly selected "
                                            "display; the complete action was refused.",
                                            stage="display", retriable=True,
                                            **points_evidence,
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])

                                if verdict == "allow" and address_mode == "desktop_pixel":
                                    scaled_desktop_arguments = scale_coordinates(arguments, ratio)
                                    inside_target, containment = _desktop_coordinate_guard(
                                        scaled_desktop_arguments, window_context,
                                    )
                                    if not inside_target:
                                        error_code = "CU_DESKTOP_COORDINATE_OUTSIDE_TARGET"
                                        structured_error = _policy_error(
                                            error_code,
                                            "Desktop coordinates fall outside the fresh visible-window union "
                                            "owned by the grounded target process.",
                                            stage="address", retriable=True,
                                            **containment,
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])

                                if verdict == "allow":
                                    oracle_spec = _bind_oracle_to_ax_target(
                                        _action_oracle_spec(name, arguments, address_mode),
                                        arguments, address_mode, elements,
                                        original_arguments=model_arguments,
                                    )
                                    if address_mode == "desktop_pixel" and (
                                            str(desktop_fallback.get("grant_tool", "") or "") != str(name or "")
                                            or str(desktop_fallback.get("grant_oracle", "") or "")
                                            != str(oracle_spec.get("kind", "") or "")
                                            or str(desktop_fallback.get("grant_chain_id", "") or "")
                                            != str(active_effect_chain.get("id", "") or "")
                                            or tuple(desktop_fallback.get("grant_operation_semantics") or ())
                                            != _desktop_operation_semantics(name, arguments)):
                                        error_code = "CU_DESKTOP_GRANT_MISMATCH"
                                        structured_error = _policy_error(
                                            error_code,
                                            "The desktop action does not match the exact tool/oracle authorized by the window ladder.",
                                            stage="routing", retriable=False,
                                            authorized_tool=desktop_fallback.get("grant_tool", ""),
                                            authorized_oracle=desktop_fallback.get("grant_oracle", ""),
                                            authorized_effect_chain=desktop_fallback.get("grant_chain_id", ""),
                                            active_effect_chain=active_effect_chain.get("id", ""),
                                            requested_tool=name,
                                            requested_oracle=oracle_spec.get("kind", ""),
                                            authorized_semantics=_json_safe(
                                                desktop_fallback.get("grant_operation_semantics") or ()
                                            ),
                                            requested_semantics=_json_safe(
                                                _desktop_operation_semantics(name, arguments)
                                            ),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                        # A semantic mismatch is not a coordinate
                                        # correction. Consume the one-shot desktop
                                        # grant and return to AX/window-first state.
                                        desktop_fallback.update({
                                            "authorized": False,
                                            "active": False,
                                            "fresh_snapshot_id": "",
                                            "grant_chain_id": "",
                                            "grant_tool": "",
                                            "grant_oracle": "",
                                            "grant_operation_signature": (),
                                            "grant_operation_semantics": (),
                                        })
                                    elif address_mode == "desktop_pixel":
                                        # A desktop coordinate frame changes the
                                        # address, not the logical escalation.
                                        # Preserve only the exact grant's chain.
                                        authorized_effect_chain_id = str(
                                            desktop_fallback.get("grant_chain_id", "") or ""
                                        )
                                    rung_key = _action_rung_key(
                                        name, arguments, address_mode, oracle_spec, window_context, identity,
                                        elements=elements, original_arguments=model_arguments,
                                        state_epoch=verified_state_epoch,
                                    )
                                    candidate_operation_hash = _rung_operation_sha256(rung_key)
                                    replay_signature_arguments = (
                                        scale_coordinates(arguments, ratio)
                                        if address_mode in PIXEL_ADDRESS_MODES else arguments
                                    )
                                    unknown_replay_signature_sha256 = \
                                        _unknown_replay_operation_sha256(
                                            name, replay_signature_arguments, address_mode,
                                            window_context, identity,
                                            elements=elements, original_arguments=model_arguments,
                                        )
                                    if oracle_spec.get("replay_sensitive") is True \
                                            and unknown_replay_signature_sha256 \
                                            and unknown_replay_signature_sha256 \
                                            in unknown_replay_barriers:
                                        error_code = "CU_UNKNOWN_DELIVERY_REPLAY_BLOCKED"
                                        structured_error = _policy_error(
                                            error_code,
                                            "This exact app-input operation has an unresolved prior delivery; "
                                            "replaying it could duplicate a click, key, paste, creation, or write.",
                                            stage="routing", retriable=False,
                                            operation_signature_sha256=candidate_operation_hash,
                                            unknown_replay_signature_sha256=(
                                                unknown_replay_signature_sha256
                                            ),
                                            snapshot_id=window_context.get("snapshot_id"),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                    elif address_mode == "element_ax" and _experience is not None \
                                            and experience_role_bans and _experience.role_banned(
                                                experience_role_bans, binding.label,
                                                str(name).lower(),
                                                str(((oracle_spec.get("target_selector") or {}).get(
                                                    "role", "")) or ""),
                                            ):
                                        error_code = "CU_AX_ACTION_UNSUPPORTED"
                                        structured_error = _policy_error(
                                            error_code,
                                            "An experience rule marks this element role as rejecting AX "
                                            "actions in this app (learned from earlier kAXError evidence). "
                                            "Use the MENU-BAR item for the command, a different element, or "
                                            "type_text/set_value for text.",
                                            stage="routing", retriable=True,
                                            snapshot_id=window_context.get("snapshot_id"),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                    elif address_mode == "element_ax" and _ax_unsupported_memo_key(
                                            name, window_context, oracle_spec,
                                    ) in ax_action_unsupported:
                                        error_code = "CU_AX_ACTION_UNSUPPORTED"
                                        structured_error = _policy_error(
                                            error_code,
                                            "This element already rejected this AX action with a kAXError earlier "
                                            "in the task; repeating it fails identically. Per the driver docs use "
                                            "instead: the app's MENU-BAR item for the command (menu items support "
                                            "AXPress reliably in the background), a DIFFERENT element, "
                                            "type_text/set_value for text entry, or a key press whose background "
                                            "no-effect result unlocks the documented one-shot transient "
                                            "foreground retry.",
                                            stage="routing", retriable=True,
                                            snapshot_id=window_context.get("snapshot_id"),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                    elif weak_absence_retry and rung_key in attempted_rungs \
                                            and rung_key == weak_absence_retry.get("rung"):
                                        # Having seen the screenshot, the model re-sent the identical
                                        # operation: it confirms the coarse no-effect verdict. The
                                        # source's foreground rung runs after the next fresh
                                        # observation; this call itself never reaches the driver.
                                        foreground_grant_source_index = int(weak_absence_retry["source_index"])
                                        weak_absence_retry = {}
                                        foreground_retry_scheduled = True
                                        quota_deferred = True
                                        error_code = "CU_FOREGROUND_RETRY_SCHEDULED"
                                        structured_error = _policy_error(
                                            error_code,
                                            "Confirmed: the worker will deliver this operation once in the "
                                            "transient foreground right after the next fresh observation. Do "
                                            "not send it again; check the result in the next snapshot.",
                                            stage="routing", retriable=False,
                                            rung=list(rung_key),
                                            snapshot_id=window_context.get("snapshot_id"),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])
                                    elif rung_key in attempted_rungs:
                                        error_code = "CU_RUNG_ALREADY_ATTEMPTED"
                                        structured_error = _policy_error(
                                            error_code,
                                            "This exact operation was already attempted in the current state epoch "
                                            "without a confirmed effect. Do NOT resend it unchanged - it will be "
                                            "refused again until the UI state visibly changes. Instead: choose a "
                                            "DIFFERENT element or coordinate, switch to another allowed delivery "
                                            "rung, act on another part of the task, or call finish and report the "
                                            "blocker honestly.",
                                            stage="routing", retriable=True,
                                            rung=list(rung_key),
                                            snapshot_id=window_context.get("snapshot_id"),
                                        )
                                        verdict = "refuse"
                                        refusal = str(structured_error["message"])

                                if verdict == "allow":
                                    allowed = True
                                    # The model moved on to another input; it did not confirm
                                    # the pending coarse no-effect verdict.
                                    weak_absence_retry = {}
                                    prepared = scale_coordinates(arguments, ratio)
                                    if addressed_from_snapshot and window_context:
                                        properties = _schema_properties(descriptor["inputSchema"])
                                        for target_key in ("pid", "window_id"):
                                            if target_key in properties and prepared.get(target_key) in (None, "") \
                                                    and window_context.get(target_key) is not None:
                                                prepared[target_key] = window_context[target_key]
                                    if "element_index" in prepared and "element_token" not in prepared \
                                            and "element_token" in _schema_properties(descriptor["inputSchema"]):
                                        try:
                                            wanted_index = int(prepared["element_index"])
                                        except (TypeError, ValueError):
                                            wanted_index = -1
                                        matched = None
                                        for item in elements:
                                            try:
                                                if int(item.get("element_index")) == wanted_index:
                                                    matched = item
                                                    break
                                            except (TypeError, ValueError):
                                                continue
                                        if matched and matched.get("element_token"):
                                            prepared["element_token"] = str(matched["element_token"])
                                            prepared.pop("element_index", None)
                                    # pid/window_id exist only as a worker-side
                                    # binding assertion for desktop mode.  0.8.3
                                    # requires a windowless screen-absolute payload.
                                    prepared = _driver_payload_for_address_mode(prepared, address_mode)
                                    driver_arguments = _with_driver_session(
                                        prepared, descriptor["inputSchema"], driver_session,
                                    )
                                    clipboard_before: dict = {}
                                    clipboard_original_text = ""
                                    clipboard_probe: dict = {}
                                    clipboard_copy_attempt = False
                                    try:
                                        if address_mode == "element_ax" and name != "capture_ax_text":
                                            cursor_evidence = await position_agent_cursor(
                                                prepared, elements, window_context, binding.label,
                                            )
                                        elif address_mode in PIXEL_ADDRESS_MODES:
                                            cursor_evidence = {
                                                "available": True,
                                                "mode": "driver_pixel_session_overlay",
                                                "real_pointer_moved": False,
                                            }
                                        result: Any = None
                                        if name == "capture_ax_text":
                                            captured_text, captured_meta = _capture_ax_text(
                                                elements, list(arguments.get("element_tokens") or []),
                                            )
                                            transfer_generation += 1
                                            transfer_buffer.clear()
                                            transfer_buffer.update({
                                                "text": captured_text,
                                                "metadata": captured_meta,
                                                "generation": transfer_generation,
                                                "source": {
                                                    "pid": window_context.get("pid"),
                                                    "window_id": window_context.get("window_id"),
                                                    "snapshot_id": window_context.get("snapshot_id", ""),
                                                },
                                                "insert_verified": False,
                                                "destination": {},
                                            })
                                            driver_arguments = {
                                                "pid": window_context.get("pid"),
                                                "window_id": window_context.get("window_id"),
                                                "element_token_count": len(arguments.get("element_tokens") or []),
                                            }
                                            structured_log = _json_safe(captured_meta)
                                            raw_summary = (
                                                f"Captured {captured_meta['char_count']} exact AX character(s) into "
                                                f"the task-private transfer buffer (sha256={captured_meta['sha256']})."
                                            )
                                            oracle_spec = {
                                                "kind": "transfer_capture",
                                                "transfer_generation": transfer_generation,
                                                "transfer_sha256": captured_meta.get("sha256", ""),
                                                "visually_silent": True,
                                                "expects_visual_change": False,
                                            }
                                            executed = True
                                            is_error = False
                                            effect_confirmed = True
                                        elif name == "insert_captured_text":
                                            buffer_text = str(transfer_buffer.get("text", "") or "")
                                            buffer_meta = transfer_buffer.get("metadata") \
                                                if isinstance(transfer_buffer.get("metadata"), dict) else {}
                                            insert_name = "set_value" if "set_value" in by_name else "type_text"
                                            insert_descriptor = by_name.get(insert_name)
                                            if insert_descriptor is None:
                                                raise RuntimeError(
                                                    "CuaDriver exposes neither set_value nor type_text for exact AX insertion."
                                                )
                                            insert_args = {
                                                "pid": int(window_context.get("pid")),
                                                "window_id": int(window_context.get("window_id")),
                                                "element_token": str(arguments.get("element_token", "") or ""),
                                                "value" if insert_name == "set_value" else "text": buffer_text,
                                            }
                                            if insert_name == "type_text":
                                                insert_args["delivery_mode"] = "background"
                                            actual_insert_args = _with_driver_session(
                                                insert_args, insert_descriptor["inputSchema"], driver_session,
                                            )
                                            buffer_sha256 = str(
                                                buffer_meta.get("sha256", "")
                                                or hashlib.sha256(buffer_text.encode("utf-8")).hexdigest()
                                            )
                                            buffer_char_count = int(
                                                buffer_meta.get("char_count", len(buffer_text))
                                                or len(buffer_text)
                                            )
                                            buffer_utf8_bytes = int(
                                                buffer_meta.get(
                                                    "utf8_bytes", len(buffer_text.encode("utf-8"))
                                                ) or len(buffer_text.encode("utf-8"))
                                            )
                                            driver_arguments = {
                                                "driver_tool": insert_name,
                                                "delivery_mode": (
                                                    "background" if insert_name == "type_text" else "ax_value"
                                                ),
                                                "pid": insert_args["pid"],
                                                "window_id": insert_args["window_id"],
                                                "element_token": insert_args["element_token"],
                                                "transfer_buffer": {
                                                    "char_count": buffer_char_count,
                                                    "utf8_bytes": buffer_utf8_bytes,
                                                    "sha256": buffer_sha256,
                                                    "generation": int(
                                                        transfer_buffer.get("generation", 0) or 0
                                                    ),
                                                },
                                            }
                                            oracle_spec = {
                                                "kind": "text_mutation",
                                                "address_mode": "element_ax",
                                                "text_write_semantics": "replace_exact",
                                                "transfer_generation": int(
                                                    transfer_buffer.get("generation", 0) or 0
                                                ),
                                                "transfer_sha256": buffer_sha256,
                                                "expected_text_sha256": buffer_sha256,
                                                "expected_char_count": buffer_char_count,
                                                "expects_visual_change": True,
                                                "visually_silent": False,
                                                "non_idempotent": True,
                                                "replay_sensitive": True,
                                                "private_transfer": True,
                                                "delivery_method": insert_name,
                                            }
                                            oracle_spec = _bind_oracle_to_ax_target(
                                                oracle_spec, arguments, address_mode, elements,
                                                original_arguments=model_arguments,
                                            )
                                            driver_attempted = True
                                            executed = True
                                            try:
                                                result = await _call_tool(
                                                    session, insert_name, actual_insert_args, step_timeout,
                                                )
                                            except asyncio.CancelledError:
                                                raise
                                            except Exception:
                                                # The driver/MCP exception may echo request
                                                # arguments. Replace it before the outer durable
                                                # logging boundary so private text cannot leak.
                                                raise RuntimeError(
                                                    "Private AX text transfer lost its driver reply after dispatch."
                                                ) from None
                                            is_error = _result_is_error(result)
                                            # Some driver builds echo the submitted value in their
                                            # textual response.  The exact transfer payload is kept
                                            # only in task memory, so do not copy any driver response
                                            # text into model context or the durable actions log.
                                            raw_summary = (
                                                f"CuaDriver {insert_name} failed during exact AX transfer."
                                                if is_error else
                                                f"CuaDriver {insert_name} completed exact AX transfer."
                                            )
                                            structured_log = {
                                                "driver_tool": insert_name,
                                                "delivery_mode": driver_arguments["delivery_mode"],
                                                "driver_confirmed": _driver_confirms_effect(result),
                                                "transfer_buffer": copy.deepcopy(
                                                    driver_arguments["transfer_buffer"]
                                                ),
                                                "raw_text_logged": False,
                                            }
                                            content_blocks_log = []
                                            delivery_outcome = (
                                                DELIVERY_DRIVER_ERROR if is_error
                                                else DELIVERY_DELIVERED_UNVERIFIED
                                            )
                                            # Driver-level `verified:true` only proves the AX write
                                            # call returned.  Keep the action pending so the next
                                            # fresh destination tree must expose the exact hash (or
                                            # the model must visibly verify it) before completion.
                                            effect_confirmed = False
                                        else:
                                            if str((oracle_spec or {}).get("kind", "")) == "clipboard_copy":
                                                _emit_progress({
                                                    "step": step,
                                                    "actions": ["clipboard_overwrite_notice"],
                                                    "target": binding.label,
                                                    "mode": "system_clipboard",
                                                    "notice": (
                                                        "About to perform a real copy: the system clipboard may be overwritten; the copied "
                                                        "plain text stays task-private for the AX write and logs "
                                                        "record only before/after hashes and lengths."
                                                    ),
                                                })
                                                clipboard_original_text, clipboard_before = \
                                                    _clipboard_text_snapshot()
                                                if clipboard_before.get("available") is True:
                                                    clipboard_probe = _clipboard_write_text(
                                                        "__BROCCOLI_CU_COPY_PROBE_"
                                                        + uuid.uuid4().hex + "__"
                                                    )
                                                else:
                                                    # An unreadable baseline makes both exact
                                                    # verification and restoration impossible.
                                                    # Do not overwrite it with either a probe or
                                                    # an unverifiable real copy.
                                                    clipboard_evidence = {
                                                        "overwrite_disclosed": True,
                                                        "before": clipboard_before,
                                                        "probe": {
                                                            "available": False,
                                                            "reason": "clipboard_baseline_unavailable",
                                                        },
                                                        "changed": False,
                                                        "absence_proven": False,
                                                        "raw_text_logged": False,
                                                    }
                                                    raise _ClipboardBaselineUnavailable()
                                                clipboard_copy_attempt = True
                                            driver_attempted = True
                                            executed = True
                                            result = await _call_tool(
                                                session, name, driver_arguments, step_timeout,
                                            )
                                            is_error = _result_is_error(result)
                                            delivery_outcome = (
                                                DELIVERY_DRIVER_ERROR if is_error
                                                else DELIVERY_DELIVERED_UNVERIFIED
                                            )
                                            raw_summary = _result_summary(result)
                                            structured_log = _json_safe(_structured_payload(result))
                                            content_blocks_log = _log_content_blocks(result)
                                            effect_confirmed = (
                                                _driver_confirms_effect(result)
                                                # App switching is routing, not a user
                                                # content claim. A successful driver
                                                # return proves that routing call was
                                                # delivered even when an already-front
                                                # window produces identical pixels.
                                                or str((oracle_spec or {}).get("kind", "") or "") == "topology"
                                            )
                                        summary = ("Driver error: " if is_error else "") + raw_summary
                                        if is_error:
                                            if driver_attempted and rung_key:
                                                attempted_rungs.add(rung_key)
                                            failures += 1
                                            unresolved_action_failure = True
                                            evidence["failure_source"] = "driver"
                                            error_code = "CU_DRIVER_ERROR"
                                            structured_error = _policy_error(
                                                error_code, raw_summary or f"{name} returned a driver error.",
                                                stage="delivery", retriable=True,
                                            )
                                            if address_mode == "element_ax" \
                                                    and _AX_ACTION_ERROR_RE.search(raw_summary or ""):
                                                # kAXError (e.g. -25206 ActionUnsupported on
                                                # SwiftUI rows/cells) is deterministic for
                                                # this element; ban identical retries so
                                                # they stop burning the failure breaker.
                                                memo_key = _ax_unsupported_memo_key(
                                                    name, window_context, oracle_spec,
                                                )
                                                if memo_key:
                                                    ax_action_unsupported.add(memo_key)
                                                learned_role = str(
                                                    ((oracle_spec.get("target_selector") or {}).get(
                                                        "role", "")) or ""
                                                ).strip().lower()
                                                if learned_role and binding.label:
                                                    app_slug = re.sub(
                                                        r"[^a-z0-9]+", "-", binding.label.lower(),
                                                    ).strip("-")
                                                    evidence.setdefault(
                                                        "experience_candidates", []
                                                    ).append({
                                                        "fact_key": f"roleban-{app_slug}-{str(name).lower()}-{learned_role}",
                                                        "app": binding.label,
                                                        "name": f"{binding.label} {learned_role} rejects AX actions",
                                                        "steps_nl": (
                                                            f"{binding.label} {learned_role} elements return kAXError "
                                                            f"for {name} AX actions (element-level unsupported)."
                                                        ),
                                                        "rule_nl": "Ban this role's AX form from the start; steer to a different element or the menu bar.",
                                                        "kind": "hook_params",
                                                        "payload": {
                                                            "hook": "role_action_ban",
                                                            "tool": str(name).lower(),
                                                            "role": learned_role,
                                                        },
                                                        "evidence": _clip(raw_summary or "", 200),
                                                    })
                                        else:
                                            failures = 0
                                            unresolved_action_failure = False
                                            evidence["failure_source"] = ""
                                            state_call_succeeded = True
                                            if rung_key:
                                                attempted_rungs.add(rung_key)
                                            if str(name).lower() in APP_BIND_TOOLS:
                                                returned_entry = _app_entry_from_action_result(
                                                    _structured_payload(result), model_arguments,
                                                )
                                                if returned_entry is not None:
                                                    entry = returned_entry
                                            if identity:
                                                if rebind:
                                                    binding.rebind(identity, entry)
                                                    no_effect_streak = 0
                                                else:
                                                    binding.add(identity, entry)
                                                if binding.pid is None:
                                                    try:
                                                        await refresh_app_map()
                                                        refreshed = _app_entry_for(identity, app_map)
                                                        if refreshed is not None:
                                                            binding.add("", refreshed)
                                                    except Exception:
                                                        # The action itself succeeded. A later fresh
                                                        # observation will retry app-map resolution.
                                                        pass
                                                if binding.label and binding.label not in visited_targets:
                                                    visited_targets.append(binding.label)
                                            if str(name).lower() in APP_BIND_TOOLS:
                                                # A background launch/rebind can change
                                                # window topology. It never grants a
                                                # persistent foreground transition.
                                                binding.window_id = None
                                                force_geometry_epoch = True
                                                geometry_stability = 0
                                                last_geometry_signature = ()
                                                desktop_fallback.update({
                                                    "authorized": False,
                                                    "active": False,
                                                    "fresh_snapshot_id": "",
                                                    "target_is_main": (
                                                        _desktop_target_is_main(target_display_policy, {})
                                                        if str(target_display_policy.get("mode", "auto")) == "display"
                                                        else None
                                                    ),
                                                    "last_window": {},
                                                    "desktop_attempted": False,
                                                    "pre_desktop_fingerprint_components": {},
                                                    "grant_chain_id": "",
                                                    "grant_tool": "",
                                                    "grant_oracle": "",
                                                    "grant_operation_signature": (),
                                                    "grant_operation_semantics": (),
                                                })
                                    except asyncio.CancelledError:
                                        raise
                                    except _ClipboardBaselineUnavailable:
                                        is_error = False
                                        executed = False
                                        driver_attempted = False
                                        delivery_outcome = DELIVERY_NOT_ATTEMPTED
                                        unresolved_action_failure = True
                                        evidence["failure_source"] = "progress"
                                        error_code = "CU_CLIPBOARD_BASELINE_UNAVAILABLE"
                                        raw_summary = (
                                            "The system clipboard could not be read, so no private probe or "
                                            "real copy command was sent."
                                        )
                                        summary = raw_summary
                                        structured_error = _policy_error(
                                            error_code, raw_summary,
                                            stage="preparation", retriable=True,
                                        )
                                    except Exception as exc:
                                        is_error = True
                                        unresolved_action_failure = True
                                        raw_summary = _flatten_error(exc)
                                        summary = f"Tool failed: {raw_summary}"
                                        if driver_attempted:
                                            executed = True
                                            delivery_outcome = DELIVERY_UNKNOWN_AFTER_ATTEMPT
                                            if rung_key:
                                                attempted_rungs.add(rung_key)
                                            failures += 1
                                            evidence["failure_source"] = "driver"
                                            error_code = "CU_DRIVER_DELIVERY_UNKNOWN"
                                            structured_error = _policy_error(
                                                error_code, raw_summary,
                                                stage="delivery", retriable=True,
                                            )
                                        else:
                                            executed = False
                                            delivery_outcome = DELIVERY_NOT_ATTEMPTED
                                            evidence["failure_source"] = "progress"
                                            error_code = "CU_ACTION_PREPARATION_FAILED"
                                            structured_error = _policy_error(
                                                error_code, raw_summary,
                                                stage="preparation", retriable=True,
                                            )
                                    finally:
                                        if clipboard_copy_attempt:
                                            await asyncio.sleep(0.12)
                                            changed, absence_proven, clipboard_evidence = \
                                                settle_clipboard_transfer(
                                                    clipboard_original_text,
                                                    clipboard_before,
                                                    clipboard_probe,
                                                    oracle_spec,
                                                    window_context,
                                                    "verified_clipboard_copy",
                                                )
                                            # Clipboard probe readback overrides
                                            # transport acknowledgement.  It also
                                            # settles a lost reply without leaving
                                            # the private sentinel behind.
                                            effect_confirmed = changed
                                            effect_absent_immediate = absence_proven
                                            if changed or absence_proven:
                                                if is_error and failures > 0:
                                                    failures -= 1
                                                is_error = False
                                                unresolved_action_failure = not changed
                                                evidence["failure_source"] = (
                                                    "" if changed else "progress"
                                                )
                                                error_code = ""
                                                structured_error = None
                                                state_call_succeeded = True
                                            progress_notice = (
                                                "The real copy was confirmed via the task-private probe; the text stays "
                                                "task-private (logs keep only hash and length)."
                                                if changed else
                                                "The real copy left the task-private probe unchanged; the prior clipboard text "
                                                "was restored best-effort and no transfer buffer was created."
                                                if absence_proven else
                                                "The clipboard is unreadable; the copy result stays indeterminate."
                                            )
                                            raw_summary = (
                                                "Clipboard probe confirmed a new non-empty private transfer payload."
                                                if changed else
                                                "Clipboard probe proved that the copy produced no new text payload."
                                                if absence_proven else
                                                "Clipboard probe could not determine the copy effect."
                                            )
                                            summary = raw_summary
                                        if address_mode == "desktop_pixel":
                                            # A full-desktop snapshot authorizes
                                            # exactly one delivery attempt.  The
                                            # next turn returns to window/AX-first
                                            # even when delivery was unknown.
                                            desktop_fallback.update({
                                                "authorized": False,
                                                "active": False,
                                                "fresh_snapshot_id": "",
                                                "target_is_main": (
                                                    _desktop_target_is_main(target_display_policy, {})
                                                    if str(target_display_policy.get("mode", "auto")) == "display"
                                                    else None
                                                ),
                                                "last_window": {},
                                                "grant_chain_id": "",
                                                "grant_tool": "",
                                                "grant_oracle": "",
                                                "grant_operation_signature": (),
                                                "grant_operation_semantics": (),
                                            })
                                            evidence["desktop_isolation"]["transition_complete"] = True
                                elif foreground_retry_scheduled:
                                    # The worker owns the next step (the scheduled foreground
                                    # retry), so this is not an unresolved model-side failure.
                                    summary = refusal
                                    unresolved_action_failure = False
                                else:
                                    summary = refusal
                                    unresolved_action_failure = True
                                    evidence["failure_source"] = "progress"

                            if not raw_summary:
                                raw_summary = summary
                            if (not allowed or is_error) and structured_error is None:
                                if not error_code:
                                    error_code = "CU_ACTION_NOT_DELIVERED"
                                structured_error = _policy_error(
                                    error_code, summary,
                                    stage="delivery" if is_error else "guard",
                                    retriable=not is_error,
                                )
                            if not oracle_spec:
                                oracle_spec = _bind_oracle_to_ax_target(
                                    _action_oracle_spec(name, arguments, address_mode),
                                    arguments, address_mode, elements,
                                    original_arguments=model_arguments,
                                )
                            if rung_key and not unknown_replay_signature_sha256:
                                replay_signature_arguments = (
                                    scale_coordinates(arguments, ratio)
                                    if address_mode in PIXEL_ADDRESS_MODES else arguments
                                )
                                unknown_replay_signature_sha256 = \
                                    _unknown_replay_operation_sha256(
                                        name, replay_signature_arguments, address_mode,
                                        window_context, identity,
                                        elements=elements, original_arguments=model_arguments,
                                    )
                            # Only a real, unambiguously delivered action may
                            # establish/update retry lineage. Worker refusals,
                            # quota deferrals, explicit driver errors and
                            # unknown-after-attempt records remain forensic-only
                            # and cannot poison the active effect chain.
                            if driver_attempted \
                                    and delivery_outcome == DELIVERY_DELIVERED_UNVERIFIED:
                                effect_chain_id = authorized_effect_chain_id \
                                    or allocate_effect_chain_id(
                                        name, arguments, address_mode, oracle_spec,
                                        window_context, original_arguments=model_arguments,
                                    )
                            else:
                                effect_chain_id = ""
                            verification_fingerprint_components = fingerprint_components
                            verification_scope = (
                                "desktop" if window_context.get("desktop_snapshot") else "window"
                            )
                            if address_mode == "desktop_pixel":
                                desktop_baseline = desktop_fallback.get(
                                    "pre_desktop_fingerprint_components"
                                )
                                if isinstance(desktop_baseline, dict) and desktop_baseline:
                                    verification_fingerprint_components = desktop_baseline
                                    verification_scope = "window"
                            initial_effect_status = (
                                EFFECT_CONFIRMED if executed and not is_error and effect_confirmed
                                else EFFECT_ABSENT if executed and not is_error and effect_absent_immediate
                                else EFFECT_PENDING if executed and not is_error
                                else EFFECT_INDETERMINATE
                                if executed and delivery_outcome == DELIVERY_UNKNOWN_AFTER_ATTEMPT
                                else EFFECT_NOT_DELIVERED
                            )
                            record_target_pid = binding.pid
                            record_target_label = binding.label
                            if str(name or "").lower() in APP_BIND_TOOLS:
                                record_target_pid = None
                                record_target_label = identity
                                if isinstance(entry, dict):
                                    try:
                                        candidate_pid = int(entry.get("pid") or 0)
                                    except (TypeError, ValueError):
                                        candidate_pid = 0
                                    if candidate_pid > 0:
                                        record_target_pid = candidate_pid
                                    record_target_label = str(
                                        entry.get("name") or entry.get("bundle_id")
                                        or identity
                                    )
                                if delivery_outcome == DELIVERY_DELIVERED_UNVERIFIED \
                                        and binding.pid is not None:
                                    record_target_pid = binding.pid
                                    record_target_label = binding.label or record_target_label
                            action_record = {
                                "step": step,
                                "tool": name,
                                "arguments": _json_safe(arguments),
                                "sanitized_arguments": _json_safe(arguments),
                                "original_arguments": _json_safe(model_arguments),
                                "original_args": _json_safe(model_arguments),
                                "driver_arguments": _json_safe(driver_arguments),
                                "driver_args": _json_safe(driver_arguments),
                                "address_mode": address_mode,
                                "dropped_arguments": list(dropped_arguments),
                                "allowed": allowed,
                                "executed": executed,
                                "driver_attempted": driver_attempted,
                                "delivery_outcome": delivery_outcome,
                                "worker_local": bool(name in SYNTHETIC_TRANSFER_TOOLS and not driver_attempted),
                                "quota_deferred": quota_deferred,
                                "is_error": is_error,
                                "error_code": error_code,
                                "structured_error": _json_safe(structured_error),
                                "result": _clip(summary, 2000),
                                "raw_summary": _clip(raw_summary, 2000),
                                "structured": structured_log,
                                "structured_content": structured_log,
                                "structuredContent": structured_log,
                                "content_blocks": content_blocks_log,
                                "effect_confirmed": effect_confirmed,
                                "effect_status": initial_effect_status,
                                "oracle": _json_safe(oracle_spec),
                                "effect_chain_id": effect_chain_id,
                                "rung_key": _json_safe(list(rung_key) if rung_key else []),
                                "operation_signature_sha256": _rung_operation_sha256(rung_key),
                                "quota_reconciliation_signature_sha256": (
                                    _quota_reconciliation_operation_sha256(
                                        name, arguments, address_mode, oracle_spec,
                                        window_context, identity, elements=elements,
                                        original_arguments=model_arguments,
                                    ) if rung_key else ""
                                ),
                                "unknown_replay_signature_sha256": (
                                    unknown_replay_signature_sha256
                                ),
                                "transient_foreground_authorization": _json_safe(
                                    transient_foreground_evidence
                                ),
                                "copy_selection_authorization": _json_safe(
                                    copy_selection_evidence
                                ),
                                "cursor": _json_safe(cursor_evidence),
                                "clipboard": _json_safe(clipboard_evidence),
                                "session": driver_session,
                                "target_identity": identity,
                                "resolved_target_pid": record_target_pid,
                                "resolved_target_label": record_target_label,
                                "window": _json_safe(window_context),
                                "snapshot_id": window_context.get("snapshot_id", ""),
                                "geometry_epoch": window_context.get("geometry_epoch"),
                                "verified_state_epoch": verified_state_epoch,
                                "geometry": _json_safe(window_context.get("geometry") or {}),
                                "fingerprint": current_fingerprint,
                                "fingerprint_components": _json_safe(fingerprint_components),
                                "verification_fingerprint_components": _json_safe(
                                    verification_fingerprint_components
                                ),
                                "verification_scope": verification_scope,
                            }
                            actions.append(action_record)
                            operation_hash = str(
                                action_record.get("operation_signature_sha256", "") or ""
                            )
                            replay_hash = str(
                                action_record.get("unknown_replay_signature_sha256", "") or ""
                            )
                            if replay_hash and oracle_spec.get("replay_sensitive") is True \
                                    and driver_attempted \
                                    and delivery_outcome == DELIVERY_UNKNOWN_AFTER_ATTEMPT:
                                unknown_replay_barriers[replay_hash] = {
                                    "action_index": len(actions) - 1,
                                    "delivery_outcome": delivery_outcome,
                                }
                                action_record["unknown_replay_barrier"] = {
                                    "active": True,
                                    "unknown_replay_signature_sha256": replay_hash,
                                    "operation_signature_sha256": operation_hash,
                                    "source_step": action_record.get("step"),
                                }
                            delivery_label = str(
                                arguments.get("delivery_mode", "background") or "background"
                            ).lower()
                            if delivery_label == "foreground":
                                progress_mode = "transient foreground retry"
                            elif str(name or "").lower() in {
                                    "hotkey", "shortcut", "press_key", "key", "press_keys",
                            } and address_mode == "element_ax":
                                progress_mode = "background AX focus+key"
                            elif str(name or "").lower() in {
                                    "hotkey", "shortcut", "press_key", "key", "press_keys",
                            } and address_mode == "window_pixel":
                                progress_mode = "background window-pixel focus+key"
                            elif str(name or "").lower() in {
                                    "hotkey", "shortcut", "press_key", "key", "press_keys",
                            }:
                                progress_mode = "background key event"
                            elif address_mode == "element_ax":
                                progress_mode = "background AX"
                            elif address_mode == "window_pixel":
                                progress_mode = "background window pixel"
                            elif address_mode == "desktop_pixel":
                                progress_mode = "main-display desktop fallback"
                            elif address_mode == "topology":
                                progress_mode = "background launch/bind"
                            else:
                                progress_mode = "background input"
                            progress_outcome = initial_effect_status
                            action_index = len(actions) - 1
                            if str(name or "").lower() in APP_BIND_TOOLS \
                                    and delivery_outcome == DELIVERY_UNKNOWN_AFTER_ATTEMPT \
                                    and identity:
                                unknown_launch_binding = {
                                    "identity": identity,
                                    "action_index": action_index,
                                    "attempts": 0,
                                }
                            insert_driver_meta = action_record.get("driver_arguments") \
                                if isinstance(action_record.get("driver_arguments"), dict) else {}
                            if str(name or "") == "insert_captured_text" \
                                    and str(insert_driver_meta.get("driver_tool", "") or "") \
                                    == "set_value" \
                                    and delivery_outcome == DELIVERY_DRIVER_ERROR:
                                # An explicit set_value rejection authorizes
                                # only a fresh read-only settlement on the next
                                # loop. It never calls type_text in this snapshot.
                                insert_fallback_source_index = action_index
                                effect_calls_since_confirmation += 1
                            if initial_effect_status == EFFECT_CONFIRMED:
                                no_effect_streak = 0
                                no_effect_counts.clear()
                                effect_calls_since_confirmation = 0
                                verified_state_epoch += 1
                                desktop_fallback["desktop_attempted"] = False
                                _reconcile_confirmed_retry(actions, action_index)
                                _reconcile_unknown_launch_routing(actions, action_index)
                                retire_effect_chain(action_record)
                            elif initial_effect_status == EFFECT_ABSENT:
                                action_record["error_code"] = "CU_CLIPBOARD_UNCHANGED"
                                action_record["structured_error"] = _policy_error(
                                    "CU_CLIPBOARD_UNCHANGED",
                                    "The real copy command did not produce a new non-empty text clipboard fingerprint.",
                                    stage="verification", retriable=True,
                                )
                                # Clipboard fingerprint readback is already an
                                # exact postcondition: no new window screenshot
                                # is needed to prove that this delivered
                                # background copy had no effect.  Authorize the
                                # same one-shot transient foreground rung now;
                                # it will still be revalidated against the next
                                # fresh window observation before dispatch.
                                foreground_grant_source_index = action_index
                                unresolved_action_failure = True
                                effect_calls_since_confirmation += 1
                            elif initial_effect_status == EFFECT_PENDING:
                                pending_action_index = action_index
                                effect_calls_since_confirmation += 1
                            elif initial_effect_status == EFFECT_INDETERMINATE \
                                    and delivery_outcome == DELIVERY_UNKNOWN_AFTER_ATTEMPT:
                                # The driver may have executed before transport
                                # failed. Give the next fresh observation one
                                # chance to settle the effect; an indeterminate
                                # result keeps the exact replay barrier active.
                                pending_action_index = action_index
                                effect_calls_since_confirmation += 1
                            step_actions.append(name + ("" if allowed and not is_error else " (failed/refused)"))
                            tool_records.append({"role": "tool", "tool_call_id": str(call.id), "content": summary})

                        recent.append([assistant_record, *tool_records])
                        _emit_progress({
                            "step": step,
                            "actions": step_actions,
                            "target": binding.label,
                            "mode": progress_mode,
                            "outcome": progress_outcome,
                            "notice": progress_notice,
                        })
                        if failures >= max_failures:
                            evidence["failure_source"] = "driver"
                            raise _FatalTaskError(
                                f"Computer Use stopped after {failures} consecutive driver tool failures."
                            )
                        # A successful action still cannot authorize finish until
                        # the next loop has produced a fresh observation.
                        if state_call_succeeded:
                            continue
                    except asyncio.CancelledError:
                        raise
                    except _FatalTaskError:
                        raise
                    except Exception as exc:
                        failures += 1
                        if failures >= max_failures:
                            raise
                        _emit_progress({
                            "step": step,
                            "actions": ["step_failed"],
                            "target": binding.label,
                            "mode": "worker_exception",
                            "outcome": "NOT_DELIVERED",
                            "notice": _clip(_flatten_error(exc), 500),
                        })
                evidence["failure_source"] = "budget"
                return {
                    "ok": False,
                    "error": "Computer Use reached its maximum step count.",
                    "answer": _last_narrative(evidence),
                    "metadata": _salvage_metadata(config, evidence, partial=True),
                }
            finally:
                if not _cancelled(config):
                    try:
                        await restore_expanded_front()
                    except BaseException:
                        pass
                if stage_manager_was_on:
                    try:
                        _set_stage_manager(True)
                    except Exception:
                        pass
                if "end_session" in by_name and (session_started or evidence.get("driver_session")):
                    try:
                        descriptor = by_name["end_session"]
                        end_args = _with_driver_session({}, descriptor["inputSchema"], driver_session)
                        await _call_tool(session, "end_session", end_args, min(step_timeout, 3))
                    except BaseException:
                        pass


async def _watch_cancel(config: dict) -> None:
    while not _cancelled(config):
        await asyncio.sleep(1.0)


async def _cancel_and_collect_run(run_task: asyncio.Task) -> None:
    """Cancel the live run and wait for its daemon/session cleanup.

    Result metadata and the durable actions log must be created *after* this
    returns; otherwise cancellation can report success before the private
    CuaDriver PID/socket/HOME have actually been accounted for.  A cleanup
    verdict intentionally overrides the ordinary ``CancelledError``.
    """
    if not run_task.done():
        run_task.cancel()
    outcome = (await asyncio.gather(run_task, return_exceptions=True))[0]
    if isinstance(outcome, BaseException) and not isinstance(outcome, asyncio.CancelledError):
        raise outcome


async def _main(config: dict, evidence: dict) -> dict:
    timeout = _positive_int(config.get("overall_timeout"), 600)
    run_task = asyncio.ensure_future(_run(config, evidence))
    cancel_task = asyncio.ensure_future(_watch_cancel(config))
    try:
        done, _pending = await asyncio.wait(
            {run_task, cancel_task}, timeout=timeout, return_when=asyncio.FIRST_COMPLETED,
        )
        if run_task in done:
            return run_task.result()
        if cancel_task in done:
            await _cancel_and_collect_run(run_task)
            return _cancelled_result(config, evidence)
        # Wording matters: "time limit" (not "timeout"/"timed out") keeps the
        # parent's model-failover classifier from mistaking task-budget
        # exhaustion for model unavailability and restarting the desktop task.
        await _cancel_and_collect_run(run_task)
        evidence["failure_source"] = "budget"
        return {
            "ok": False,
            "error": "Computer Use reached its overall time limit.",
            "answer": _last_narrative(evidence),
            "metadata": _salvage_metadata(config, evidence, partial=True),
        }
    finally:
        for task in (run_task, cancel_task):
            task.cancel()
        # Await the cancellations so the MCP stdio session closes and its child
        # process is terminated before the worker exits (no orphan drivers).
        await asyncio.gather(run_task, cancel_task, return_exceptions=True)


def main() -> int:
    evidence = _new_evidence()
    config: dict = {}
    try:
        config = json.loads(sys.stdin.read() or "{}")
        if _cancelled(config):
            _emit_result({"cancelled": True, "answer": "Computer Use task was stopped before it started."})
            return 0
        result = asyncio.run(_main(config, evidence))
        _emit_result(result)
        return 0
    except Exception as exc:
        if not evidence.get("failure_source"):
            evidence["failure_source"] = "worker"
        _emit_result({
            "ok": False,
            "error": _flatten_error(exc),
            "answer": _last_narrative(evidence),
            "metadata": _salvage_metadata(config if isinstance(config, dict) else {}, evidence, partial=True),
        })
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
