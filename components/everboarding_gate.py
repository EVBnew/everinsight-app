import json
import urllib.parse
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple

import streamlit as st


# =============================
# Helpers HTTP
# =============================
def _get_json(url: str, params: Dict[str, Any], timeout: int = 8) -> Tuple[bool, Dict[str, Any]]:
    try:
        qs = urllib.parse.urlencode({k: v for k, v in params.items() if v is not None})
        full_url = f"{url}?{qs}" if qs else url
        req = urllib.request.Request(full_url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return True, json.loads(body) if body else {}
            except Exception:
                return True, {"raw": body}
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return False, {"http_error": str(e), "body": body}
    except Exception as e:
        return False, {"error": str(e)}


def _post_json(url: str, payload: Dict[str, Any], timeout: int = 8) -> Tuple[bool, Dict[str, Any]]:
    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url=url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            try:
                return True, json.loads(body) if body else {}
            except Exception:
                return True, {"raw": body}
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", errors="replace")
        except Exception:
            body = ""
        return False, {"http_error": str(e), "body": body}
    except Exception as e:
        return False, {"error": str(e)}


# =============================
# Public API
# =============================
def get_token_from_url() -> str:
    """
    Read token from URL query params.
    Compatible with Streamlit new query_params API.
    """
    try:
        qp = st.query_params
        tok = qp.get("token", "")
        if isinstance(tok, list):
            tok = tok[0] if tok else ""
        return (tok or "").strip()
    except Exception:
        # fallback old API
        qp = st.experimental_get_query_params()
        tok = (qp.get("token", [""])[0] or "").strip()
        return tok


def validate_token_via_webhook(token: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate token against Apps Script doGet(?token=...).

    Expects secret:
      - ACCESS_WEBHOOK_URL  (your Apps Script /exec URL)
    Returns:
      (ok, resp_dict)
      ok=True only if resp.ok==True AND resp.status == "approved"
    """
    url = (st.secrets.get("ACCESS_WEBHOOK_URL") or "").strip()
    if not url:
        return False, {"ok": False, "error": "Missing secret ACCESS_WEBHOOK_URL"}

    ok_http, resp = _get_json(url, {"token": token}, timeout=8)
    if not ok_http:
        return False, resp

    approved = bool(resp.get("ok")) and str(resp.get("status", "")).strip().lower() == "approved"
    return approved, resp


def log_event_via_webhook(
    email: str,
    event: str,
    page: str = "",
    payload: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Fire-and-forget logging to Apps Script doPost with action="log_event".

    Expects secret:
      - ACCESS_WEBHOOK_URL  (Apps Script /exec URL)
    """
    url = (st.secrets.get("ACCESS_WEBHOOK_URL") or "").strip()
    if not url:
        return

    email_norm = (email or "").strip().lower()
    if not email_norm:
        return

    # Best effort user-agent (Streamlit context is not always available)
    ua = ""
    try:
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            ua = st.context.headers.get("user-agent", "") or ""
    except Exception:
        ua = ""

    _post_json(
        url,
        {
            "action": "log_event",
            "email": email_norm,
            "event": event,
            "page": page,
            "payload": payload or {},
            "ua": ua,
        },
        timeout=5,
    )
