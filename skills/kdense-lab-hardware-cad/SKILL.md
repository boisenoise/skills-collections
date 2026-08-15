---
name: lab-hardware-cad
description: Design custom laboratory hardware as parametric build123d models and export fabrication-ready STEP, STL, and DXF files - microfluidic chips and molds, optomechanical mounts and breadboard adapters, cuvette and microplate holders, tube racks, animal-behavior rigs, and 3D-printed instrument fixtures. Use when a research task needs a physical part that must mate with standardized labware, an optical table, a cage system, or a printer, CNC, or laser process.
license: MIT
compatibility: Python 3.10-3.14 with build123d 0.11.1 and matplotlib for snapshots. Geometry commands require build123d; the standards lookup and the interface check run on the standard library alone. No network access needed.
allowed-tools: Read Write Edit Bash Glob Grep
metadata:
  version: "1.1"
  skill-author: K-Dense Inc.
  last-reviewed: "2026-08-14"
  build123d-version: "0.11.1"
---

# Lab Hardware CAD

Design physical research hardware as **parametric Python source**, export STEP as the
authoritative artifact, and verify the result both numerically and visually before anything
is fabricated.

The hard part of lab hardware is almost never the geometry. It is that the part must mate with
equipment whose dimensions are fixed by a published standard or a vendor drawing. A holder that
is 0.5 mm too wide does not fit the plate reader; a channel with the wrong aspect ratio collapses
during bonding; a mount whose bolt pattern is 25.4 mm instead of 25.0 mm will not reach the
optical table. This skill exists to keep those numbers correct and checked.

## When to use

Use for any request to design, model, or fabricate a physical part for a lab: chip, mold, mount,
adapter, holder, rack, bracket, enclosure, jig, fixture, arena, or maze. Also use to inspect or
modify an existing STEP file.

Do **not** use for finite-element analysis, computational fluid dynamics, molecular structure,
or scientific plotting. Those are different skills.

## Setup

```bash
uv venv --python 3.12 .venv-labcad
uv pip install --python .venv-labcad/bin/python "build123d==0.11.1" "matplotlib>=3.8"
```

build123d 0.11.1 requires Python >=3.10,<3.15 and pulls in the OpenCascade kernel through
`cadquery-ocp-novtk`. The wheel is large; install once per project and reuse it.

All bundled scripts take `--help`. `check.py standards` runs without build123d installed.

**Model files are executed, not parsed.** `gen.py`, `check.py`, and `snapshot.py` import a
`*_model.py` and call its `build()`, which runs arbitrary Python in the current environment. That
is inherent to parametric CAD — the source is the design. Only run model files authored in this
session or supplied by the user from a trusted location. If a model came from the internet, a
shared drive, or an untrusted colleague, read it before running it and say that you did.

## Required workflow

Follow these steps in order. Steps 5 and 6 are not optional, and step 6 is not waived by step 5
passing.

### 1. Route to a device family

Read the request, classify it, and load **exactly one** family reference. Do not load all four —
they are long, and mixing conventions between families is a common source of error.

| If the part is | Load |
| --- | --- |
| A chip, mold, channel network, flow cell, gasket, or anything with fluid ports | `references/microfluidics.md` |
| A mount, post, breadboard adapter, cage-system part, filter or sample holder in a beam path | `references/optomechanics.md` |
| An adapter, insert, rack, or holder for plates, cuvettes, tubes, slides, or dishes | `references/labware-adapters.md` |
| An arena, maze, head-fixation part, spout, tether, or extrusion-mounted enclosure for animal work | `references/behavior-rigs.md` |

If the part genuinely spans two families — a microfluidic chip that bolts to an optical table —
load the family that owns the **critical interface**, then read only the interface section of the
second. State in your response which family you routed to.

### 2. Establish the interface dimensions before any geometry

Every part has at least one mating interface. Before writing code, write down for each interface:

