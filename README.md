# WhatsApp MCP

WhatsApp Cloud API tool-server. Tools: send session text, send template.

**Publish name:** `WhatsApp MCP` (k8s host `whatsapp-mcp-main`).

**Auth:** Studio **Account → Integrations** saves a token bundle (`access_token` + `phone_number_id`), not a Google-style login. Treat tokens like Trello secrets. Sends require `confirm=true`.
