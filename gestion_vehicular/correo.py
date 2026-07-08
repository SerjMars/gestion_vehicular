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


def enviar_alertas(cuerpo_texto: str, cantidad: int, asunto: str | None = None) -> list[str]:
    """Envía el tablero de alertas por correo. Devuelve la lista de destinatarios.

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

    if cfg["ssl"]:
        with smtplib.SMTP_SSL(cfg["host"], cfg["port"]) as s:
            _login_y_enviar(s, cfg, mensaje)
    else:
        with smtplib.SMTP(cfg["host"], cfg["port"]) as s:
            if cfg["tls"]:
                s.starttls()
            _login_y_enviar(s, cfg, mensaje)

    return cfg["to"]


def _login_y_enviar(servidor, cfg, mensaje) -> None:
    if cfg["user"] and cfg["password"]:
        servidor.login(cfg["user"], cfg["password"])
    servidor.send_message(mensaje)
