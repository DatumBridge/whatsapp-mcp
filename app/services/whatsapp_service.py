"""WhatsApp Cloud API client. Token bundle from Studio vault."""

from __future__ import annotations

import json
from typing import Any, Optional

import requests

GRAPH_BASE = "https://graph.facebook.com/v21.0"


class WhatsAppError(Exception):
    def __init__(self, message: str, error_code: str = "WHATSAPP_ERROR", retryable: bool = False):
        super().__init__(message)
        self.error_code = error_code
        self.retryable = retryable

    def to_dict(self) -> dict:
        return {
            "error_code": self.error_code,
            "error_message": str(self),
            "retryable": self.retryable,
            "original_provider_error": None,
        }


def _bundle(credentials_json: Optional[str], credentials_path: Optional[str]) -> dict[str, str]:
    data: dict[str, Any] = {}
    if credentials_json:
        data = json.loads(credentials_json)
    elif credentials_path:
        with open(credentials_path, encoding="utf-8") as fh:
            data = json.load(fh)
    token = (data.get("access_token") or data.get("token") or "").strip()
    phone_id = (data.get("phone_number_id") or "").strip()
    if not token or not phone_id:
        raise WhatsAppError(
            "Credentials required: access_token and phone_number_id",
            error_code="CREDENTIALS_REQUIRED",
        )
    return {
        "access_token": token,
        "phone_number_id": phone_id,
        "business_account_id": str(data.get("business_account_id") or "").strip(),
    }


class WhatsAppService:
    def __init__(
        self,
        credentials_json: Optional[str] = None,
        credentials_path: Optional[str] = None,
    ):
        self._creds = _bundle(credentials_json, credentials_path)

    def send_text(self, to: str, body: str) -> dict:
        url = f"{GRAPH_BASE}/{self._creds['phone_number_id']}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body},
        }
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {self._creds['access_token']}"},
            json=payload,
            timeout=30,
        )
        if resp.status_code >= 400:
            raise WhatsAppError(
                f"WhatsApp API {resp.status_code}: {resp.text[:300]}",
                retryable=resp.status_code >= 500,
            )
        return resp.json()

    def send_template(self, to: str, template_name: str, language: str = "en_US") -> dict:
        url = f"{GRAPH_BASE}/{self._creds['phone_number_id']}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {"name": template_name, "language": {"code": language}},
        }
        resp = requests.post(
            url,
            headers={"Authorization": f"Bearer {self._creds['access_token']}"},
            json=payload,
            timeout=30,
        )
        if resp.status_code >= 400:
            raise WhatsAppError(
                f"WhatsApp API {resp.status_code}: {resp.text[:300]}",
                retryable=resp.status_code >= 500,
            )
        return resp.json()
