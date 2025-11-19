import streamlit as st
from datetime import datetime

st.set_page_config(page_title="Accueil", page_icon="🏠", layout="wide")

st.title("EverINSIGHT — Diagnostic DISC")

st.markdown(
    """
Ce questionnaire vous aidera à mieux comprendre votre **style naturel**, vos **points forts**
et vos **axes de progression** pour mieux collaborer en équipe.
"""
)

# -------------------------------
#  FORMULAIRE D’IDENTIFICATION
# -------------------------------
st.subheader("1. Vos informations")

if "first_name" not in st.session_state:
    st.session_state["first_name"] = ""
if "last_name" not in st.session_state:
    st.session_state["last_name"] = ""
if "email" not in st.session_state:
    st.session_state["email"] = ""

with st.form("user_form"):
    first_name = st.text_input("Prénom", value=st.session_state["first_name"])
    last_name = st.text_input("Nom", value=st.session_state["last_name"])
    email = st.text_input(
        "Adresse e-mail (celle utilisée pour le cours)",
        value=st.session_state["email"],
        help="Elle servira à retrouver vos résultats et votre synthèse."
    )

    submitted = st.form_submit_button("Enregistrer mes informations")

# -------------------------------
#  VALIDATION DU FORMULAIRE
# -------------------------------
if submitted:
    if not first_name or not last_name or not email:
        st.error("Merci de renseigner **Prénom**, **Nom** et **Adresse e-mail**.")
    elif "@" not in email:
        st.error("L’adresse e-mail ne semble pas valide.")
    else:
        st.session_state["first_name"] = first_name.strip()
        st.session_state["last_name"] = last_name.strip()
        st.session_state["email"] = email.strip().lower()
        st.session_state["user_saved_at"] = datetime.utcnow().isoformat() + "Z"

        st.success(
            f"Merci {first_name}, vos informations ont été enregistrées. "
            "Vous pouvez maintenant passer à l’onglet **Questionnaire DISC**."
        )

# -------------------------------
#  RÉCAP UTILISATEUR CONNECTÉ
# -------------------------------
if st.session_state.get("email"):
    st.info(
        f"Vous êtes connecté en tant que **{st.session_state['first_name']} "
        f"{st.session_state['last_name']}** ({st.session_state['email']}).\n\n"
        "Vous pouvez modifier vos informations si besoin, puis cliquer sur "
        "**Enregistrer mes informations**."
    )

