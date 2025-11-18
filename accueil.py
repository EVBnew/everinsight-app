# accueil.py
# Page d'accueil EverINSIGHT — Diagnostic DISC

import streamlit as st
from datetime import datetime

# ---------------------------------------------------------
# Config générale de la page
# ---------------------------------------------------------
st.set_page_config(
    page_title="EverINSIGHT — Diagnostic DISC",
    page_icon="🧠",
    layout="wide",
)

# ---------------------------------------------------------
# Page principale (aucun mot de passe)
# ---------------------------------------------------------
def main():

    st.title("EverINSIGHT — Diagnostic DISC")

    st.markdown(
        """
Le modèle **DISC** décrit 4 grandes manières d’agir et de communiquer :

- **D – Dominance** : orienté résultats, aime décider et relever des défis.  
- **I – Influence** : sociable, enthousiaste, aime convaincre et inspirer.  
- **S – Stabilité** : à l’écoute, coopératif, recherche l’harmonie.  
- **C – Conformité** : structuré, rigoureux, orienté qualité et précision.

Ce questionnaire n’est **ni un test d’intelligence, ni un jugement**.  
Il sert à mieux comprendre votre **style naturel**, vos **points forts**
et vos **axes de progression** pour travailler plus efficacement en équipe.
"""
    )

    st.markdown("---")

    # -----------------------------------------------------
    # 1. Vos informations
    # -----------------------------------------------------
    st.header("1. Vos informations")

    default_first_name = st.session_state.get("first_name", "")
    default_last_name = st.session_state.get("last_name", "")
    default_email = st.session_state.get("email", "")

    with st.form("user_info_form"):
        col1, col2 = st.columns(2)
        with col1:
            first_name = st.text_input("Prénom", value=default_first_name)
        with col2:
            last_name = st.text_input("Nom", value=default_last_name)

        email = st.text_input(
            "Adresse e-mail (celle utilisée pour le cours)",
            value=default_email,
            help="Elle servira à retrouver vos résultats et recevoir votre synthèse.",
        )

        submitted = st.form_submit_button("Enregistrer mes informations")

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

    if st.session_state.get("email"):
        st.info(
            f"Vous êtes connecté en tant que **{st.session_state.get('first_name', '')} "
            f"{st.session_state.get('last_name', '')}** "
            f"({st.session_state['email']}).\n\n"
            "Si besoin, vous pouvez modifier ces informations puis cliquer sur "
            "**Enregistrer mes informations**."
        )

    st.markdown("---")

    # -----------------------------------------------------
    # 2. Étapes suivantes
    # -----------------------------------------------------
    st.header("2. Comment se déroule la démarche ?")

    st.markdown(
        """
1. Renseignez vos informations sur cette page.  
2. Allez dans l’onglet **“Questionnaire DISC”** pour répondre aux 25 situations proposées.  
3. Une fois le questionnaire complété, vous pourrez accéder à **“Mes Résultats et Plan d’action”** pour :
   - visualiser votre profil DISC et votre radar,  
   - lire une analyse synthétique de vos points forts,  
   - identifier des axes de réflexion,  
   - définir un **micro plan d’action personnel**.

Vous pourrez également télécharger votre synthèse au format **PDF**.
"""
    )

if __name__ == "__main__":
    main()

