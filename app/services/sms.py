"""
SMS delivery via Africa's Talking.

Falls back to logging (no-op) when AT_API_KEY is not configured, so the rest
of the app works fine in local/dev environments without real credentials.
"""
import logging

from app.core.config import settings

logger = logging.getLogger("tubura.sms")

_gateway = None


def _get_gateway():
    global _gateway
    if _gateway is not None:
        return _gateway
    if not settings.AT_API_KEY:
        return None
    try:
        import africastalking

        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        _gateway = africastalking.SMS
        return _gateway
    except Exception as e:  # pragma: no cover
        logger.warning("Could not initialize Africa's Talking SDK: %s", e)
        return None


def send_sms(phone: str, message: str) -> bool:
    gateway = _get_gateway()
    if gateway is None:
        logger.info("[SMS:DEV-MODE] to=%s message=%s", phone, message)
        return True
    try:
        gateway.send(message, [phone], sender_id=settings.AT_SENDER_ID or None)
        return True
    except Exception as e:  # pragma: no cover
        logger.error("Failed to send SMS to %s: %s", phone, e)
        return False


def send_otp_sms(phone: str, code: str) -> bool:
    return send_sms(phone, f"Your Tubura verification code is {code}. It expires in "
                            f"{settings.OTP_EXPIRE_MINUTES} minutes.")


def send_order_update_sms(phone: str, order_ref: str, status: str) -> bool:
    return send_sms(phone, f"Tubura order #{order_ref} update: {status}.")