- the **source** of the dimension: a published standard, a vendor drawing, or a user measurement;
- the **nominal value and tolerance**;
- the **clearance or interference** you intend, and why.

Look the number up in `assets/standards.json` or the family reference. **Never write an interface
dimension from memory.** If the number is not in the standards file or the reference, ask the user
for the vendor drawing or the measurement rather than guessing. A guessed interface dimension is
the single most expensive failure mode in this skill.

A feature that must *receive* a standardised component is sized against that component's
**maximum material condition** — nominal plus its plus-tolerance — and only then given clearance.
Sized from nominal instead, it fits only the smaller half of conforming parts.

```bash
python scripts/check.py standards --list
python scripts/check.py standards --show slas-microplate-footprint
```

### 3. Choose the process before choosing the geometry

Read `references/fabrication-limits.md`. Process determines minimum wall, minimum feature,
achievable tolerance, and whether the part survives autoclaving or contact with your solvent.
FDM cannot hold ±0.05 mm; SLA resin is generally not safe for cell contact without post-cure and
testing. Record the process and material in the model docstring.

### 4. Author a parametric model

Write `<part>_model.py`. The source is the authoritative artifact — **never hand-edit an exported
STEP file**, and never regenerate from a mesh.

Requirements:

- Every dimension that a user might change is a **module-level named constant** with units in the
  name: `bore_d_mm`, `wall_t_mm`, `post_h_mm`. No bare numbers in the body except 0, 1, and 2.
- Expose `build() -> Part`. `gen.py` calls it.
- Group parameters into an `INTERFACE` block (dimensions fixed by a standard, annotated with the
  standard ID) and a `DESIGN` block (dimensions you are free to choose).
- **Derive every computed dimension inside a function**, never at module level, so `--param`
  overrides actually reach it.
- Declare an `interfaces()` function returning the dimensions the part must fit, each with its
  standard ID and intent. This is what makes the interface machine-checkable in step 5.
- Put the process, material, and every interface source in the module docstring.

```python
"""SLAS microplate carrier for a custom stage insert.

Process: FDM, PETG, 0.2 mm layer.  Tolerance budget +/-0.3 mm.
Interfaces:
  - Plate pocket: ANSI/SLAS 1-2004 (R2012) footprint 127.76 x 85.48 mm, +/-0.25.
  - Stage bolts: user-measured, 40.0 mm centres (drawing in docs/stage.pdf).
"""
from build123d import *

# --- INTERFACE (fixed by standard; do not tune) ---
plate_l_mm = 127.76   # ANSI/SLAS 1-2004 nominal
plate_w_mm = 85.48    # ANSI/SLAS 1-2004 nominal
plate_tol_mm = 0.25   # ANSI/SLAS 1-2004; the pocket is sized to nominal + this
# --- DESIGN (free) ---
pocket_clearance_mm = 0.40   # per-side; FDM, see fabrication-limits.md
wall_t_mm = 3.0
floor_t_mm = 2.5
body_h_mm = 12.0


def pocket_mm() -> tuple[float, float]:
    """Pocket at the plate's maximum material condition plus clearance per side.

    A pocket sized from nominal jams on roughly half of conforming plates.
    """
    growth = plate_tol_mm + 2 * pocket_clearance_mm
    return plate_l_mm + growth, plate_w_mm + growth


def interfaces() -> list[dict]:
    """What this part must fit. `check.py interfaces` verifies every entry."""
    pocket_l, pocket_w = pocket_mm()
    return [
        {"feature": "plate pocket length", "standard": "slas-microplate-footprint",
         "dimension": "footprint_length", "value": pocket_l,
         "intent": "envelope", "clearance": 2 * pocket_clearance_mm},
        {"feature": "plate pocket width", "standard": "slas-microplate-footprint",
         "dimension": "footprint_width", "value": pocket_w,
         "intent": "envelope", "clearance": 2 * pocket_clearance_mm},
    ]


def build() -> Part:
    pocket_l, pocket_w = pocket_mm()
    with BuildPart() as carrier:
        Box(pocket_l + 2 * wall_t_mm, pocket_w + 2 * wall_t_mm, body_h_mm)
        with Locations((0, 0, floor_t_mm)):
            Box(pocket_l, pocket_w, body_h_mm, mode=Mode.SUBTRACT,
                align=(Align.CENTER, Align.CENTER, Align.MIN))
    return carrier.part
```

