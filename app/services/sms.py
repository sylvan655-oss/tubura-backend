"""
SMS via Africa's Talking. If AT_USERNAME / AT_API_KEY are not configured,
messages are printed to the server log instead of sent — so development
and testing work without an SMS account.
"""
from app.core.config import settings

_at_sms = None
if settings.AT_USERNAME and settings.AT_API_KEY:
    try:
        import africastalking
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        _at_sms = africastalking.SMS
    except Exception as e:      # pragma: no cover
        print(f"[sms] Africa's Talking init failed: {e}")


def send_sms(phone: str, message: str) -> None:
    if _at_sms is None:
        print(f"[sms:DEV] to {phone}: {message}")
        return
    try:
        kwargs = {}
        if settings.AT_SENDER:
            kwargs["sender_id"] = settings.AT_SENDER
        _at_sms.send(message, [phone], **kwargs)
    except Exception as e:
        # Never let SMS failure break an order or signup
        print(f"[sms] send failed to {phone}: {e}")
