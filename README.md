# Gestión Vehicular

Herramienta de línea de comandos para gestionar, sobre una flota distribuida en
varias sucursales, tres cosas:

1. **Mantenimientos** de cada vehículo (por fecha y por kilometraje), tanto de
   combustión/híbridos como **eléctricos**.
2. **Derechos y permisos**: tenencia, refrendo, verificación, tarjeta de
   circulación, placas, seguro (terminología de México).
3. **Licencias de conductores** y su vigencia.

El corazón de la herramienta es el comando **`alertas`**: un tablero que te dice,
de un vistazo, qué está vencido o por vencer en toda la flota, y que además
puede **enviarse por correo**. La información se puede **exportar a CSV separada
por rubro**.

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

# 2. (Opcional) Cargar datos de ejemplo: 6 sucursales + Corporativo (con eléctricos)
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
# tipo:    sedan | hatchback | pickup
# energia: combustion (default) | hibrido | electrico
python gv.py vehiculo add --sucursal 2 --tipo pickup --marca Ford --modelo Ranger \
    --anio 2022 --placas "DEF-22-01" --km 45000
python gv.py vehiculo add --sucursal 7 --tipo pickup --marca Ford \
    --modelo "F-150 Lightning" --energia electrico --placas "COR-00-02"
python gv.py vehiculo list
python gv.py vehiculo list --sucursal 2
python gv.py vehiculo km --id 4 --km 48200      # actualizar odómetro
```

La **energía** (combustión / híbrido / eléctrico) es independiente del tipo de
carrocería, porque el mantenimiento cambia. Hoy los eléctricos viven solo en el
Corporativo, pero el sistema ya los soporta: al registrar un mantenimiento podés
usar tipos propios de EV (`bateria_hv`, `refrigerante_bateria`, `software`,
`frenos_regenerativos`, `cargador_puerto`, `motor_inversor`, …). Ver la lista
completa por energía en `gestion_vehicular/catalogos.py`.

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

### Alertas por correo

El mismo tablero se puede enviar por correo. La configuración va en **variables
de entorno** (no se guardan credenciales en el código ni en la base):

```bash
export GV_SMTP_HOST=smtp.gmail.com
export GV_SMTP_USER=flota@empresa.com
export GV_SMTP_PASS=xxxx-xxxx-xxxx-xxxx      # contraseña de aplicación
export GV_SMTP_TO="gerencia@empresa.com, tu-correo@empresa.com"

python gv.py alertas --email          # imprime y además envía
python gv.py alertas --solo-email     # solo envía (ideal para tareas programadas)
```

Variables disponibles: `GV_SMTP_HOST` (obligatoria), `GV_SMTP_TO` (obligatoria),
`GV_SMTP_PORT` (587), `GV_SMTP_USER`, `GV_SMTP_PASS`, `GV_SMTP_FROM`,
`GV_SMTP_TLS` (1), `GV_SMTP_SSL` (0). Detalle completo en
`gestion_vehicular/correo.py`.

Para recibir el aviso automáticamente (por ejemplo, todos los lunes a las 8:00),
se puede programar con `cron` en Linux/Mac:

```cron
0 8 * * 1  cd /ruta/al/proyecto && /usr/bin/python3 gv.py alertas --solo-email
```

### Exportar por rubro

La información se exporta a CSV (se abre en Excel), **cada rubro en su propio
archivo** para no mezclar mantenimientos con permisos:

```bash
python gv.py exportar --rubro todo --dir ./exportes     # un archivo por rubro
python gv.py exportar --rubro mantenimientos --salida mantenimientos.csv
python gv.py exportar --rubro permisos                  # derechos/permisos de vehículos
python gv.py exportar --rubro licencias                 # licencias de conductores
```

Rubros: `sucursales`, `vehiculos`, `conductores`, `mantenimientos`, `permisos`
(obligaciones de vehículos), `licencias` (obligaciones de conductores).

---

## Estructura del proyecto

```
gv.py                       Punto de entrada (python gv.py ...)
gestion_vehicular/
├── db.py                   Conexión, esquema SQLite y migraciones
├── repositorio.py          Acceso a datos + lógica de negocio (reutilizable)
│                           (incluye calcular_alertas)
├── catalogos.py            Terminología de México y tipos de mantenimiento (editable)
├── correo.py               Envío de alertas por correo (SMTP)
├── exportar.py             Exportación a CSV por rubro
├── cli.py                  Interfaz de línea de comandos (presentación)
├── formato.py              Formato de tablas, montos y render del tablero
└── seed.py                 Datos de ejemplo (incluye flota eléctrica del Corporativo)
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
