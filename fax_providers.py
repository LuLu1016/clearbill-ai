"""Fax provider abstraction for ClearBill AI.

The app talks only to `get_provider()` and `FaxProvider.send()` -- swapping
fax vendors means adding one subclass here, nothing changes in app.py.

Configuration is entirely via environment variables (see .env.example):
  FAX_PROVIDER  -- which backend to use: "documo", "notifyre", or "dryrun"
  FAX_API_KEY   -- the provider's API key (not needed for dryrun)

The "dryrun" provider writes the PDF to ./outbox/ instead of faxing it, so
the whole flow can be exercised with no account and no risk of faxing a real
hospital during testing.
"""

import base64
import os
import pathlib
import time

import requests


class FaxError(Exception):
    """Fax could not be sent. The message is safe to show to the user."""


class FaxProvider:
    name = "base"

    def send(self, pdf_bytes: bytes, to_number: str) -> dict:
        """Send a PDF to a fax number. Returns provider metadata (id, etc.).
        Raises FaxError with a user-facing message on failure."""
        raise NotImplementedError


class DryRunProvider(FaxProvider):
    """Writes the PDF to ./outbox/ and reports success. For local testing --
    never sends anything anywhere."""

    name = "dryrun"

    def send(self, pdf_bytes: bytes, to_number: str) -> dict:
        outbox = pathlib.Path(__file__).parent / "outbox"
        outbox.mkdir(exist_ok=True)
        path = outbox / f"fax-{int(time.time())}-{to_number.lstrip('+')}.pdf"
        path.write_bytes(pdf_bytes)
        return {"id": path.name, "detail": f"Dry run: PDF written to {path}, nothing was faxed."}


class DocumoProvider(FaxProvider):
    """Documo / mFax -- https://docs.documo.com. Verify the endpoint/fields
    against their current docs when the account is created; this was written
    from documentation, not against a live account."""

    name = "documo"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def send(self, pdf_bytes: bytes, to_number: str) -> dict:
        resp = requests.post(
            "https://api.documo.com/v1/faxes",
            headers={"Authorization": f"Basic {self.api_key}"},
            data={"faxNumber": to_number, "subject": "Billing dispute letter"},
            files={"attachments": ("dispute_letter.pdf", pdf_bytes, "application/pdf")},
            timeout=60,
        )
        if resp.status_code >= 400:
            raise FaxError(f"Documo rejected the fax (HTTP {resp.status_code}): {resp.text[:300]}")
        body = resp.json()
        return {"id": body.get("messageId") or body.get("id"), "detail": "Queued with Documo."}


class NotifyreProvider(FaxProvider):
    """Notifyre -- https://docs.notifyre.com. Same caveat as Documo: confirm
    payload shape against current docs once there's a real account."""

    name = "notifyre"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def send(self, pdf_bytes: bytes, to_number: str) -> dict:
        resp = requests.post(
            "https://api.notifyre.com/fax/send",
            headers={"x-api-token": self.api_key, "Content-Type": "application/json"},
            json={
                "Faxes": {
                    "Recipients": [{"Type": "fax_number", "Value": to_number}],
                    "SendFrom": "",
                    "Documents": [
                        {
                            "Filename": "dispute_letter.pdf",
                            "Data": base64.b64encode(pdf_bytes).decode(),
                        }
                    ],
                }
            },
            timeout=60,
        )
        if resp.status_code >= 400:
            raise FaxError(f"Notifyre rejected the fax (HTTP {resp.status_code}): {resp.text[:300]}")
        body = resp.json()
        payload = body.get("payload") or {}
        return {"id": payload.get("faxID") or payload.get("id"), "detail": "Queued with Notifyre."}


_PROVIDERS = {
    DryRunProvider.name: DryRunProvider,
    DocumoProvider.name: DocumoProvider,
    NotifyreProvider.name: NotifyreProvider,
}


def get_provider() -> FaxProvider:
    """Build the configured provider from environment variables."""
    kind = os.environ.get("FAX_PROVIDER", "").strip().lower()
    if not kind:
        raise FaxError(
            "No fax provider is configured. Set FAX_PROVIDER in .env to one of: "
            + ", ".join(sorted(_PROVIDERS))
            + " (and FAX_API_KEY for real providers). Use FAX_PROVIDER=dryrun to "
            "test the flow without sending anything."
        )
    cls = _PROVIDERS.get(kind)
    if cls is None:
        raise FaxError(
            f"Unknown FAX_PROVIDER '{kind}'. Supported: " + ", ".join(sorted(_PROVIDERS))
        )
    if cls is DryRunProvider:
        return cls()
    api_key = os.environ.get("FAX_API_KEY", "").strip()
    if not api_key:
        raise FaxError(f"FAX_PROVIDER is '{kind}' but FAX_API_KEY is not set in .env.")
    return cls(api_key)
