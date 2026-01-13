import os
import json
import streamlit as st

from components.access_guard import enforce_access
from components.everboarding_gate import log_event_via_webhook  # si tu veux garder tes logs existants

# =============================
# STREAMLIT CONFIG (MUST BE FIRST)
# =============================
st.set_page_config(page_title="Bienvenue", page_icon="🏁", layout="wide")

# =============================
# CONFIG
# =============================
PORTAL_URL = (st.secrets.get("PORTAL_ACCESS_URL") or "https://everboarding.fr/everinsight").strip()

DATA_DIR = "Data"
PROFILE_PATH = os.path.join(DATA_DIR, "profil_apprenant.json")
os.makedirs(DATA_DIR, exist_ok=True)

DEBUG = bool(st.secrets.get("DEBUG", False))

# =============================
# ACCESS GATE (MUST RUN BEFORE UI)
# =============================
access = enforce_access(portal_url=PORTAL_URL, page_name="accueil")
approved_email = (access.get("email") or "").strip().lower()
st.session_state["approved_email"] = approved_email  # utile pour verrouiller l'email dans le form

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


# =============================
# UI
# =============================
st.title("Bienvenue dans EVERINSIGHT")
st.markdown("Renseigne tes infos une seule fois. Elles seront réutilisées dans toute l’app.")

profile = load_profile()
default_prenom = profile.get("prenom", "")
default_nom = profile.get("nom", "")

default_email = approved_email if approved_email else profile.get("email", "")

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
        st.write("approved_email =", repr(approved_email))
        st.write("email_raw =", repr(email_raw))
        st.write("email_normalized =", repr(email))
        st.write("token_present =", bool(st.query_params.get("token")))

if submitted:
    if not email:
        st.error(
            "L’email est obligatoire (identifiant apprenant).\n\n"
            "Astuce : clique dans le champ email et tape un caractère si ton navigateur l'a auto-rempli."
        )
    else:
        save_profile({"prenom": prenom.strip(), "nom": nom.strip(), "email": email})
        st.success("Profil enregistré. Tu peux aller sur “Mon espace” / “Mon programme”.")

        # log profile_saved
        log_event_via_webhook(
            email=email,
            event="profile_saved",
            page="accueil",
            payload={"prenom": prenom.strip(), "nom": nom.strip()},
        )
