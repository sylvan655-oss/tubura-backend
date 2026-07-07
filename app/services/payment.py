"""
Mobile-money payment collection services.

Both providers use a "request-to-pay" pattern: the API call pushes a USSD
prompt to the payer's phone, and the actual payment confirmation arrives
later via a webhook (see app/api/routes/orders.py `/payments/*/callback`).

When credentials are not configured (local/dev), these functions log the
request and return a fake success so the rest of the checkout flow can be
exercised end-to-end without live provider accounts.
"""
import logging
import uuid
from typing import Optional

import httpx

from app.core.config import settings

logger = logging.getLogger("tubura.payment")


def _dev_mode(*keys: str) -> bool:
    return not all(keys)


async def request_mtn_momo_payment(phone: str, amount: float, order_ref: str) -> dict:
    if _dev_mode(settings.MTN_MOMO_SUBSCRIPTION_KEY, settings.MTN_MOMO_API_USER, settings.MTN_MOMO_API_KEY):
        logger.info("[MTN-MOMO:DEV-MODE] push %.2f RWF to %s for order %s", amount, phone, order_ref)
        return {"status": "pending", "reference_id": str(uuid.uuid4()), "dev_mode": True}

    reference_id = str(uuid.uuid4())
    url = f"{settings.MTN_MOMO_BASE_URL}/collection/v1_0/requesttopay"
    headers = {
        "X-Reference-Id": reference_id,
        "X-Target-Environment": settings.MTN_MOMO_ENVIRONMENT,
        "Ocp-Apim-Subscription-Key": settings.MTN_MOMO_SUBSCRIPTION_KEY,
        "Authorization": f"Bearer {settings.MTN_MOMO_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "amount": str(amount),
        "currency": "RWF",
        "externalId": order_ref,
        "payer": {"partyIdType": "MSISDN", "partyId": phone.replace("+", "")},
        "payerMessage": f"Tubura order {order_ref}",
        "payeeNote": f"Tubura order {order_ref}",
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
        return {"status": "pending", "reference_id": reference_id, "dev_mode": False}
    except Exception as e:  # pragma: no cover
        logger.error("MTN MoMo request failed: %s", e)
        return {"status": "failed", "reference_id": reference_id, "error": str(e)}


async def request_airtel_money_payment(phone: str, amount: float, order_ref: str) -> dict:
    if _dev_mode(settings.AIRTEL_CLIENT_ID, settings.AIRTEL_CLIENT_SECRET):
        logger.info("[AIRTEL-MONEY:DEV-MODE] push %.2f RWF to %s for order %s", amount, phone, order_ref)
        return {"status": "pending", "reference_id": str(uuid.uuid4()), "dev_mode": True}

    reference_id = str(uuid.uuid4())
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            token_resp = await client.post(
                f"{settings.AIRTEL_BASE_URL}/auth/oauth2/token",
                json={
                    "client_id": settings.AIRTEL_CLIENT_ID,
                    "client_secret": settings.AIRTEL_CLIENT_SECRET,
                    "grant_type": "client_credentials",
                },
            )
            token_resp.raise_for_status()
            access_token = token_resp.json().get("access_token")

            headers = {
                "Authorization": f"Bearer {access_token}",
                "X-Country": "RW",
                "X-Currency": "RWF",
                "Content-Type": "application/json",
            }
            payload = {
                "reference": order_ref,
                "subscriber": {"country": "RW", "currency": "RWF", "msisdn": phone.replace("+250", "")},
                "transaction": {"amount": amount, "country": "RW", "currency": "RWF", "id": reference_id},
            }
            pay_resp = await client.post(
                f"{settings.AIRTEL_BASE_URL}/merchant/v1/payments/", json=payload, headers=headers
            )
            pay_resp.raise_for_status()
        return {"status": "pending", "reference_id": reference_id, "dev_mode": False}
    except Exception as e:  # pragma: no cover
        logger.error("Airtel Money request failed: %s", e)
        return {"status": "failed", "reference_id": reference_id, "error": str(e)}


async def request_payment(method: str, phone: str, amount: float, order_ref: str) -> Optional[dict]:
    if method == "mtn_momo":
        return await request_mtn_momo_payment(phone, amount, order_ref)
    if method == "airtel":
        return await request_airtel_money_payment(phone, amount, order_ref)
    # card / other: no push-payment needed, assume handled client-side or externally
    return {"status": "not_applicable"}
