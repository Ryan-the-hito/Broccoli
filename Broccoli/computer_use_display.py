#!/usr/bin/env python3
"""Display discovery and geometry helpers for Broccoli Computer Use.

The module intentionally has no Qt dependency.  The main process can use it
from GUI or planner threads, and the standalone worker can reuse the pure
geometry helpers without constructing a QApplication.  CoreGraphics is loaded
lazily; non-macOS hosts and minimal test environments safely report no physical
displays instead of failing import-time.
"""

from __future__ import annotations

import hashlib
import json
import math
import sys
from typing import Any, Iterable


TARGET_DISPLAY_AUTO = "auto"
TARGET_DISPLAY_EXPLICIT = "display"


def default_target_display() -> dict:
    return {"mode": TARGET_DISPLAY_AUTO}


def _finite_number(value: Any) -> float | None:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


def _json_number(value: float) -> int | float:
    rounded = round(value)
    return int(rounded) if abs(value - rounded) < 1e-9 else float(value)


def normalize_bounds(value: Any) -> dict | None:
    """Return a JSON-safe x/y/width/height rectangle or ``None``.

    Both ``width``/``height`` and CoreGraphics-style ``w``/``h`` inputs are
    accepted.  Negative origins are valid for displays arranged left/above the
    main display; non-positive extents are not.
    """

    if not isinstance(value, dict):
        return None
    x = _finite_number(value.get("x"))
    y = _finite_number(value.get("y"))
    width = _finite_number(value.get("width", value.get("w")))
    height = _finite_number(value.get("height", value.get("h")))
    if x is None or y is None or width is None or height is None:
        return None
    if width <= 0 or height <= 0:
        return None
    return {
        "x": _json_number(x),
        "y": _json_number(y),
        "width": _json_number(width),
        "height": _json_number(height),
    }


def bounds_intersection_area(first: Any, second: Any) -> float:
    a = normalize_bounds(first)
    b = normalize_bounds(second)
    if a is None or b is None:
        return 0.0
    left = max(float(a["x"]), float(b["x"]))
    top = max(float(a["y"]), float(b["y"]))
    right = min(float(a["x"]) + float(a["width"]), float(b["x"]) + float(b["width"]))
    bottom = min(float(a["y"]) + float(a["height"]), float(b["y"]) + float(b["height"]))
    return max(0.0, right - left) * max(0.0, bottom - top)


def bounds_contains_point(bounds: Any, x: Any, y: Any) -> bool:
    rect = normalize_bounds(bounds)
    px = _finite_number(x)
    py = _finite_number(y)
    if rect is None or px is None or py is None:
        return False
    return (
        float(rect["x"]) <= px < float(rect["x"]) + float(rect["width"])
        and float(rect["y"]) <= py < float(rect["y"]) + float(rect["height"])
    )


def display_stable_id(
    vendor_id: Any,
    model_id: Any,
    serial_number: Any,
    unit_number: Any,
    is_builtin: Any,
) -> str:
    """Build a layout-independent physical-display key from CG metadata."""

    def integer(value: Any) -> int:
        try:
            return max(0, int(value))
        except (TypeError, ValueError):
            return 0

    return "cg:{:08x}:{:08x}:{:08x}:{:04x}:{}".format(
        integer(vendor_id),
        integer(model_id),
        integer(serial_number),
        integer(unit_number),
        1 if bool(is_builtin) else 0,
    )


def normalize_target_display(value: Any) -> dict:
    """Normalize the persisted Computer Use target-display setting.

    The current object shape is accepted alongside the early string prototype
    so an older ``"auto"`` or stable-id value can be read without data loss.
    Runtime-only fields such as a CGDirectDisplayID are deliberately discarded.
    """

    if value in (None, "", TARGET_DISPLAY_AUTO):
        return default_target_display()
    if isinstance(value, str):
        stable_id = value.strip()
        return (
            {"mode": TARGET_DISPLAY_EXPLICIT, "stable_id": stable_id}
            if stable_id and stable_id != TARGET_DISPLAY_AUTO
            else default_target_display()
        )
    if not isinstance(value, dict):
        return default_target_display()
    mode = str(value.get("mode", "") or "").strip().lower()
    stable_id = str(value.get("stable_id", value.get("id", "")) or "").strip()
    if mode in ("", TARGET_DISPLAY_AUTO) and not stable_id:
        return default_target_display()
    if stable_id == TARGET_DISPLAY_AUTO:
        return default_target_display()
    if mode in (TARGET_DISPLAY_EXPLICIT, "explicit", "screen") and not stable_id:
        # Preserve explicit intent so the runtime resolver can fail closed. A
        # malformed saved explicit choice must never silently become auto.
        normalized = {"mode": TARGET_DISPLAY_EXPLICIT, "stable_id": ""}
        label_hint = str(value.get("label_hint", value.get("label", "")) or "").strip()
        if label_hint:
            normalized["label_hint"] = label_hint[:200]
        return normalized
    if mode not in (TARGET_DISPLAY_EXPLICIT, "explicit", "screen") or not stable_id:
        return default_target_display()
    normalized = {"mode": TARGET_DISPLAY_EXPLICIT, "stable_id": stable_id}
    label_hint = str(value.get("label_hint", value.get("label", "")) or "").strip()
    if label_hint:
        normalized["label_hint"] = label_hint[:200]
    geometry = normalize_bounds(value.get("last_geometry", value.get("bounds")))
    if geometry is not None:
        normalized["last_geometry"] = geometry
    return normalized


