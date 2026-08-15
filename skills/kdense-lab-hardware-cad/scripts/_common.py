"""Shared helpers for the lab-hardware-cad scripts.

Import of build123d is deferred so that standard-library-only commands
(``check.py standards``) work in an environment without the CAD kernel.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from pathlib import Path
from typing import Any

SKILL_ROOT = Path(__file__).resolve().parent.parent
STANDARDS_PATH = SKILL_ROOT / "assets" / "standards.json"

MESH_FORMATS = {".stl"}
BREP_FORMATS = {".step", ".stp"}


class LabCadError(RuntimeError):
    """A user-facing error: printed without a traceback."""


def eprint(message: str) -> None:
    """Progress and diagnostics go to stderr so stdout stays machine-readable."""
    print(message, file=sys.stderr)


def emit(payload: Any, as_json: bool, text: str | None = None) -> None:
    """Write a result to stdout as JSON or as human-readable text."""
    if as_json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print(text if text is not None else payload)


def load_standards() -> dict:
    """Load the bundled standards database. Standard library only."""
    if not STANDARDS_PATH.exists():
        raise LabCadError(f"standards database missing at {STANDARDS_PATH}")
    with STANDARDS_PATH.open(encoding="utf-8") as handle:
        return json.load(handle)


def get_standard(standard_id: str) -> dict:
    data = load_standards()
    standards = data.get("standards", {})
    if standard_id not in standards:
        known = ", ".join(sorted(standards))
        raise LabCadError(f"unknown standard {standard_id!r}. Available: {known}")
    return standards[standard_id]


def require_build123d():
    """Import build123d, or fail with an actionable message."""
    try:
        import build123d  # noqa: PLC0415
    except ImportError as exc:  # pragma: no cover - environment dependent
        raise LabCadError(
            "build123d is not installed in this interpreter.\n"
            "  uv venv --python 3.12 .venv-labcad\n"
            '  uv pip install --python .venv-labcad/bin/python "build123d==0.11.1" "matplotlib>=3.8"'
        ) from exc
    return build123d


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _coerce(value: str) -> Any:
    """Parse a --param value into the narrowest sensible Python type."""
    lowered = value.strip().lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    for caster in (int, float):
        try:
            return caster(value)
        except ValueError:
            continue
    return value


def parse_params(pairs: list[str] | None) -> dict[str, Any]:
    """Turn ``["bore_d_mm=6.1", "wall_t_mm=3"]`` into a dict."""
    params: dict[str, Any] = {}
    for pair in pairs or []:
        if "=" not in pair:
            raise LabCadError(f"--param expects key=value, got {pair!r}")
        key, _, raw = pair.partition("=")
        params[key.strip()] = _coerce(raw)
    return params


def model_parameters(module) -> dict[str, Any]:
    """Collect a model module's public scalar parameters for the manifest."""
    return {
        name: value
        for name, value in vars(module).items()
        if not name.startswith("_") and isinstance(value, (int, float, str, bool))
    }