See `references/build123d-patterns.md` for the builder-vs-algebra choice, the `interfaces()`
contract, sketching, selectors, fillets, and threaded-insert bores.

### 5. Generate and check the interfaces

```bash
python scripts/gen.py carrier_model.py --outdir out/
python scripts/check.py facts out/carrier.step
python scripts/check.py interfaces out/carrier.manifest.json
```

`gen.py` writes `carrier.step` (authoritative), `carrier.stl` (mesh preview and printing), and
`carrier.manifest.json` recording the source hash, resolved parameters, declared interfaces,
library versions, and measured bounding box, volume, and validity. The manifest is the provenance
record — keep it with the artifact.

`check.py facts` reports `is_valid`, bounding box, volume, surface area, centre of mass, and
solid count. A part that reports `is_valid: false` is broken geometry; fix the source before going
further.

`check.py interfaces` is the check that gates fabrication. It evaluates every entry the model
declared against the standards database and exits non-zero on failure. Use it rather than
`check.py fit` for anything internal: **the interface is almost always a pocket, bore, or slot,
and none of those appear in the part's outer bounding box.** `fit` measures that outer envelope, so
running it on a carrier reports the outside of the walls and fails against the plate footprint.
Reach for `fit` only to check one number by hand, or when the part's own outline is the interface —
a gasket cut to a plate footprint, for instance:

```bash
# check one dimension by hand, without a geometry kernel
python scripts/check.py fit --standard slas-microplate-footprint \
  --intent envelope --clearance 0.8 --value footprint_length=128.81
```

For assemblies, check that parts do not interfere:

```bash
python scripts/check.py clearance out/carrier.step out/lid.step --min 0.3
```

### 6. Snapshot and actually look at it

```bash
python scripts/snapshot.py out/carrier.step --out out/carrier.png
```

Then **read the PNG**. This step is mandatory after every generation and every modification.
Deterministic checks passing is not a reason to skip it: `is_valid` and a correct bounding box are
both fully consistent with a pocket cut on the wrong face, an inverted mold polarity, a boss
placed outside the body, or a fillet that ate a feature. Those errors are obvious in a picture and
invisible in the numbers.

The six views are true orthographic projections, and the outlines are the model's real edges drawn
**without hidden-line removal**. So a circle visible "through" material is a bore on the far side,
not a window — the part is not transparent. Read it that way rather than reporting a hole that
is not there.

State in your response what you saw in the snapshot, not merely that you generated one.

### 7. Repair through the source

If any check fails, edit the parameters or the model code, rerun `gen.py`, and rerun **both**
step 5 and step 6. Never patch the STEP.

### 8. Report before fabrication

Work through `references/validation.md` and give the user: the process and material, every
interface dimension with its source and tolerance, the clearances chosen, what the snapshot showed,
and any check that did not pass.

Flag explicitly every interface the automatic check could not cover — a vendor drawing, a user
measurement, a standard not in the bundled database. `check.py interfaces` reports only what the
model declared against a known standard, so silence there is not confirmation; a dimension nobody
could check has to be named as such.

## Units

build123d is unitless internally and everything in this skill is **millimetres and degrees**.
`export_step` is called with `Unit.MM`. Imperial hardware appears throughout optomechanics
(1/4-20 screws, 1 inch grids, SM1 threads); convert to millimetres in a single named constant at
the point of definition and never mix systems inside an expression. 1 inch is exactly 25.4 mm, and
a 25 mm metric optical grid is **not** interchangeable with a 1 inch imperial grid — the error
accumulates to 1.6 mm over four holes.

