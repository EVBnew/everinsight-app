import os
import json
import streamlit as st

from components.everboarding_gate import (
    get_token_from_url,
    validate_token_via_webhook,
    log_event_via_webhook,
)

# =============================
# STREAMLIT CONFIG (MUST BE FIRST)
# =============================
st.set_page_config(page_title="Bienvenue", page_icon="🏁", layout="wide")

# =============================
# CONFIG
# =============================
PORTAL_URL = (st.secrets.get("PORTAL_ACCESS_URL") or "https://everboarding.fr/everinsight").strip()
DEBUG = bool(st.secrets.get("DEBUG", False))

DATA_DIR = "Data"
PROFILE_PATH = os.path.join(DATA_DIR, "profil_apprenant.json")
os.makedirs(DATA_DIR, exist_ok=True)

# =============================
# HELPERS
# =============================
def load_profile() -> dict:
    if os.path.exists(PROFILE_PATH):
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_profile(profile: dict) -> None:
    with open(PROFILE_PATH, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

def normalize_email(raw: str) -> str:
    if raw is None:
        return ""
    return str(raw).replace("\u00A0", " ").strip().lower()

def deny_access(title: str, msg: str) -> None:
    st.warning("🔒 Accès restreint")
    st.subheader(title)
    st.write(msg)
    st.link_button("👉 Demander un accès", PORTAL_URL)
    st.stop()

# =============================
# ACCESS GATE
# =============================
token = get_token_from_url()

st.session_state.setdefault("access_granted", False)
st.session_state.setdefault("approved_email", "")
st.session_state.setdefault("logged_app_open", False)

if not st.session_state["access_granted"]:
    if not token:
        deny_access(
            title="Accès requis",
            msg="Pour tester l’application, l’accès se fait via EVERBOARDING (invitation / freemium).",
        )

    with st.spinner("Vérification de l’accès..."):
        ok, resp = validate_token_via_webhook(token)

    if not ok:
        deny_access(
            title="Lien non valide",
            msg="Le lien est invalide, expiré, ou non approuvé.",
        )

    # ✅ Access granted
    st.session_state["access_granted"] = True
    st.session_state["approved_email"] = normalize_email(resp.get("email") or "")

    # Log app_open once per session
    if not st.session_state["logged_app_open"]:
        log_event_via_webhook(
            email=st.session_state["approved_email"],
            event="app_open",
            page="accueil",
            payload={"token_present": True},
        )
        st.session_state["logged_app_open"] = True

# =============================
# UI
# =============================
st.title("Bienvenue dans EVERINSIGHT")
st.markdown("Renseigne tes infos une seule fois. Elles seront réutilisées dans toute l’app.")

profile = load_profile()
default_prenom = profile.get("prenom", "")
default_nom = profile.get("nom", "")

approved_email = st.session_state.get("approved_email", "").strip()
default_email = approved_email if approved_email else normalize_email(profile.get("email", ""))

with st.form("profil_form", clear_on_submit=False):
    prenom = st.text_input("Prénom", value=default_prenom)
    nom = st.text_input("Nom", value=default_nom)

    email_raw = st.text_input(
        "Email (identifiant apprenant)",
        value=default_email,
        disabled=bool(approved_email),
        help="Email verrouillé car associé à ton lien d’accès." if approved_email else None,
    )

    submitted = st.form_submit_button("💾 Enregistrer")

email = normalize_email(email_raw)

if DEBUG:
    with st.expander("Debug (temporaire)"):
        st.write("token_present =", bool(token))
        st.write("approved_email =", repr(approved_email))
        st.write("email_raw =", repr(email_raw))
        st.write("email_normalized =", repr(email))

if submitted:
    if not email:
        st.error(
            "L’email est obligatoire (identifiant apprenant).\n\n"
            "Astuce : clique dans le champ email et tape un caractère si ton navigateur l'a auto-rempli."
        )
        st.stop()

    # Safety: if approved_email exists, enforce exact match
    if approved_email and email != approved_email:
        st.error("Cet email ne correspond pas à l’email validé pour ce lien d’accès.")
        st.stop()

    save_profile({"prenom": prenom.strip(), "nom": nom.strip(), "email": email})
    st.success("Profil enregistré. Tu peux aller sur “Mon espace” / “Mon programme”.")

    log_event_via_webhook(
        email=email,
        event="profile_saved",
        page="accueil",
        payload={"prenom": prenom.strip(), "nom": nom.strip()},
    )