def import_model(model_path: Path, overrides: dict[str, Any] | None = None):
    """Import a ``*_model.py`` file and apply ``--param`` overrides.

    Returns the module without calling ``build()``, so declared interfaces can be
    read without paying for the geometry.
    """
    model_path = model_path.resolve()
    if not model_path.exists():
        raise LabCadError(f"model file not found: {model_path}")

    spec = importlib.util.spec_from_file_location(model_path.stem, model_path)
    if spec is None or spec.loader is None:
        raise LabCadError(f"cannot import {model_path}")
    module = importlib.util.module_from_spec(spec)
    # Let the model resolve sibling imports.
    sys.path.insert(0, str(model_path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)

    for key, value in (overrides or {}).items():
        if not hasattr(module, key):
            known = ", ".join(sorted(model_parameters(module)))
            raise LabCadError(
                f"model has no parameter {key!r}. Available: {known}"
            )
        setattr(module, key, value)
    return module


def run_model(model_path: Path, overrides: dict[str, Any] | None = None):
    """Import a ``*_model.py`` file, apply overrides, and call ``build()``.

    Returns ``(part, resolved_parameters)``.
    """
    module = import_model(model_path, overrides)

    builder = getattr(module, "build", None)
    if builder is None or not callable(builder):
        raise LabCadError(
            f"{Path(model_path).name} must define a callable build() that returns a Part"
        )

    part = builder()
    if part is None:
        raise LabCadError(f"{Path(model_path).name}: build() returned None")
    return part, model_parameters(module)


def model_interfaces(module) -> list[dict]:
    """Collect the interface checks a model declares about itself.

    A model exposes either a module-level ``INTERFACES`` list or an
    ``interfaces()`` callable returning one. Each entry names the standard and
    dimension the feature must satisfy and the value the model computed:

        INTERFACES = [
            {"feature": "plate pocket length",
             "standard": "slas-microplate-footprint",
             "dimension": "footprint_length",
             "value": pocket_l_mm,
             "intent": "envelope",
             "clearance": 0.80},
        ]

    This exists because most lab-hardware interfaces are internal features -- a
    pocket, a bore, a slot -- whose size is nowhere in the part's outer bounding
    box. Declaring them lets ``check.py interfaces`` verify the number the model
    actually built instead of one retyped by hand.
    """
    declared = getattr(module, "interfaces", None)
    if callable(declared):
        declared = declared()
    elif declared is None:
        declared = getattr(module, "INTERFACES", None)
    if declared is None:
        return []
    return normalise_interfaces(declared)


def normalise_interfaces(declared: Any) -> list[dict]:
    """Validate and fill in defaults for declared interface entries."""
    if isinstance(declared, dict):
        declared = [declared]
    if not isinstance(declared, (list, tuple)):
        raise LabCadError("INTERFACES must be a list of dicts")

    entries: list[dict] = []
    for index, raw in enumerate(declared):
        if not isinstance(raw, dict):
            raise LabCadError(f"INTERFACES[{index}] must be a dict, got {type(raw).__name__}")
        missing = [key for key in ("standard", "dimension", "value") if key not in raw]
        if missing:
            raise LabCadError(
                f"INTERFACES[{index}] is missing {', '.join(missing)}. Every entry needs "
                "standard, dimension, and value."
            )
        try:
            value = float(raw["value"])
        except (TypeError, ValueError) as exc:
            raise LabCadError(
                f"INTERFACES[{index}] value {raw['value']!r} is not a number"
            ) from exc
        intent = str(raw.get("intent", "match"))
        if intent not in {"match", "envelope"}:
            raise LabCadError(
                f"INTERFACES[{index}] intent must be 'match' or 'envelope', got {intent!r}"
            )
        entries.append({
            "feature": str(raw.get("feature", raw["dimension"])),
            "standard": str(raw["standard"]),
            "dimension": str(raw["dimension"]),
            "value": value,
            "intent": intent,
            "clearance": float(raw.get("clearance", 0.0)),
        })
    return entries


def load_shape(path: Path):
    """Load a STEP or STL file, or build a model, into a build123d shape."""
    path = Path(path)
    if not path.exists():
        raise LabCadError(f"file not found: {path}")

    suffix = path.suffix.lower()
    if suffix == ".py":
        part, _ = run_model(path)
        return part

    build123d = require_build123d()
    if suffix in BREP_FORMATS:
        return build123d.import_step(str(path))
    if suffix in MESH_FORMATS:
        eprint(
            f"warning: {path.name} is a mesh. Volume and validity are approximate, "
            "and STEP is the authoritative format. Prefer inspecting the STEP."
        )
        return build123d.import_stl(str(path))
    raise LabCadError(
        f"unsupported input {suffix!r}. Expected .step, .stp, .stl, or a *_model.py file."
    )


def _is_valid(shape) -> bool:
    """``Shape.is_valid`` is a property in build123d 0.11.x; older builds expose a method."""
    value = shape.is_valid
    return bool(value() if callable(value) else value)


def shape_facts(shape) -> dict:
    """Deterministic geometric facts about a shape, in millimetres."""
    build123d = require_build123d()
    bbox = shape.bounding_box()

    try:
        centre = shape.center(build123d.CenterOf.MASS)
        centre_of = "mass"
    except (ValueError, NotImplementedError):
        centre = bbox.center()
        centre_of = "bounding_box"

    try:
        solids = len(shape.solids())
    except (AttributeError, TypeError):
        solids = None

    return {
        "is_valid": _is_valid(shape),
        "bounding_box_mm": {
            "x": round(bbox.size.X, 4),
            "y": round(bbox.size.Y, 4),
            "z": round(bbox.size.Z, 4),
            "min": [round(bbox.min.X, 4), round(bbox.min.Y, 4), round(bbox.min.Z, 4)],
            "max": [round(bbox.max.X, 4), round(bbox.max.Y, 4), round(bbox.max.Z, 4)],
        },
        "volume_mm3": round(float(shape.volume), 4),
        "area_mm2": round(float(shape.area), 4),
        "center_mm": [round(centre.X, 4), round(centre.Y, 4), round(centre.Z, 4)],
        "center_of": centre_of,
        "solid_count": solids,
    }


def measure(facts: dict, name: str, swap_xy: bool = False) -> float:
    """Resolve a fit-check measure name against a facts dict."""
    box = facts["bounding_box_mm"]
    x, y = (box["y"], box["x"]) if swap_xy else (box["x"], box["y"])
    extents = sorted((x, y, box["z"]))
    table = {
        "bbox_x": x,
        "bbox_y": y,
        "bbox_z": box["z"],
        "bbox_min": extents[0],
        "bbox_mid": extents[1],
        "bbox_max": extents[2],
    }
    if name not in table:
        raise LabCadError(
            f"unknown measure {name!r}. Expected one of: {', '.join(sorted(table))}"
        )
    return table[name]


def main_guard(func) -> None:
    """Run a CLI entry point, converting LabCadError into a clean exit."""
    try:
        sys.exit(func())
    except LabCadError as exc:
        eprint(f"error: {exc}")
        sys.exit(2)
    except KeyboardInterrupt:  # pragma: no cover
        eprint("interrupted")
        sys.exit(130)