## Tolerances and fits

A nominal dimension is not a fit. Every mating dimension needs a deliberate clearance chosen from
the process tolerance in `references/fabrication-limits.md`. Common defaults, per side:

| Fit | FDM | SLA | CNC |
| --- | --- | --- | --- |
| Free-sliding (plate in a pocket) | 0.40 mm | 0.20 mm | 0.10 mm |
| Located but removable | 0.25 mm | 0.10 mm | 0.05 mm |
| Press / interference | -0.05 mm | -0.03 mm | -0.02 mm |

These are starting points for a first article, not guarantees. Say so when you report them, and
recommend printing a test coupon of the critical interface before committing to a full part.

## Scientific caveats

- **Material compatibility governs.** A geometrically perfect part in the wrong polymer fails in
  service: autoclave cycles distort PLA, many solvents craze acrylic, and uncured SLA resin is
  cytotoxic. Check `references/fabrication-limits.md` before recommending a material for anything
  contacting cells, tissue, solvents, or heat.
- **Optical parts have non-geometric requirements.** Autofluorescence, surface roughness, and
  stray-light scatter are not visible in a STEP file. Black resin is not automatically low-scatter.
- **Vendor labware varies.** The SLAS standards fix the plate footprint but not well geometry,
  skirt profile, or lid fit, and consumable tubes differ between suppliers. Design to the standard
  where one exists; otherwise require a measurement.
- **A passing bounding box is not a passing part.** `fit` checks the dimensions it is given. It
  cannot see a missing feature, and it does not replace the snapshot.

## References

| File | Contents |
| --- | --- |
| `references/microfluidics.md` | Channel cross-sections and aspect ratios, mold vs chip polarity, minimum features by process, port and tubing interfaces, bonding lands, dead volume |
| `references/optomechanics.md` | Breadboard grids and screw clearances, post and pedestal heights, 30 mm cage geometry, SM lens-tube threads, beam height |
| `references/labware-adapters.md` | ANSI/SLAS 1-4 microplate dimensions, cuvettes, tubes, slides, dishes, deck and stage constraints |
| `references/behavior-rigs.md` | Arena and maze geometry, head-fixation interfaces, spouts and ports, T-slot extrusion, cleaning and durability |
| `references/fabrication-limits.md` | Process tolerances, minimum walls and features, clearance and thread inserts, materials, autoclave and solvent and biocompatibility |
| `references/validation.md` | Pre-fabrication checklist and the failure modes each item catches |
| `references/build123d-patterns.md` | build123d 0.11.1 API cookbook: builder vs algebra, sketches, selectors, joints, exports |

## Scripts

| Command | Purpose |
| --- | --- |
| `gen.py <model.py> --outdir DIR` | Run `build()`, export STEP and STL, write the provenance manifest |
| `gen.py <model.py> --dxf [--dxf-z MM]` | Also slice a 2D DXF profile for laser cutting (default plane: mid-height) |
| `check.py facts <step>` | Validity, bounding box, volume, area, centre of mass, solid count |
| `check.py interfaces <manifest\|model.py>` | Check every interface the model declares; non-zero exit on failure |
| `check.py fit --standard ID --value DIM=MM` | Check one dimension by hand, or a part whose outer envelope is the interface |
| `check.py clearance <a> <b> --min MM` | Minimum distance between two solids; detects interference |
| `check.py standards [--list\|--show ID]` | Browse the bundled standards data (standard library only) |
| `snapshot.py <step> --out PNG` | Six-view orthographic and isometric render for visual review |

All commands accept `--json` for machine-readable output and write progress to stderr.
`check.py standards`, and `check.py interfaces` on a manifest, run without build123d installed.
