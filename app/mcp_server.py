"""WhatsApp Cloud API MCP Server."""

from __future__ import annotations

from typing import Optional

from fastmcp import FastMCP
from pydantic import Field
from starlette.applications import Starlette
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from app.services.whatsapp_service import WhatsAppError, WhatsAppService
from app.capability_bind import bind_declared_capabilities

mcp = FastMCP(
    name="whatsapp",
    instructions="WhatsApp Cloud API. Vault bundle is access_token + phone_number_id. Sends require confirm=true.",
)

_CREDS_JSON = Field(default=None, description="Token bundle JSON from Studio vault inject")
_CREDS_PATH = Field(default=None, description="Local credentials JSON path")


def _creds_required() -> dict:
    return {
        "error_code": "CREDENTIALS_REQUIRED",
        "error_message": "Provide credentials_path or credentials_json",
        "retryable": False,
        "original_provider_error": None,
    }


def _confirm_required() -> dict:
    return {
        "error_code": "CONFIRM_REQUIRED",
        "error_message": "Set confirm=true to execute this side-effecting tool",
        "retryable": False,
        "original_provider_error": None,
    }


@mcp.tool()
def whatsapp_send_text(
    to: str = Field(..., description="Recipient phone in international format"),
    body: str = Field(..., description="Session text body", json_schema_extra={"x-datumbridge-encoding": "plain"}),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    confirm: bool = Field(default=False),
    dry_run: bool = Field(default=False),
) -> dict:
    """Send a WhatsApp session text message. Requires confirm=true.

        Capabilities: whatsapp.whatsapp_send_text
Outputs: success
        """
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        if dry_run:
            return {"success": True, "dry_run": True, "message": "Would send text", "to": to}
        if not confirm:
            return {"success": False, "error": _confirm_required()}
        result = WhatsAppService(credentials_json, credentials_path).send_text(to, body)
        return {"success": True, "message": "Sent", "result": result}
    except WhatsAppError as e:
        return {"success": False, "error": e.to_dict()}


@mcp.tool()
def whatsapp_send_template(
    to: str = Field(..., description="Recipient phone in international format"),
    template_name: str = Field(..., description="Approved template name"),
    language: str = Field(default="en_US"),
    credentials_path: Optional[str] = _CREDS_PATH,
    credentials_json: Optional[str] = _CREDS_JSON,
    confirm: bool = Field(default=False),
    dry_run: bool = Field(default=False),
) -> dict:
    """Send a WhatsApp template message. Requires confirm=true.

        Capabilities: whatsapp.whatsapp_send_template
Outputs: success
        """
    try:
        if not credentials_path and not credentials_json:
            return {"success": False, "error": _creds_required()}
        if dry_run:
            return {"success": True, "dry_run": True, "message": "Would send template", "to": to}
        if not confirm:
            return {"success": False, "error": _confirm_required()}
        result = WhatsAppService(credentials_json, credentials_path).send_template(
            to, template_name, language
        )
        return {"success": True, "message": "Sent", "result": result}
    except WhatsAppError as e:
        return {"success": False, "error": e.to_dict()}



bind_declared_capabilities(mcp)

_base_app = mcp.http_app()


async def health(_request):
    return JSONResponse({"status": "ok", "service": "whatsapp-mcp"})


http_app = Starlette(
    routes=[Route("/health", health), Mount("/", _base_app)],
    lifespan=getattr(_base_app, "lifespan", None),
)

if __name__ == "__main__":
    mcp.run()
