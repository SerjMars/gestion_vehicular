#!/usr/bin/env python3
"""Interfaz web: iniciar con  ``python app.py``  y abrir http://127.0.0.1:5000

Usa la misma base de datos que la línea de comandos (``~/gestion_vehicular.db``
por defecto, o la ruta de la variable de entorno ``GV_DB``).
"""

import os

from gestion_vehicular.web import crear_app

app = crear_app()

if __name__ == "__main__":
    host = os.environ.get("GV_WEB_HOST", "127.0.0.1")
    port = int(os.environ.get("GV_WEB_PORT", "5000"))
    app.run(host=host, port=port, debug=True)
