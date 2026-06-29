"""Manejo de sesiones - version correcta (sin token en logs)."""
import logging

logger = logging.getLogger(__name__)


def handle_expired_session(session_token, user_id):
    if is_expired(session_token):
        # Correcto: logueamos el evento SIN el token
        logger.info("Sesion expirada para usuario %s, renovando", user_id)
        return refresh(session_token)
    return session_token


def is_expired(token):
    return False


def refresh(token):
    return token + "_renovado"
