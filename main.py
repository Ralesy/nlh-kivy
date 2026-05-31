#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mini RPG — точка входа приложения (Kivy UI).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from ui.ui_app import RPGApp

if __name__ == "__main__":
    RPGApp().run()
