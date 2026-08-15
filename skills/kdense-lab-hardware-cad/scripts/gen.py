#!/usr/bin/env python3
"""Generate fabrication artifacts from a parametric build123d model.

Runs a model file's ``build()``, exports STEP (authoritative) and STL (preview and
printing), and writes a manifest recording the source hash, resolved parameters,
library versions, and measured geometry.

    python scripts/gen.py carrier_model.py --outdir out/
    python scripts/gen.py carrier_model.py --outdir out/ --param wall_t_mm=4.0
    python scripts/gen.py plate_model.py --outdir out/ --dxf     # 2D laser profile
"""

from __future__ import annotations

import argparse
import json
import platform
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    LabCadError,
    emit,
    eprint,
    import_model,
    main_guard,
    model_interfaces,
    model_parameters,
    parse_params,
    require_build123d,
    sha256_of,
    shape_facts,
)


def _build123d_version() -> str:
    from importlib.metadata import PackageNotFoundError, version  # noqa: PLC0415

    try:
        return version("build123d")
    except PackageNotFoundError:  # pragma: no cover
        return "unknown"


def _export_dxf(part, path: Path, build123d, height: float | None) -> float:
    """Slice the part on a horizontal plane and write the profile as DXF.

    ``section()`` is a module-level operation in build123d 0.11.1, not a method on
    the shape. The default cut height is the middle of the part rather than z = 0,
    because a part modelled sitting on the build plate has nothing but a degenerate
    face at z = 0. Returns the height actually used, for the manifest.
    """
    if height is None:
        bbox = part.bounding_box()
        height = (float(bbox.min.Z) + float(bbox.max.Z)) / 2.0

    plane = build123d.Plane.XY.offset(height)
    try:
        profile = build123d.section(part, plane, mode=build123d.Mode.PRIVATE)
    except Exception as exc:  # noqa: BLE001 - the kernel raises assorted OCCT errors
        raise LabCadError(f"DXF section at z={height:.3f} mm failed: {exc}") from exc
    if not profile.faces():
        raise LabCadError(
            f"DXF section at z={height:.3f} mm is empty. Pass --dxf-z with a height "
            "that actually cuts material."
        )

    exporter = build123d.ExportDXF(unit=build123d.Unit.MM)
    exporter.add_shape(profile)
    exporter.write(str(path))
    return height


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("model", type=Path, help="path to a *_model.py exposing build() -> Part")
    parser.add_argument("--outdir", type=Path, default=Path("out"), help="output directory (default: out)")
    parser.add_argument("--name", help="artifact basename (default: model filename without _model)")
    parser.add_argument("--param", action="append", metavar="KEY=VALUE",
                        help="override a model parameter; repeatable")
    parser.add_argument("--tolerance", type=float, default=1e-3,
                        help="STL linear deflection in mm (default: 0.001)")
    parser.add_argument("--angular-tolerance", type=float, default=0.1,
                        help="STL angular deflection (default: 0.1)")
    parser.add_argument("--dxf", action="store_true",
                        help="also export a 2D DXF profile, sliced on a horizontal plane")
    parser.add_argument("--dxf-z", type=float, default=None, metavar="MM",
                        help="height of the DXF section plane (default: the middle of the part)")
    parser.add_argument("--no-stl", action="store_true", help="skip the STL export")
    parser.add_argument("--json", action="store_true", dest="as_json", help="emit the manifest as JSON on stdout")
    args = parser.parse_args()

    if args.dxf_z is not None and not args.dxf:
        raise LabCadError("--dxf-z sets the section height for --dxf; pass --dxf as well")

    build123d = require_build123d()
    overrides = parse_params(args.param)

    eprint(f"building {args.model.name} ...")
    module = import_model(args.model, overrides)
    builder = getattr(module, "build", None)
    if builder is None or not callable(builder):
        raise LabCadError(f"{args.model.name} must define a callable build() that returns a Part")
    part = builder()
    if part is None:
        raise LabCadError(f"{args.model.name}: build() returned None")
    params = model_parameters(module)
    # Read the declared interfaces after build(), so a model that computes them in
    # build() and stores them on the module still reports the resolved numbers.
    interfaces = model_interfaces(module)
    if interfaces and overrides and not callable(getattr(module, "interfaces", None)):
        eprint(
            "WARNING: this model declares a static INTERFACES list, which was evaluated "
            "at import - before --param was applied. Any interface derived from an "
            "overridden parameter is now recorded WRONG. Convert INTERFACES into an "
            "interfaces() function that computes from the current parameters."
        )

    stem = args.name or args.model.stem.removesuffix("_model")
    outdir = args.outdir
    outdir.mkdir(parents=True, exist_ok=True)

    step_path = outdir / f"{stem}.step"
    build123d.export_step(part, str(step_path), unit=build123d.Unit.MM)
    eprint(f"wrote {step_path}")
    artifacts = {"step": str(step_path)}

    if not args.no_stl:
        stl_path = outdir / f"{stem}.stl"
        build123d.export_stl(
            part, str(stl_path),
            tolerance=args.tolerance,
            angular_tolerance=args.angular_tolerance,
        )
        eprint(f"wrote {stl_path}")
        artifacts["stl"] = str(stl_path)

    dxf_z = None
    dxf_error = None
    if args.dxf:
        dxf_path = outdir / f"{stem}.dxf"
        try:
            dxf_z = _export_dxf(part, dxf_path, build123d, args.dxf_z)
        except LabCadError as exc:
            # Not fatal: finish the manifest so the STEP already on disk keeps its
            # provenance record, and fail at the end instead.
            dxf_error = str(exc)
            eprint(f"warning: DXF export failed: {exc}")
        else:
            eprint(f"wrote {dxf_path} (section at z = {dxf_z:.3f} mm)")
            artifacts["dxf"] = str(dxf_path)

    facts = shape_facts(part)
    if not facts["is_valid"]:
        eprint(
            "WARNING: the generated solid fails OpenCascade validity checks. "
            "Fix the model source before fabricating."
        )

    manifest = {
        "artifact_name": stem,
        "source": {
            "path": str(args.model.resolve()),
            "sha256": sha256_of(args.model),
        },
        "parameters": params,
        "overrides": overrides,
        "interfaces": interfaces,
        "geometry": facts,
        "artifacts": artifacts,
        "dxf_section_z_mm": dxf_z,
        "dxf_error": dxf_error,
        "environment": {
            "build123d": _build123d_version(),
            "python": platform.python_version(),
            "platform": platform.platform(),
        },
        "units": "mm",
    }

    manifest_path = outdir / f"{stem}.manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    eprint(f"wrote {manifest_path}")

    if not interfaces:
        eprint(
            "note: this model declares no INTERFACES, so no interface can be checked "
            "automatically. See references/build123d-patterns.md."
        )

    box = facts["bounding_box_mm"]
    lines = [
        f"{stem}: {box['x']:.2f} x {box['y']:.2f} x {box['z']:.2f} mm, "
        f"volume {facts['volume_mm3']:.1f} mm^3, valid={facts['is_valid']}, "
        f"declared interfaces: {len(interfaces)}",
        f"Next: python scripts/check.py facts {step_path}",
    ]
    if interfaces:
        lines.append(f"      python scripts/check.py interfaces {manifest_path}")
    lines.append(
        f"      python scripts/snapshot.py {step_path} --out {outdir / (stem + '.png')}"
    )
    emit(manifest, args.as_json, "\n".join(lines))
    return 0 if facts["is_valid"] and dxf_error is None else 1


if __name__ == "__main__":
    main_guard(main)
