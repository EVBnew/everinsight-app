import json
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, Tuple

import streamlit as st


def _post_json(url: str, payload: Dict[str, Any], timeout: int = 12) -> Tuple[bool, Dict[str, Any]]:
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


def get_token_from_url() -> str:
    qp = st.query_params
    tok = qp.get("token", "")
    if isinstance(tok, list):
        tok = tok[0] if tok else ""
    return (tok or "").strip()


def deny_access(portal_url: str, title: str = "Accès requis", msg: str = "") -> None:
    st.warning("🔒 Accès restreint")
    st.subheader(title)
    if msg:
        st.write(msg)
    st.link_button("👉 Demander un accès", portal_url)
    st.stop()


def validate_token_via_webhook(token: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Calls Apps Script / webhook to validate token against sheet.
    Expects secrets:
      - ACCESS_WEBHOOK_URL
      - ACCESS_WEBHOOK_SECRET (optional but recommended)
    """
    url = (st.secrets.get("ACCESS_WEBHOOK_URL") or "").strip()
    if not url:
        return False, {"error": "Missing secret ACCESS_WEBHOOK_URL"}

    secret = (st.secrets.get("ACCESS_WEBHOOK_SECRET") or "").strip()

    ok, resp = _post_json(url, {"action": "validate_token", "token": token, "secret": secret})
    if not ok:
        return False, resp

    if resp.get("ok") is True and resp.get("status") == "approved":
        return True, resp
    return False, resp


def log_event_via_webhook(email: str, event: str, page: str = "", payload: Optional[Dict[str, Any]] = None) -> None:
    url = (st.secrets.get("ACCESS_WEBHOOK_URL") or "").strip()
    if not url:
        return

    secret = (st.secrets.get("ACCESS_WEBHOOK_SECRET") or "").strip()
    ua = st.context.headers.get("user-agent", "") if hasattr(st, "context") else ""

    _post_json(
        url,
        {
            "action": "event",
            "secret": secret,
            "email": (email or "").strip().lower(),
            "event": event,
            "page": page,
            "payload": payload or {},
            "ua": ua,
        },
        timeout=6,
    )


def enforce_access(portal_url: str, page_name: str = "") -> Dict[str, str]:
    """
    HARD RULE:
    - No token in URL => always deny
    - Token must validate to 'approved'
    Returns: {"email": "..."} (approved email)
    """
    token = get_token_from_url()

    if not token:
        deny_access(
            portal_url=portal_url,
            title="Accès requis",
            msg="Pour tester l’application, l’accès se fait via EVERBOARDING (invitation / freemium).",
        )

    # Always validate on each page load (simple & safe)
    with st.spinner("Vérification de l’accès..."):
        ok, resp = validate_token_via_webhook(token)

    if not ok:
        deny_access(
            portal_url=portal_url,
            title="Lien non valide",
            msg="Le lien est invalide, expiré, ou non approuvé.",
        )

    email = (resp.get("email") or "").strip().lower()

    # Log once per session per page
    key = f"logged_open__{page_name or 'unknown'}"
    if key not in st.session_state:
        log_event_via_webhook(
            email=email,
            event="app_open",
            page=page_name or "",
            payload={"token_present": True},
        )
        st.session_state[key] = True

    return {"email": email}
