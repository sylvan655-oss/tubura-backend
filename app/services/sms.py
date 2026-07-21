"""
SMS via Africa's Talking. If AT_USERNAME / AT_API_KEY are not configured,
messages are printed to the server log instead of sent — so development
and testing work without an SMS account.

Set on Railway (web service > Variables):
  AT_USERNAME  - the Africa's Talking APP username (not your email)
  AT_API_KEY   - the app's API key
  AT_SENDER    - optional; only after an alphanumeric sender ID is approved
"""
import re

from app.core.config import settings

_at_sms = None
if settings.AT_USERNAME and settings.AT_API_KEY:
    try:
        import africastalking
        africastalking.initialize(settings.AT_USERNAME, settings.AT_API_KEY)
        _at_sms = africastalking.SMS
    except Exception as e:      # pragma: no cover
        print(f"[sms] Africa's Talking init failed: {e}")


def normalize_phone(phone: str) -> str | None:
    """
    Convert Rwandan numbers to international format (+2507XXXXXXXX),
    which Africa's Talking requires.
      '0788 123 456'   -> '+250788123456'
      '250788123456'   -> '+250788123456'
      '+250788123456'  -> '+250788123456' (unchanged)
      '788123456'      -> '+250788123456'
    Returns None if the number can't be a valid mobile number.
    """
    digits = re.sub(r"\D", "", phone or "")   # strip spaces, dashes, etc.
    if digits.startswith("250"):
        digits = digits[3:]
    if digits.startswith("0"):
        digits = digits[1:]
    # Rwandan mobiles: 9 digits starting with 7 (72/73/78/79...)
    if len(digits) == 9 and digits.startswith("7"):
        return "+250" + digits
    return None


def send_sms(phone: str, message: str) -> None:
    """Fire-and-forget: SMS failure must never break signup or orders."""
    to = normalize_phone(phone)
    if to is None:
        print(f"[sms] invalid phone, not sent: {phone!r}")
        return
    if _at_sms is None:
        print(f"[sms:DEV] to {to}: {message}")
        return
    try:
        kwargs = {}
        if settings.AT_SENDER:
            kwargs["sender_id"] = settings.AT_SENDER
        result = _at_sms.send(message, [to], **kwargs)
        # Log the delivery status AT reports (Success / InvalidPhoneNumber /
        # InsufficientBalance / ...) so problems show up in Railway logs.
        try:
            r = result["SMSMessageData"]["Recipients"][0]
            print(f"[sms] to {to}: {r.get('status')} (cost {r.get('cost')})")
        except Exception:
            print(f"[sms] to {to}: sent, unparsed response {result!r}")
    except Exception as e:
        print(f"[sms] send failed to {to}: {e}")
