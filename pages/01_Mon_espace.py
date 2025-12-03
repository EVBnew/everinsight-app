# pages/01_Mon_espace.py
import streamlit as st
from components import user_context

st.set_page_config(page_title="Mon espace", page_icon="👤", layout="wide")

st.title("Mon espace")

# --------------------------------------------------
# 1) Profil de base (photo + info depuis Accueil)
# --------------------------------------------------
profile = user_context.get_profile()
first_name = profile.get("first_name", "")
last_name = profile.get("last_name", "")
email = profile.get("email", "")

with st.container():
    st.subheader("Mon profil")

    col_photo, col_text = st.columns([1, 3])

    # --- Photo à gauche ---
    with col_photo:
        uploaded_photo = st.file_uploader(
            "Mettre à jour ma photo",
            type=["png", "jpg", "jpeg"],
            key="photo_uploader",
        )
        if uploaded_photo is not None:
            user_context.save_photo(uploaded_photo)
            st.success("Photo mise à jour.")

        photo_bytes = user_context.get_photo()
        if photo_bytes:
            st.image(
                photo_bytes,
                width=160,
                caption=f"{first_name} {last_name}".strip() or "Ma photo",
            )
        else:
            st.info(
                "Aucune photo pour l’instant. Ajoutez-en une dans l’onglet **Accueil** ou ici 😊"
            )

    # --- Résumé à droite ---
    with col_text:
        if first_name or last_name or email:
            st.markdown(
                f"""
                **Nom :** {first_name} {last_name}  
                **E-mail :** {email or "_non renseigné_"}  
                **Fonction / rôle :** {profile.get("job_title", "_non renseigné_")}  
                **Organisation :** {profile.get("company", "_non renseignée_")}
                """
            )
        else:
            st.warning(
                "Pour profiter pleinement de l’application, commence par renseigner "
                "tes informations dans l’onglet **Accueil**."
            )

st.markdown("---")

# --------------------------------------------------
# 2) Mon équipe de performance (vision “athlète”)
# --------------------------------------------------
st.subheader("Mon équipe de performance")

st.caption(
    "Comme un athlète, tu t’entoures d’une équipe pour progresser : programme "
    "d’entraînement, coach carrière, partenaires d’entraînement, occasions de briller…"
)

c1, c2, c3 = st.columns(3)

with c1:
    st.page_link(
        "pages/02_Mieux se connaître.py",     # 🔴 important : on pointe vers le HUB
        label="📊 Mon programme d’entraînement\n(autodiagnostics)",
        icon=None,
    )

with c2:
    st.page_link(
        "pages/20_Chat_coach.py",
        label="🧑‍🏫 Mon coach carrière",
        icon=None,
    )

with c3:
    st.page_link(
        "pages/14_Mon_espace_Buddy.py",
        label="🤝 Mes partenaires d’entraînement\n(Buddy)",
        icon=None,
    )

st.markdown("---")

# --------------------------------------------------
# 3) Mon ambition (jeu des 5 pourquoi)
# --------------------------------------------------
st.subheader("Mon ambition")

st.markdown(
    "Décris en quelques lignes ce que tu veux atteindre, puis utilise le jeu des "
    "**5 pourquoi** pour aller au cœur de ta motivation."
)

ambition = st.text_area(
    "Mon ambition (version courte)",
    key="ambition_text",
    height=80,
    placeholder="Ex : Devenir un manager reconnu pour faire grandir ses équipes…",
)

st.markdown("##### Le jeu des 5 pourquoi")

whys = []
for i in range(1, 6):
    answer = st.text_input(
        f"Pourquoi {i} ?",
        key=f"why_{i}",
        placeholder="Réponse…",
    )
    whys.append(answer)

if st.button("Enregistrer mon ambition"):
    user_context.save_ambition(ambition, whys)
    st.success("Ambition enregistrée dans ton profil (réutilisable dans le reste de l’app).")

st.markdown("---")

# --------------------------------------------------
# 4) Raccourcis vers les autres espaces
# --------------------------------------------------
st.subheader("Accès rapide à mes outils")

col_a, col_b, col_c = st.columns(3)

with col_a:
    st.page_link(
        "pages/03_Mes-Resultats_et_Plan_action.py",
        label="🎯 Mes résultats & plan d’action",
        icon=None,
    )

with col_b:
    st.page_link(
        "pages/13_Bases_connaissances.py",
        label="📚 Mes bases de connaissances\n(Everboarding)",
        icon=None,
    )

with col_c:
    st.page_link(
        "pages/11_Mieux_me_connaitre.py",
        label="🧭 Mon profil DISC (accès direct)",
        icon=None,
    )
