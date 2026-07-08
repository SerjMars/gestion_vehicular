"""Gestión Vehicular: control de mantenimientos, derechos, permisos y licencias.

El paquete separa tres capas para facilitar una futura migración a web:

- ``db``          : conexión y esquema de la base de datos SQLite.
- ``repositorio`` : acceso a datos y lógica de negocio (reutilizable por una web).
- ``cli``         : interfaz de línea de comandos (solo presentación).
"""

__version__ = "1.0.0"
