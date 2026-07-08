"""Envío de alertas por correo electrónico.

Usa únicamente la librería estándar (``smtplib``). La configuración se toma de
variables de entorno para no dejar credenciales en el código ni en la base de
datos:

    GV_SMTP_HOST   servidor SMTP (ej. smtp.gmail.com)          [obligatorio]
    GV_SMTP_PORT   puerto (default 587)
    GV_SMTP_USER   usuario / cuenta
    GV_SMTP_PASS   contraseña o "app password"
    GV_SMTP_FROM   remitente (default = GV_SMTP_USER)
    GV_SMTP_TO     destinatarios, separados por coma           [obligatorio]
    GV_SMTP_TLS    "1" para STARTTLS (default), "0" para desactivar
    GV_SMTP_SSL    "1" para usar SSL directo (puerto 465)

Ejemplo (Gmail con contraseña de aplicación):

    export GV_SMTP_HOST=smtp.gmail.com
    export GV_SMTP_USER=flota@empresa.com
    export GV_SMTP_PASS=xxxx-xxxx-xxxx-xxxx
    export GV_SMTP_TO="gerencia@empresa.com, tu-correo@empresa.com"
    python gv.py alertas --email
"""

from __future__ import annotations

import os
import smtplib
from datetime import date
from email.message import EmailMessage


class CorreoNoConfigurado(RuntimeError):
    """Falta configuración obligatoria (host o destinatarios)."""


def configurado() -> bool:
    """True si hay suficiente configuración SMTP como para intentar un envío."""
    try:
        _config()
        return True
    except CorreoNoConfigurado:
        return False


def _config() -> dict:
    host = os.environ.get("GV_SMTP_HOST")
    destinatarios = [d.strip() for d in os.environ.get("GV_SMTP_TO", "").split(",") if d.strip()]
    if not host or not destinatarios:
        raise CorreoNoConfigurado(
            "Definí al menos GV_SMTP_HOST y GV_SMTP_TO. "
            "Ver 'python -c \"import gestion_vehicular.correo as c; help(c)\"'."
        )
    usuario = os.environ.get("GV_SMTP_USER")
    return {
        "host": host,
        "port": int(os.environ.get("GV_SMTP_PORT", "587")),
        "user": usuario,
        "password": os.environ.get("GV_SMTP_PASS"),
        "from": os.environ.get("GV_SMTP_FROM") or usuario or "gestion-vehicular@localhost",
        "to": destinatarios,
        "tls": os.environ.get("GV_SMTP_TLS", "1") != "0",
        "ssl": os.environ.get("GV_SMTP_SSL", "0") == "1",
    }


def enviar_alertas(cuerpo_texto: str, cantidad: int, cuerpo_html: str | None = None,
                   asunto: str | None = None) -> list[str]:
    """Envía el tablero de alertas por correo. Devuelve la lista de destinatarios.

    Si se pasa ``cuerpo_html``, el correo se manda como multipart/alternative:
    los clientes que muestran HTML ven la versión con colores por urgencia, y
    el resto cae de vuelta al texto plano.

    Lanza :class:`CorreoNoConfigurado` si falta configuración, o los errores de
    ``smtplib`` si el envío falla.
    """
    cfg = _config()
    mensaje = EmailMessage()
    mensaje["Subject"] = asunto or (
        f"[Flota] {cantidad} vencimiento(s) por atender — {date.today().isoformat()}"
    )
    mensaje["From"] = cfg["from"]
    mensaje["To"] = ", ".join(cfg["to"])
    mensaje.set_content(cuerpo_texto)
    if cuerpo_html:
        mensaje.add_alternative(cuerpo_html, subtype="html")

    _enviar_mensaje(cfg, mensaje)
    return cfg["to"]


def enviar_prueba() -> list[str]:
    """Envía un correo de prueba para verificar que la configuración SMTP funciona.

    Es el equivalente, en línea de comandos, a un botón de "enviar correo de
    prueba": no toca la base de datos, solo confirma que el host, el usuario,
    la contraseña y los destinatarios están bien. Devuelve la lista de
    destinatarios si el envío fue exitoso.
    """
    cfg = _config()
    mensaje = EmailMessage()
    mensaje["Subject"] = "[Flota] Correo de prueba — configuración SMTP correcta"
    mensaje["From"] = cfg["from"]
    mensaje["To"] = ", ".join(cfg["to"])
    mensaje.set_content(
        "Este es un correo de prueba del sistema de Gestión Vehicular.\n\n"
        "Si lo recibiste, la configuración SMTP quedó lista:\n"
        f"  Servidor:      {cfg['host']}:{cfg['port']}\n"
        f"  Remitente:     {cfg['from']}\n"
        f"  Destinatarios: {', '.join(cfg['to'])}\n"
    )
    mensaje.add_alternative(
        f"""\
<!doctype html>
<html><body style="font-family:Arial,Helvetica,sans-serif;color:#1f2937;">
  <h2 style="color:#166534;">✓ Correo de prueba</h2>
  <p>Este es un correo de prueba del sistema de <strong>Gestión Vehicular</strong>.</p>
  <p>Si lo recibiste, la configuración SMTP quedó lista:</p>
  <ul>
    <li><strong>Servidor:</strong> {cfg['host']}:{cfg['port']}</li>
    <li><strong>Remitente:</strong> {cfg['from']}</li>
    <li><strong>Destinatarios:</strong> {', '.join(cfg['to'])}</li>
  </ul>
</body></html>
""",
        subtype="html",
    )

    _enviar_mensaje(cfg, mensaje)
    return cfg["to"]


def _enviar_mensaje(cfg: dict, mensaje: EmailMessage) -> None:
    if cfg["ssl"]:
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"]) as s:
            _login_y_enviar(s, cfg, mensaje)
    else:
        with smtplib.SMTP(cfg["host"], cfg["port"]) as s:
            if cfg["tls"]:
                s.starttls()
            _login_y_enviar(s, cfg, mensaje)


def _login_y_enviar(servidor, cfg, mensaje) -> None:
    if cfg["user"] and cfg["password"]:
        servidor.login(cfg["user"], cfg["password"])
    servidor.send_message(mensaje)
