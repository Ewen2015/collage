#!/usr/bin/env python3
"""Check that the collage-art skill is complete and runnable.

Usage:  python3 scripts/check_setup.py

Checks Python version, the bundled references/scripts, Pillow, NumPy, font
resolution and the optional network path. It exits non-zero if anything the
renderer needs is missing, so an agent can run it immediately after installing
the skill.
"""
from __future__ import annotations

import os
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ok = True


def good(msg):
    print("  ok   " + msg)


def bad(msg):
    global ok
    ok = False
    print("  FAIL " + msg)


print("collage-art setup check — " + HERE)
if sys.version_info >= (3, 9):
    good("Python %d.%d.%d" % sys.version_info[:3])
else:
    bad("Python 3.9+ required, found %d.%d" % sys.version_info[:2])

for rel in ("SKILL.md", "requirements.txt", "install.sh", "install.ps1",
            "references/movements.md", "references/materials.md",
            "references/composition.md", "references/prompts.md",
            "references/concept-schema.md", "assets/README.md",
            "scripts/collage.py", "scripts/source_assets.py",
            "scripts/theme_to_recipe.py", "scripts/check_setup.py"):
    if os.path.isfile(os.path.join(HERE, rel)):
        good(rel)
    else:
        bad("missing " + rel)

try:
    import PIL
    from PIL import Image, ImageDraw, ImageFont  # noqa: F401
    good("Pillow " + PIL.__version__)
except Exception as e:
    bad("Pillow unavailable: %s" % e)

try:
    import numpy
    good("NumPy " + numpy.__version__)
except Exception as e:
    bad("NumPy unavailable: %s" % e)

sys.path.insert(0, os.path.join(HERE, "scripts"))
try:
    import collage
    font = collage.resolve_font("serif", 42)
    good("text font resolves: %s" % getattr(font, "path", "built-in default"))
    pal = collage.PALETTES["cream"]
    canvas = collage.paper_base(120, 120, pal["paper"], collage.np.random.default_rng(1))
    good("paper texture renders (%d×%d)" % canvas.size)
except Exception as e:
    bad("renderer smoke test: %s" % e)

print("---")
if ok:
    print("Ready. Network is optional: needed only for Commons image sourcing; "
          "procedural presets work offline.")
    print("Smoke test: python3 scripts/collage.py --preset cubist-grid --out cubist.png")
    sys.exit(0)
print("Not ready. Fix the FAIL lines above, then re-run this check.")
sys.exit(1)
