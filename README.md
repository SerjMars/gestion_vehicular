# Gestión Vehicular

Herramienta de línea de comandos para gestionar, sobre una flota distribuida en
varias sucursales, tres cosas:

1. **Mantenimientos** de cada vehículo (por fecha y por kilometraje).
2. **Derechos y permisos**: tenencia, refrendo, verificación, tarjeta de
   circulación, placas, seguro (terminología de México).
3. **Licencias de conductores** y su vigencia.

El corazón de la herramienta es el comando **`alertas`**: un tablero que te dice,
de un vistazo, qué está vencido o por vencer en toda la flota.

Está escrita en **Python + SQLite** sin dependencias externas (solo la librería
estándar), y con la lógica separada de la interfaz para poder **migrarla a una
app web** más adelante reutilizando la base de datos y el código de negocio.

---

## Requisitos

- Python 3.10 o superior. No hay que instalar nada más.

## Puesta en marcha

```bash
# 1. Crear la base de datos
python gv.py init

# 2. (Opcional) Cargar datos de ejemplo: 6 sucursales con su flota
python gv.py seed

# 3. Ver el tablero de alertas
python gv.py alertas
```

La base de datos se guarda por defecto en `~/gestion_vehicular.db`. Se puede
cambiar con la variable de entorno `GV_DB` o con la opción `--db`:

```bash
python gv.py --db ./flota.db alertas
GV_DB=/ruta/a/flota.db python gv.py alertas
```

> Todos los comandos aceptan `--help`, por ejemplo `python gv.py vehiculo add --help`.

---

## Uso diario

### Sucursales

```bash
python gv.py sucursal add "Guadalajara" --ciudad Guadalajara --estado Jalisco \
    --responsable "Carlos Ruiz" --telefono 33-1000-0002
python gv.py sucursal list
```

### Vehículos

```bash
# tipo: sedan | hatchback | pickup
python gv.py vehiculo add --sucursal 2 --tipo pickup --marca Ford --modelo Ranger \
    --anio 2022 --placas "DEF-22-01" --km 45000
python gv.py vehiculo list
python gv.py vehiculo list --sucursal 2
python gv.py vehiculo km --id 4 --km 48200      # actualizar odómetro
```

### Conductores y licencias

```bash
python gv.py conductor add "Fernanda López" --sucursal 2 --licencia LIC-JAL-0022 \
    --tipo B --vigencia 2027-03-15
python gv.py conductor list
```

### Mantenimientos

```bash
python gv.py mantenimiento add --vehiculo 4 --tipo cambio_aceite --km 48000 \
    --costo 1800 --taller "Ford GDL" --proximo-km 58000 --proximo-fecha 2026-12-01
python gv.py mantenimiento list --vehiculo 4
```

Al registrar un mantenimiento podés indicar el **próximo servicio** por fecha
(`--proximo-fecha`) y/o por kilometraje (`--proximo-km`). Eso es lo que alimenta
las alertas.

### Derechos, permisos y licencias (obligaciones)

```bash
# Sobre un vehículo (tenencia, verificacion, refrendo, seguro, placas, ...)
python gv.py obligacion add --tipo tenencia --vehiculo 4 --vencimiento 2026-07-20 \
    --monto 5200 --periodo 2026

# Sobre un conductor (renovación de licencia)
python gv.py obligacion add --tipo licencia --conductor 2 --vencimiento 2027-03-15

python gv.py obligacion list                 # todas
python gv.py obligacion list --pendientes    # solo las no pagadas
python gv.py obligacion pagar --id 3         # marcar como pagada (fecha = hoy)
```

### Tablero de alertas

```bash
python gv.py alertas                          # horizonte 30 días / 1000 km
python gv.py alertas --dias 60 --umbral-km 2000
```

Muestra tres bloques, ordenados por urgencia: obligaciones (derechos, permisos y
licencias) pendientes vencidas o por vencer, mantenimientos próximos por fecha y
mantenimientos próximos por kilometraje.

---

## Estructura del proyecto

```
gv.py                       Punto de entrada (python gv.py ...)
gestion_vehicular/
├── db.py                   Conexión y esquema SQLite (toda la persistencia)
├── repositorio.py          Acceso a datos + lógica de negocio (reutilizable)
├── alertas   (en repositorio.calcular_alertas)
├── catalogos.py            Terminología de México (editable)
├── cli.py                  Interfaz de línea de comandos (presentación)
├── formato.py              Formato de tablas y montos
└── seed.py                 Datos de ejemplo
```

La separación en capas es intencional: `db.py` y `repositorio.py` no imprimen ni
saben de la consola, así que el día que quieras una **app web** (por ejemplo con
Flask o FastAPI) reutilizás esos módulos y la misma base de datos, y solo
reemplazás `cli.py` por las vistas web.

## Adaptar la terminología

Los tipos de obligación y de mantenimiento sugeridos están en
`gestion_vehicular/catalogos.py`. Los campos "tipo" aceptan cualquier texto, así
que podés usar tus propias categorías; editá ese archivo para que la ayuda y los
datos de ejemplo reflejen tu operación.
