#!/usr/bin/env python3
"""Punto de entrada: permite ejecutar  ``python gv.py <comando>``.

Equivale a  ``python -m gestion_vehicular``.
"""

from gestion_vehicular.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
