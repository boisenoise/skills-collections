#!/usr/bin/env python3
"""Deterministic checks on lab-hardware geometry.

    python scripts/check.py standards --list
    python scripts/check.py standards --show slas-microplate-footprint
    python scripts/check.py facts out/carrier.step
    python scripts/check.py interfaces out/carrier.manifest.json
    python scripts/check.py fit --standard slas-microplate-footprint \
        --intent envelope --clearance 0.8 --value footprint_length=128.81
    python scripts/check.py clearance out/carrier.step out/lid.step --min 0.3

``standards`` and ``interfaces`` on a manifest run on the standard library alone. The
other subcommands need build123d. Checking subcommands exit non-zero on failure so they
can gate a build.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    LabCadError,
    emit,
    eprint,
    get_standard,
    import_model,
    load_shape,
    load_standards,
    main_guard,
    measure,
    model_interfaces,
    normalise_interfaces,
    shape_facts,
)


def cmd_standards(args) -> int:
    data = load_standards()
    standards = data["standards"]

    if args.show:
        entry = get_standard(args.show)
        lines = [
            f"{args.show}: {entry['title']}",
            f"  authority: {entry['authority']}",
            f"  document:  {entry['document']}",
            f"  url:       {entry.get('url', '-')}",
            f"  verified:  {entry.get('verified')}",
            "  dimensions (mm):",
        ]
        for name, dim in entry["dimensions"].items():
            band = f"+{dim.get('tol_plus', 0)}/-{dim.get('tol_minus', 0)}"
            lines.append(f"    {name}: {dim['nominal']} {band}")
            if dim.get("note"):
                lines.append(f"      note: {dim['note']}")
        if entry.get("design_note"):
            lines.append(f"  design note: {entry['design_note']}")
        if not entry.get("verified", False):
            lines.append("  WARNING: this entry is not verified against the primary document.")
        emit(entry, args.as_json, "\n".join(lines))
        return 0

    listing = [
        {
            "id": key,
            "title": value["title"],
            "document": value["document"],
            "verified": value.get("verified", False),
        }
        for key, value in sorted(standards.items())
    ]
    text = "\n".join(
        f"{item['id']:<32} {'ok ' if item['verified'] else 'UNVERIFIED'}  {item['title']}"
        for item in listing
    )
    emit(listing, args.as_json, text)
    return 0


def cmd_facts(args) -> int:
    shape = load_shape(args.target)
    facts = shape_facts(shape)
    box = facts["bounding_box_mm"]
    text = "\n".join([
        f"target:      {args.target}",
        f"is_valid:    {facts['is_valid']}",
        f"bbox (mm):   {box['x']:.4f} x {box['y']:.4f} x {box['z']:.4f}",
        f"bbox min:    {box['min']}",
        f"bbox max:    {box['max']}",
        f"volume:      {facts['volume_mm3']:.4f} mm^3",
        f"area:        {facts['area_mm2']:.4f} mm^2",
        f"centre ({facts['center_of']}): {facts['center_mm']}",
        f"solids:      {facts['solid_count']}",
    ])
    emit(facts, args.as_json, text)
    return 0 if facts["is_valid"] else 1


def _evaluate(
    entry, dimension: str, actual: float, offset: float, measure_label: str, intent: str
) -> dict:
    """Compare one measured dimension against a standard.

    Two intents, because they are different questions:

    ``match``    - this part must itself conform to the standard. Symmetric band
                   around nominal, widened by ``offset``.
    ``envelope`` - this feature must accept ANY conforming part (a pocket, bore,
                   or slot). One-sided minimum at maximum material condition plus
                   the clearance. Designing such a feature to nominal fits only
                   the smallest half of conforming parts.
    """
    if dimension not in entry["dimensions"]:
        known = ", ".join(sorted(entry["dimensions"]))
        raise LabCadError(f"unknown dimension {dimension!r}. Available: {known}")
    dim = entry["dimensions"][dimension]
    nominal = float(dim["nominal"])
    tol_plus = float(dim.get("tol_plus", 0.0))
    tol_minus = float(dim.get("tol_minus", 0.0))

    if intent == "envelope":
        low = nominal + tol_plus + offset
        high = None
        passed = actual >= low - 1e-9
        headroom = round(actual - low, 4)
    else:
        low = nominal - tol_minus + offset
        high = nominal + tol_plus + offset
        passed = low - 1e-9 <= actual <= high + 1e-9
        headroom = None

    return {
        "dimension": dimension,
        "measure": measure_label,
        "intent": intent,
        "nominal_mm": nominal,
        "max_material_mm": round(nominal + tol_plus, 4),
        "expected_range_mm": [round(low, 4), None if high is None else round(high, 4)],
        "actual_mm": round(actual, 4),
        "headroom_mm": headroom,
        "pass": passed,
    }


def cmd_fit(args) -> int:
    entry = get_standard(args.standard)
    offset = float(args.clearance)
    results = []

    if args.value:
        # Value mode: check dimensions the model computed. Needed whenever the
        # interface is an internal feature (a pocket, a bore, a slot), where the
        # part's outer bounding box is not the dimension that has to match.
        if args.target is not None:
            eprint(
                f"warning: --value was given, so {args.target} is not measured. Drop the "
                "target, or drop --value to check the outer bounding box."
            )
        for pair in args.value:
            if "=" not in pair:
                raise LabCadError(f"--value expects dimension=number, got {pair!r}")
            name, _, raw = pair.partition("=")
            try:
                actual = float(raw)
            except ValueError as exc:
                raise LabCadError(f"--value {pair!r}: {raw!r} is not a number") from exc
            results.append(
                _evaluate(entry, name.strip(), actual, offset, "declared", args.intent)
            )
    else:
        checks = entry.get("fit_checks", [])
        if not checks:
            raise LabCadError(
                f"{args.standard} defines no automatic bounding-box checks (it is a "
                "reference dimension set). Use --value to check a computed dimension, "
                "or `standards --show` and check the interface by hand."
            )
        if args.target is None:
            raise LabCadError("fit needs either a target file or one or more --value arguments")
        facts = shape_facts(load_shape(args.target))
        for check in checks:
            actual = measure(facts, check["measure"], swap_xy=args.swap_xy)
            results.append(
                _evaluate(
                    entry, check["dimension"], actual, offset, check["measure"], args.intent
                )
            )

    passed = all(item["pass"] for item in results)
    payload = {
        "standard": args.standard,
        "title": entry["title"],
        "document": entry["document"],
        "verified_source": entry.get("verified", False),
        "clearance_applied_mm": offset,
        "mode": "declared" if args.value else "bounding_box",
        "swap_xy": args.swap_xy,
        "checks": results,
        "pass": passed,
    }

    lines = [f"{args.standard} ({entry['document']})  intent={args.intent}"]
    for item in results:
        mark = "PASS" if item["pass"] else "FAIL"
        low, high = item["expected_range_mm"]
        if high is None:
            expected = f">= {low:.3f}  headroom {item['headroom_mm']:+.3f}"
        else:
            expected = f"{low:.3f}..{high:.3f}"
        lines.append(
            f"  [{mark}] {item['dimension']:<22} {item['measure']:<9} "
            f"actual {item['actual_mm']:>9.3f}  expected {expected}"
        )
    if not entry.get("verified", False):
        lines.append("  WARNING: standard entry is not verified against the primary document.")
    if not passed and not args.value:
        if not args.swap_xy:
            lines.append("  hint: if the part is modelled rotated 90 degrees, rerun with --swap-xy")
        lines.append(
            "  hint: bounding-box mode measures the OUTER envelope. If the interface is a "
            "pocket, bore, or slot, pass the computed dimension with --value instead."
        )
    lines.append("Reminder: a passing bounding box is not a passing part. Run snapshot.py.")
    emit(payload, args.as_json, "\n".join(lines))
    return 0 if passed else 1


def _declared_interfaces(target: Path) -> tuple[list[dict], str]:
    """Read a model's declared interfaces from a manifest or from the model itself."""
    suffix = target.suffix.lower()
    if suffix == ".json":
        if not target.exists():
            raise LabCadError(f"file not found: {target}")
        try:
            payload = json.loads(target.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise LabCadError(f"{target} is not valid JSON: {exc}") from exc
        declared = payload.get("interfaces")
        if not declared:
            raise LabCadError(
                f"{target.name} records no declared interfaces. Add an INTERFACES list "
                "to the model (see references/build123d-patterns.md) and rerun gen.py."
            )
        return normalise_interfaces(declared), "manifest"
    if suffix == ".py":
        declared = model_interfaces(import_model(target))
        if not declared:
            raise LabCadError(
                f"{target.name} declares no INTERFACES. Add an INTERFACES list naming "
                "each standard, dimension, and computed value the part must satisfy "
                "(see references/build123d-patterns.md)."
            )
        return declared, "model"
    raise LabCadError(
        f"unsupported input {suffix!r}. Pass a *.manifest.json written by gen.py, or a "
        "*_model.py."
    )


def cmd_interfaces(args) -> int:
    """Check every interface a model declares about itself.

    This is the check that gates a fabrication decision, because the dimensions
    that have to be right are almost always internal features the outer bounding
    box cannot see.
    """
    declared, source = _declared_interfaces(args.target)

    results = []
    for entry in declared:
        standard = get_standard(entry["standard"])
        result = _evaluate(
            standard,
            entry["dimension"],
            entry["value"],
            entry["clearance"],
            "declared",
            entry["intent"],
        )
        result["feature"] = entry["feature"]
        result["standard"] = entry["standard"]
        result["document"] = standard["document"]
        result["verified_source"] = standard.get("verified", False)
        result["clearance_applied_mm"] = entry["clearance"]
        results.append(result)

    passed = all(item["pass"] for item in results)
    payload = {
        "target": str(args.target),
        "source": source,
        "checks": results,
        "pass": passed,
    }

    lines = [f"{args.target.name}: {len(results)} declared interface(s) from the {source}"]
    for item in results:
        mark = "PASS" if item["pass"] else "FAIL"
        low, high = item["expected_range_mm"]
        if high is None:
            expected = f">= {low:.3f}  headroom {item['headroom_mm']:+.3f}"
        else:
            expected = f"{low:.3f}..{high:.3f}"
        lines.append(
            f"  [{mark}] {item['feature']:<26} {item['actual_mm']:>9.3f} mm  "
            f"expected {expected}"
        )
        lines.append(
            f"         {item['standard']} {item['dimension']} "
            f"({item['intent']}, clearance {item['clearance_applied_mm']} mm)"
        )
        if not item["verified_source"]:
            lines.append("         WARNING: standard entry is not verified against the document.")
    lines.append("Reminder: a passing interface check is not a passing part. Run snapshot.py.")
    emit(payload, args.as_json, "\n".join(lines))
    return 0 if passed else 1


def _min_distance(shape_a, shape_b) -> float | None:
    for method in ("distance_to", "distance"):
        func = getattr(shape_a, method, None)
        if callable(func):
            try:
                return float(func(shape_b))
            except (TypeError, ValueError):
                continue
    func = getattr(shape_a, "distance_to_with_closest_points", None)
    if callable(func):
        try:
            return float(func(shape_b)[0])
        except (TypeError, ValueError, IndexError):
            return None
    return None


def _volume_of(result) -> float:
    """Total volume of an intersection result.

    ``Shape.intersect()`` returns a ShapeList with no ``.volume`` in build123d
    0.11.1, while the ``&`` operator returns a Solid that has one. Handle both.
    """
    if result is None:
        return 0.0
    volume = getattr(result, "volume", None)
    if volume is not None:
        return float(volume)
    total = 0.0
    for item in result:
        item_volume = getattr(item, "volume", None)
        if item_volume:
            total += float(item_volume)
    return total


def cmd_clearance(args) -> int:
    shape_a = load_shape(args.a)
    shape_b = load_shape(args.b)

    overlap_volume = 0.0
    try:
        overlap_volume = _volume_of(shape_a & shape_b)
    except Exception:  # noqa: BLE001 - kernel raises assorted OCCT errors
        try:
            overlap_volume = _volume_of(shape_a.intersect(shape_b))
        except Exception as exc:  # noqa: BLE001
            eprint(f"warning: intersection test failed ({exc}); relying on distance only")

    interferes = overlap_volume > 1e-6
    gap = None if interferes else _min_distance(shape_a, shape_b)

    payload = {
        "a": str(args.a),
        "b": str(args.b),
        "interference": interferes,
        "overlap_volume_mm3": round(overlap_volume, 6),
        "min_distance_mm": None if gap is None else round(gap, 4),
        "required_min_mm": args.min,
    }

    if interferes:
        payload["pass"] = False
        text = (
            f"INTERFERENCE: the two solids overlap by {overlap_volume:.4f} mm^3.\n"
            "Parts cannot be assembled as modelled."
        )
    elif gap is None:
        payload["pass"] = None
        text = (
            "Could not compute a minimum distance with this build123d build, and the "
            "solids do not overlap. Verify the fit visually with snapshot.py."
        )
    else:
        payload["pass"] = gap >= args.min
        mark = "PASS" if payload["pass"] else "FAIL"
        text = (
            f"[{mark}] minimum gap {gap:.4f} mm (required >= {args.min} mm)\n"
            f"       overlap volume {overlap_volume:.6f} mm^3"
        )

    emit(payload, args.as_json, text)
    if payload["pass"] is None:
        return 0
    return 0 if payload["pass"] else 1


def main() -> int:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--json", action="store_true", dest="as_json",
                        help="emit machine-readable JSON on stdout")
    sub = parser.add_subparsers(dest="command", required=True)

    p_std = sub.add_parser("standards", help="browse the bundled standards database")
    group = p_std.add_mutually_exclusive_group()
    group.add_argument("--list", action="store_true", help="list every standard (default)")
    group.add_argument("--show", metavar="ID", help="show one standard in full")
    p_std.set_defaults(func=cmd_standards)

    p_facts = sub.add_parser("facts", help="validity, bounding box, volume, area, centre")
    p_facts.add_argument("target", type=Path, help="STEP, STL, or *_model.py")
    p_facts.set_defaults(func=cmd_facts)

    p_int = sub.add_parser(
        "interfaces",
        help="check every interface a model declares about itself (the build gate)",
        description="Check each entry of a model's INTERFACES list against its standard. "
                    "Use this rather than `fit` whenever the interface is an internal "
                    "feature -- a pocket, bore, or slot -- which is most of the time. "
                    "Reading a manifest needs no geometry kernel.",
    )
    p_int.add_argument("target", type=Path,
                       help="a *.manifest.json written by gen.py, or a *_model.py")
    p_int.set_defaults(func=cmd_interfaces)

    p_fit = sub.add_parser("fit", help="check one dimension against a standard by hand")
    p_fit.add_argument("target", type=Path, nargs="?",
                       help="STEP, STL, or *_model.py; omit when using --value")
    p_fit.add_argument("--standard", required=True, help="standard ID from `standards --list`")
    p_fit.add_argument("--value", action="append", metavar="DIMENSION=MM",
                       help="check a dimension the model computed, e.g. "
                            "footprint_length=128.81. Use this when the interface is an "
                            "internal feature. Repeatable; needs no geometry kernel.")
    p_fit.add_argument("--intent", choices=("match", "envelope"), default="match",
                       help="'match': this part must itself conform to the standard "
                            "(symmetric band). 'envelope': this feature must accept any "
                            "conforming part, so it is checked one-sided against maximum "
                            "material condition. Use 'envelope' for pockets, bores, and "
                            "slots. (default: match)")
    p_fit.add_argument("--clearance", type=float, default=0.0,
                       help="total intended clearance in mm, e.g. 0.8 for a pocket with "
                            "0.4 mm clearance per side (default: 0)")
    p_fit.add_argument("--swap-xy", action="store_true",
                       help="the part is modelled with x and y exchanged")
    p_fit.set_defaults(func=cmd_fit)

    p_clr = sub.add_parser("clearance", help="minimum distance between two solids")
    p_clr.add_argument("a", type=Path)
    p_clr.add_argument("b", type=Path)
    p_clr.add_argument("--min", type=float, default=0.2,
                       help="required minimum gap in mm (default: 0.2)")
    p_clr.set_defaults(func=cmd_clearance)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    main_guard(main)
