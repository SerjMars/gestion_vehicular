"""Conexión y esquema de la base de datos SQLite.

Toda la persistencia vive aquí. El resto del programa solo pide una conexión
con :func:`conectar` y usa el repositorio; así, el día de mañana, una app web
puede apuntar a la misma base de datos (o migrar el esquema a otro motor) sin
tocar la lógica de negocio.
"""

from __future__ import annotations

import os
import sqlite3

# Ubicación por defecto de la base de datos. Se puede sobreescribir con la
# variable de entorno GV_DB o con el parámetro --db de la línea de comandos.
RUTA_DB_POR_DEFECTO = os.environ.get(
    "GV_DB", os.path.join(os.path.expanduser("~"), "gestion_vehicular.db")
)

# Esquema completo. Usamos "IF NOT EXISTS" para que crear la base sea idempotente.
ESQUEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS sucursales (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL UNIQUE,
    ciudad      TEXT,
    estado      TEXT,
    responsable TEXT,
    telefono    TEXT
);

CREATE TABLE IF NOT EXISTS vehiculos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    sucursal_id INTEGER NOT NULL REFERENCES sucursales(id) ON DELETE CASCADE,
    tipo        TEXT NOT NULL,          -- sedan | hatchback | pickup
    marca       TEXT NOT NULL,
    modelo      TEXT NOT NULL,
    anio        INTEGER,
    placas      TEXT UNIQUE,
    num_serie   TEXT,                   -- NIV / número de serie
    km_actual   INTEGER NOT NULL DEFAULT 0,
    energia     TEXT NOT NULL DEFAULT 'combustion',  -- combustion | hibrido | electrico
    activo      INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS conductores (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    sucursal_id       INTEGER REFERENCES sucursales(id) ON DELETE SET NULL,
    nombre            TEXT NOT NULL,
    num_licencia      TEXT,
    tipo_licencia     TEXT,             -- A | B | C ... según el estado
    vigencia_licencia TEXT,             -- fecha ISO YYYY-MM-DD
    telefono          TEXT,
    activo            INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS mantenimientos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    vehiculo_id   INTEGER NOT NULL REFERENCES vehiculos(id) ON DELETE CASCADE,
    tipo          TEXT NOT NULL,        -- afinacion | cambio_aceite | llantas | frenos ...
    fecha         TEXT NOT NULL,        -- fecha ISO en que se realizó
    km            INTEGER,              -- kilometraje al realizarlo
    costo         REAL,
    taller        TEXT,
    proximo_fecha TEXT,                 -- próximo servicio sugerido (fecha ISO)
    proximo_km    INTEGER,              -- próximo servicio sugerido (km)
    notas         TEXT
);

-- Derechos, permisos, tenencia, verificación, seguro y licencias.
-- Una obligación pertenece a un vehículo (tenencia, verificación...) o a un
-- conductor (licencia). Exactamente una de las dos referencias va poblada.
CREATE TABLE IF NOT EXISTS obligaciones (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    vehiculo_id       INTEGER REFERENCES vehiculos(id) ON DELETE CASCADE,
    conductor_id      INTEGER REFERENCES conductores(id) ON DELETE CASCADE,
    tipo              TEXT NOT NULL,    -- tenencia | verificacion | seguro | licencia ...
    descripcion       TEXT,
    periodo           TEXT,             -- ej. "2026", "2026-1er semestre"
    fecha_vencimiento TEXT NOT NULL,   -- fecha ISO YYYY-MM-DD
    monto             REAL,
    pagado            INTEGER NOT NULL DEFAULT 0,
    fecha_pago        TEXT,
    notas             TEXT,
    CHECK (vehiculo_id IS NOT NULL OR conductor_id IS NOT NULL)
);

CREATE INDEX IF NOT EXISTS idx_veh_sucursal   ON vehiculos(sucursal_id);
CREATE INDEX IF NOT EXISTS idx_mant_vehiculo  ON mantenimientos(vehiculo_id);
CREATE INDEX IF NOT EXISTS idx_obl_vehiculo   ON obligaciones(vehiculo_id);
CREATE INDEX IF NOT EXISTS idx_obl_conductor  ON obligaciones(conductor_id);
CREATE INDEX IF NOT EXISTS idx_obl_venc       ON obligaciones(fecha_vencimiento);
"""


def conectar(ruta: str | None = None) -> sqlite3.Connection:
    """Abre (creando si hace falta) la base de datos y devuelve la conexión.

    Las filas se devuelven como ``sqlite3.Row`` para poder accederlas por nombre
    de columna. Se activan las claves foráneas en cada conexión.
    """
    ruta = ruta or RUTA_DB_POR_DEFECTO
    conexion = sqlite3.connect(ruta)
    conexion.row_factory = sqlite3.Row
    conexion.execute("PRAGMA foreign_keys = ON")
    return conexion


def inicializar(conexion: sqlite3.Connection) -> None:
    """Crea las tablas e índices si no existen y migra bases anteriores."""
    conexion.executescript(ESQUEMA)
    _migrar(conexion)
    conexion.commit()


def _columnas(conexion: sqlite3.Connection, tabla: str) -> set[str]:
    return {fila["name"] for fila in conexion.execute(f"PRAGMA table_info({tabla})")}


def _migrar(conexion: sqlite3.Connection) -> None:
    """Aplica cambios de esquema sobre bases de datos creadas con versiones previas.

    Es idempotente: solo agrega lo que falta. Así, quien ya tenía datos cargados
    no los pierde al actualizar el programa.
    """
    # v1 -> v1.1: columna de energía en vehículos (para eléctricos/híbridos).
    if "energia" not in _columnas(conexion, "vehiculos"):
        conexion.execute(
            "ALTER TABLE vehiculos ADD COLUMN energia TEXT NOT NULL DEFAULT 'combustion'"
        )
