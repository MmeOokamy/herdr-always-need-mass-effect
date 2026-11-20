#!/usr/bin/env python3
"""Renders the Glyph drone of the notifications (me-toast/glyph/*.png).

The drawing is the "Glyph" mascot of odoo-badge-reminder (paint_drone in
badge_reminder/mascot.py): a translucent holographic sphere, a central lens
and an orbiting ring. This script imports it from a clone of that project
and renders one image per state, at SIZE px (shown at about 44 px: twice
the pixels for high-density screens).

States: calm (blue, info and done), alert (orange with a pulsing halo:
an agent needs you, a warning) and error (orange with a red lens).

Usage: <odoo-badge-reminder>/.venv/bin/python me-toast/tools/render_glyph.py <odoo-badge-reminder>
       (needs PySide6, from that project's virtual environment)
"""

import os
import sys

if len(sys.argv) != 2:
    sys.exit(__doc__)
sys.path.insert(0, os.path.abspath(sys.argv[1]))
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QPointF, Qt  # noqa: E402
from PySide6.QtGui import QGuiApplication, QPainter, QPixmap  # noqa: E402

from badge_reminder import mascot  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "glyph")
SIZE = 112
PHASE = 0.9  # moment of the animation: ring beacons on both sides, lens a little to the right
# State of the notification -> status of the drone in odoo-badge-reminder.
STATES = {"calm": "ok", "alert": "reminder", "error": "forgot"}


def main():
    app = QGuiApplication(sys.argv[:1])  # noqa: F841 (Qt needs an application to paint)
    mascot.set_style("drone")
    scale = SIZE / 150  # the sphere and its halo (radius 1.7 x 40) fit in 150 px
    os.makedirs(OUT, exist_ok=True)
    for state, status in STATES.items():
        pixmap = QPixmap(SIZE, SIZE)
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.Antialiasing)
        # Accessories ("!", "?") are left out: the toast says what happens.
        original = mascot._paint_accessories
        mascot._paint_accessories = lambda *_args: None
        mascot.paint_drone(painter, QPointF(SIZE / 2, SIZE / 2), status, PHASE, scale=scale)
        mascot._paint_accessories = original
        painter.end()
        pixmap.save(os.path.join(OUT, f"{state}.png"))
    print(os.path.normpath(OUT))


if __name__ == "__main__":
    main()
