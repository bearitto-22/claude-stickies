#!/usr/bin/env python3
"""Claude Stickies - A macOS Stickies clone for GNOME."""

import os
import sys

# Force X11 backend so we can use _NET_WM_STATE_ABOVE for always-on-top.
# Wayland has no client API for this. XWayland works fine for small windows.
os.environ.setdefault("GDK_BACKEND", "x11")

from stickies.app import StickiesApp


def main():
    app = StickiesApp()
    return app.run(sys.argv)


if __name__ == "__main__":
    sys.exit(main())