def _cg_rect_dict(rect: Any) -> dict | None:
    try:
        return normalize_bounds({
            "x": rect.origin.x,
            "y": rect.origin.y,
            "width": rect.size.width,
            "height": rect.size.height,
        })
    except Exception:
        return None


def enumerate_displays() -> list[dict]:
    """Enumerate active macOS displays; return ``[]`` everywhere else.

    ``runtime_id`` is useful only inside the current login session.  Persist
    ``stable_id`` instead.  A failure to import/call CoreGraphics is a normal
    capability absence, not an application-startup error.
    """

    if sys.platform != "darwin":
        return []
    try:
        import Quartz  # type: ignore

        error, display_ids, count = Quartz.CGGetActiveDisplayList(64, None, None)
        if int(error) != 0:
            return []
        descriptors: list[dict] = []
        for display_id in tuple(display_ids or ())[: int(count or 0)]:
            runtime_id = int(display_id)
            bounds = _cg_rect_dict(Quartz.CGDisplayBounds(runtime_id))
            if bounds is None:
                continue
            vendor_id = int(Quartz.CGDisplayVendorNumber(runtime_id))
            model_id = int(Quartz.CGDisplayModelNumber(runtime_id))
            serial_number = int(Quartz.CGDisplaySerialNumber(runtime_id))
            unit_number = int(Quartz.CGDisplayUnitNumber(runtime_id))
            is_builtin = bool(Quartz.CGDisplayIsBuiltin(runtime_id))
            pixel_width = int(Quartz.CGDisplayPixelsWide(runtime_id))
            pixel_height = int(Quartz.CGDisplayPixelsHigh(runtime_id))
            logical_width = float(bounds["width"])
            scale_factor = (float(pixel_width) / logical_width) if logical_width > 0 else 1.0
            descriptors.append({
                "stable_id": display_stable_id(
                    vendor_id, model_id, serial_number, unit_number, is_builtin,
                ),
                "runtime_id": runtime_id,
                "bounds": bounds,
                "is_main": bool(Quartz.CGDisplayIsMain(runtime_id)),
                "is_builtin": is_builtin,
                "vendor_id": vendor_id,
                "model_id": model_id,
                "serial_number": serial_number,
                "unit_number": unit_number,
                "pixel_width": pixel_width,
                "pixel_height": pixel_height,
                "scale_factor": scale_factor,
                "label": "Built-in Display" if is_builtin else f"Display {unit_number or runtime_id}",
            })
        descriptors.sort(key=lambda item: (
            not bool(item.get("is_main")),
            float((item.get("bounds") or {}).get("y", 0)),
            float((item.get("bounds") or {}).get("x", 0)),
            str(item.get("stable_id", "")),
        ))
        return descriptors
    except Exception:
        return []


def display_topology_signature(displays: Iterable[dict]) -> str:
    cells = []
    for item in displays or []:
        if not isinstance(item, dict):
            continue
        stable_id = str(item.get("stable_id", "") or "").strip()
        bounds = normalize_bounds(item.get("bounds"))
        if stable_id and bounds is not None:
            cells.append({
                "stable_id": stable_id,
                "bounds": bounds,
                "is_main": bool(item.get("is_main")),
            })
    cells.sort(key=lambda item: item["stable_id"])
    encoded = json.dumps(cells, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def resolve_target_display(value: Any, displays: Iterable[dict] | None = None) -> dict | None:
    """Resolve a persisted setting to an immutable per-task descriptor.

    ``auto`` always resolves.  An explicit id resolves only when exactly one
    active display matches; zero or duplicate matches fail closed.
    """

    setting = normalize_target_display(value)
    if setting["mode"] == TARGET_DISPLAY_AUTO:
        return default_target_display()
    current = list(enumerate_displays() if displays is None else displays)
    wanted = str(setting.get("stable_id", "") or "")
    matches = [item for item in current if str(item.get("stable_id", "") or "") == wanted]
    if len(matches) != 1:
        return None
    source = matches[0]
    bounds = normalize_bounds(source.get("bounds"))
    if bounds is None:
        return None
    label = str(setting.get("label_hint", "") or source.get("label", "") or wanted).strip()
    return {
        "mode": TARGET_DISPLAY_EXPLICIT,
        "stable_id": wanted,
        "label": label[:200],
        "bounds": bounds,
        "scale_factor": float(source.get("scale_factor", 1.0) or 1.0),
        "is_main": bool(source.get("is_main")),
        "topology_signature": display_topology_signature(current),
    }


__all__ = [
    "TARGET_DISPLAY_AUTO",
    "TARGET_DISPLAY_EXPLICIT",
    "bounds_contains_point",
    "bounds_intersection_area",
    "default_target_display",
    "display_stable_id",
    "display_topology_signature",
    "enumerate_displays",
    "normalize_bounds",
    "normalize_target_display",
    "resolve_target_display",
]
