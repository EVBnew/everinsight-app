# components/user_context.py
import streamlit as st

# Profil par défaut
DEFAULT_PROFILE = {
    "first_name": "",
    "last_name": "",
    "email": "",
    "job_title": "",
    "company": "",
    "bio": "",
    "photo_bytes": None,  # bytes de l'image
}


def init_user() -> dict:
    """Initialise le profil utilisateur dans st.session_state si besoin."""
    profile = st.session_state.get("user_profile")
    if profile is None:
        profile = DEFAULT_PROFILE.copy()
        # On récupère si possible ce qui vient déjà de l'onglet Accueil
        for key in ("first_name", "last_name", "email"):
            if key in st.session_state and st.session_state[key]:
                profile[key] = st.session_state[key]
        st.session_state["user_profile"] = profile
    return profile


def get_profile() -> dict:
    """Retourne le profil courant (et l'initialise si vide)."""
    return init_user()


def save_profile(
    first_name: str,
    last_name: str,
    email: str,
    job_title: str,
    company: str,
    bio: str,
) -> None:
    """Met à jour le profil + recopie dans les clés globales utilisées ailleurs."""
    profile = init_user()
    profile.update(
        {
            "first_name": first_name.strip(),
            "last_name": last_name.strip(),
            "email": email.strip().lower(),
            "job_title": job_title.strip(),
            "company": company.strip(),
            "bio": bio.strip(),
        }
    )
    st.session_state["user_profile"] = profile

    # Ces clés sont utilisées par le DISC, etc.
    st.session_state["first_name"] = profile["first_name"]
    st.session_state["last_name"] = profile["last_name"]
    st.session_state["email"] = profile["email"]


def save_photo(uploaded_file) -> None:
    """Sauvegarde la photo (bytes) dans le profil."""
    if uploaded_file is None:
        return
    profile = init_user()
    profile["photo_bytes"] = uploaded_file.getvalue()
    st.session_state["user_profile"] = profile


def get_photo():
    """Retourne les bytes de la photo ou None."""
    profile = init_user()
    return profile.get("photo_bytes")
