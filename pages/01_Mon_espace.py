import os
import json
import base64
import datetime
import streamlit as st

# Essayez d'importer OpenAI, sans faire planter l'app si le module n'est pas installé
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

st.set_page_config(
    page_title="Mon espace",
    page_icon="🏠",
    layout="wide",
)

DATA_FILE = "data/mon_espace.json"

# ============================================================
# PERSISTANCE : CHARGER / SAUVEGARDER
# ============================================================

def load_saved_data():
    """Charge les données sauvegardées depuis le fichier JSON, si présent."""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            for key, value in data.items():
                if key not in st.session_state:
                    st.session_state[key] = value
        except Exception:
            # On ne bloque pas l'app si le JSON est corrompu
            pass


def save_current_data():
    """Sauvegarde les principales données de la page dans un fichier JSON."""
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    keys_to_save = [
        "ambition_courte",
        "why1",
        "why2",
        "why3",
        "why4",
        "why5",
        "ambition_validee",
        "motivation_profonde",
        "objectif_principal",
        "sous_objectif_1",
        "sous_objectif_2",
        "horizon_mois",
        "horizon_annee",
        "kpi_user",
        "kpi_suggestions",
    ]
    data = {k: st.session_state.get(k) for k in keys_to_save if k in st.session_state}
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# Charger les données sauvées AVANT d'initialiser les widgets
load_saved_data()

# ============================================================
# OUTILS IA
# ============================================================

def get_openai_client():
    """Retourne un client OpenAI à partir de st.secrets, ou None si non dispo."""
    if OpenAI is None:
        return None

    api_key = st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        return None

    try:
        client = OpenAI(api_key=api_key)
        return client
    except Exception:
        return None


def generer_motivation_ia(ambition, why1, why2, why3, why4, why5):
    client = get_openai_client()
    if client is None:
        raise RuntimeError("Client OpenAI non disponible")

    donnees = {
        "ambition": ambition or "",
        "pourquoi_1": why1 or "",
        "pourquoi_2": why2 or "",
        "pourquoi_3": why3 or "",
        "pourquoi_4": why4 or "",
        "pourquoi_5": why5 or "",
    }

    prompt = f"""
Tu es un coach carrière qui écrit en français simple, fluide et positif.

Je te donne l'ambition d'une personne et jusqu'à 5 réponses successives à la question
"Pourquoi ?". Les réponses peuvent contenir des fautes ou être mal structurées.

Ta mission :
- corriger les fautes,
- reformuler pour que ce soit fluide,
- écrire un seul paragraphe de 4 à 6 phrases,
- garder le sens global,
- finir par une phrase du type : "C'est pour toutes ces raisons que je souhaite <ambition>."

Ne fais pas de liste, pas de titres, pas de guillemets, pas de commentaire.

Données :
{donnees}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        max_output_tokens=300,
    )

    texte = response.output[0].content[0].text
    return texte.strip()


def generer_kpi_ia(ambition, objectif, sous1, sous2, horizon_mois, horizon_annee):
    client = get_openai_client()
    if client is None:
        raise RuntimeError("Client OpenAI non disponible")

    horizon_txt = ""
    if horizon_mois or horizon_annee:
        horizon_txt = f"{horizon_mois} {horizon_annee}".strip()

    donnees = {
        "ambition": ambition or "",
        "objectif_principal": objectif or "",
        "sous_objectif_1": sous1 or "",
        "sous_objectif_2": sous2 or "",
        "horizon": horizon_txt,
    }

    prompt = f"""
Tu es un coach professionnel spécialisé en objectifs et en suivi de progrès.

Je te donne l'ambition et l'objectif d'une personne, éventuellement des sous-objectifs,
et un horizon de temps (mois/année).

Ta mission :
- proposer 3 à 5 critères de succès concrets (KPI ou indicateurs),
- adaptés à l'objectif,
- formulés en français simple,
- au format texte libre (pas de puces markdown, pas de numérotation, pas de tableau),
- dans un seul paragraphe ou plusieurs phrases courtes séparées par des points.

Données :
{donnees}
"""

    response = client.responses.create(
        model="gpt-4.1-mini",
        input=prompt,
        max_output_tokens=300,
    )

    texte = response.output[0].content[0].text
    return texte.strip()

# ============================================================
# FALLBACKS SANS IA
# ============================================================

def motivation_fallback(ambition, why1, why2, why3, why4, why5):
    ambition_txt = (ambition or "").strip()
    if ambition_txt.endswith("."):
        ambition_txt = ambition_txt[:-1]
    ambition_txt = ambition_txt.strip()

    parts = []

    if ambition_txt and why5:
        parts.append(f"En visant à {ambition_txt.lower()}, je veux {why5.strip().rstrip('.')}.")
    elif ambition_txt:
        parts.append(f"Je souhaite {ambition_txt.lower()}.")

    if why4:
        parts.append(f"Pour y parvenir, il est important pour moi de {why4.strip().rstrip('.')}.")
    if why3:
        parts.append(f"Cela suppose notamment de {why3.strip().rstrip('.')}.")
    if why2:
        parts.append(f"Grâce à cela, je pourrai {why2.strip().rstrip('.')}.")
    if why1:
        parts.append(f"C'est important pour moi car {why1.strip().rstrip('.')}.")
    if ambition_txt:
        parts.append(f"C'est pour toutes ces raisons que je souhaite {ambition_txt.lower()}.")

    return " ".join(parts).strip()


def kpi_fallback(ambition, objectif, sous1, sous2, horizon_mois, horizon_annee):
    ambition_txt = ambition or "ton ambition"
    obj_txt = objectif or ambition_txt
    horizon_txt = ""
    if horizon_mois and horizon_annee:
        horizon_txt = f"d'ici {horizon_mois} {horizon_annee}"
    elif horizon_annee:
        horizon_txt = f"d'ici {horizon_annee}"

    lignes = []

    lignes.append(
        f"Atteindre l'objectif « {obj_txt} » {horizon_txt} en ayant un retour positif "
        "de la part de ton manager ou de tes clients."
    )

    if sous1:
        lignes.append(
            f"Progresser sur le sous-objectif « {sous1} » avec des résultats visibles "
            "dans les missions ou projets confiés."
        )

    if sous2:
        lignes.append(
            f"Consolider le sous-objectif « {sous2} » en gagnant en autonomie et en responsabilité."
        )

    lignes.append(
        "Être capable d'illustrer ta progression avec au moins 2 ou 3 exemples concrets "
        "sur lesquels tu as fait la différence."
    )

    return " ".join(lignes)

# ============================================================
# VIDÉO TUTORIEL EN VIGNETTE
# ============================================================

def render_video_thumbnail(path: str, width: int = 260):
    """
    Affiche la vidéo en petit format (vignette) grâce à un embed base64.
    """
    if not os.path.exists(path):
        st.info(
            "Ajoute la vidéo `assets/Les_5_pourquoi.mp4` pour afficher ici le tutoriel "
            "sur le jeu des 5 pourquoi."
        )
        return

    try:
        with open(path, "rb") as f:
            data = f.read()
        b64 = base64.b64encode(data).decode()
        video_html = f"""
        <video width="{width}" controls>
            <source src="data:video/mp4;base64,{b64}" type="video/mp4">
            Votre navigateur ne supporte pas la lecture vidéo.
        </video>
        """
        st.markdown(video_html, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Impossible d'afficher la vidéo tutorielle : {e}")

# ============================================================
# INITIALISATION ETAT
# ============================================================

if "motivation_profonde" not in st.session_state:
    st.session_state["motivation_profonde"] = ""

if "kpi_suggestions" not in st.session_state:
    st.session_state["kpi_suggestions"] = ""

if "ambition_validee" not in st.session_state:
    st.session_state["ambition_validee"] = False

# ============================================================
# HEADER / PHOTO PROFIL
# ============================================================

st.title("Mon espace")

st.write("OPENAI détecté :", "OPENAI_API_KEY" in st.secrets)
st.write("")

# Zone photo un peu plus à gauche
col_photo, col_empty = st.columns([1.2, 2])

with col_photo:
    st.markdown("#### Ma photo de profil")

    photo_path = "assets/photo_profil.png"

    if os.path.exists(photo_path):
        st.image(photo_path, width=160)
    else:
        st.image("https://via.placeholder.com/160", width=160)

    uploaded = st.file_uploader(
        "Télécharger une photo (jpg ou png)",
        type=["jpg", "jpeg", "png"],
        key="upload_photo",
    )

    if uploaded is not None:
        try:
            os.makedirs("assets", exist_ok=True)
            with open(photo_path, "wb") as f:
                f.write(uploaded.getbuffer())
            # On relance l'app pour voir immédiatement la nouvelle photo
            try:
                st.rerun()
            except AttributeError:
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Erreur lors de l'enregistrement de la photo : {e}")

st.write("---")

# ============================================================
# ÉTAPE 1 — CONSTRUIRE MON AMBITION
# ============================================================

st.header("Étape 1 • Construire mon ambition")

st.write(
    "Décris en quelques lignes ce que tu veux atteindre, puis utilise le jeu des "
    "**5 pourquoi** pour aller au cœur de ta motivation."
)

ambition = st.text_input(
    "Mon ambition (version courte)",
    key="ambition_courte",
    placeholder="Exemple : Devenir chef de projet",
)

st.subheader("Le jeu des 5 pourquoi")

# Formulaire + spacer + vignette vidéo
col_why_form, col_spacer, col_tuto = st.columns([3, 0.3, 1])

with col_why_form:
    # Pourquoi 1
    if ambition:
        label_1 = f"Pourquoi veux-tu {ambition.lower()} ?"
    else:
        label_1 = "Pourquoi 1 ?"

    why1 = st.text_input(
        label_1,
        key="why1",
        placeholder="Réponse…",
    )

    # Pourquoi 2
    if why1:
        label_2 = f"Pourquoi {why1.lower()} ?"
    else:
        label_2 = "Pourquoi 2 ?"

    why2 = st.text_input(
        label_2,
        key="why2",
        placeholder="Réponse…",
    )

    # Pourquoi 3
    if why2:
        label_3 = f"Pourquoi {why2.lower()} ?"
    else:
        label_3 = "Pourquoi 3 ?"

    why3 = st.text_input(
        label_3,
        key="why3",
        placeholder="Réponse…",
    )

    # Pourquoi 4
    if why3:
        label_4 = f"Pourquoi {why3.lower()} ?"
    else:
        label_4 = "Pourquoi 4 ?"

    why4 = st.text_input(
        label_4,
        key="why4",
        placeholder="Réponse…",
    )

    # Pourquoi 5
    if why4:
        label_5 = f"Pourquoi {why4.lower()} ?"
    else:
        label_5 = "Pourquoi 5 ?"

    why5 = st.text_input(
        label_5,
        key="why5",
        placeholder="Réponse…",
    )

    st.write("")
    btn_valider_why = st.button("✅ Valider mon ambition et mes 5 pourquoi")

    if btn_valider_why:
        if all([ambition, why1, why2, why3, why4, why5]):
            st.session_state["ambition_validee"] = True
            st.success("Ton ambition et tes 5 pourquoi sont enregistrés.")
        else:
            st.session_state["ambition_validee"] = False
            st.warning("Merci de renseigner ton ambition et les 5 pourquoi avant de valider.")

    if st.session_state["ambition_validee"]:
        st.caption(
            f"✔ Ambition validée : **{ambition or st.session_state.get('ambition_courte', '')}** "
            f"— pourquoi profond : **{why5 or st.session_state.get('why5', '')}**"
        )

with col_tuto:
    st.markdown("### Tutoriel")
    render_video_thumbnail("assets/Les_5_pourquoi.mp4", width=260)

st.write("---")

st.subheader("Ma motivation profonde")

col_btn_mot, col_info_mot = st.columns([1, 3])

with col_btn_mot:
    btn_motivation = st.button("Générer ma motivation profonde avec l’IA")

with col_info_mot:
    if OpenAI is None:
        st.caption(
            "ℹ️ Le module `openai` n'est pas installé dans cet environnement. "
            "Installe-le pour activer la génération IA (`pip install openai`)."
        )

if btn_motivation:
    if ambition and why5:
        try:
            texte = generer_motivation_ia(ambition, why1, why2, why3, why4, why5)
            st.session_state["motivation_profonde"] = texte
        except Exception:
            texte = motivation_fallback(ambition, why1, why2, why3, why4, why5)
            st.session_state["motivation_profonde"] = texte
            st.warning(
                "Impossible d'appeler l'IA (clé absente, modèle indisponible ou autre erreur). "
                "Texte généré avec une version simplifiée."
            )
    else:
        st.warning("Merci de renseigner au minimum ton ambition et ton 5ᵉ pourquoi.")

if st.session_state["motivation_profonde"]:
    st.write(st.session_state["motivation_profonde"])
else:
    st.info(
        "Une fois ton ambition et tes 5 pourquoi renseignés, clique sur le bouton ci-dessus "
        "pour générer automatiquement ton texte de motivation profonde."
    )

st.write("---")

# ============================================================
# ÉTAPE 2 — CLARIFIER MON OBJECTIF
# ============================================================

st.header("Étape 2 • Clarifier mon objectif")

ambition_affichee = ambition or st.session_state.get("ambition_courte", "")
if ambition_affichee:
    st.info(f"Ton ambition actuelle : **{ambition_affichee}**")

st.markdown(
    """
**Comment faire le lien ambition → objectif → sous-objectifs ?**

- L’**objectif principal** reprend ton ambition quasiment telle quelle, en phrase complète.
- Les **sous-objectifs** sont des étapes intermédiaires : compétences à développer, missions à prendre, expériences à vivre.
- L’**horizon de temps** (mois/année) te donne une date cible réaliste.
- Les **indicateurs de succès (KPI)** décrivent comment tu verras que tu as vraiment progressé.
"""
)

col_obj_1, col_obj_2 = st.columns(2)

with col_obj_1:
    objectif_default = st.session_state.get("objectif_principal", "")
    if not objectif_default:
        objectif_default = ambition_affichee

    objectif_principal = st.text_input(
        "Objectif principal",
        key="objectif_principal",
        placeholder="Exemple : Devenir chef de projet sur des projets de transformation digitale",
        value=objectif_default,
    )

    sous_objectif_1 = st.text_input(
        "Sous-objectif intermédiaire n°1",
        key="sous_objectif_1",
        placeholder="Exemple : Piloter un projet interne de bout en bout",
    )

    sous_objectif_2 = st.text_input(
        "Sous-objectif intermédiaire n°2 (optionnel)",
        key="sous_objectif_2",
        placeholder="Exemple : Renforcer mes compétences en gestion de projet agile",
    )

with col_obj_2:
    st.markdown("**Horizon de temps** (mois / année)")

    mois_liste = [
        "", "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre",
    ]
    current_year = datetime.datetime.now().year

    horizon_mois = st.selectbox(
        "Mois",
        options=mois_liste,
        key="horizon_mois",
    )

    horizon_annee = st.number_input(
        "Année",
        min_value=current_year,
        max_value=current_year + 10,
        value=st.session_state.get("horizon_annee", current_year + 1),
        step=1,
        key="horizon_annee",
    )

    st.write("")
    st.markdown("**Indicateurs de succès (KPI)**")

    kpi_text_user = st.text_area(
        "Comment sauras-tu que tu as réussi ?",
        key="kpi_user",
        height=120,
        placeholder=(
            "Quelques exemples : retours positifs de tes clients, prise de responsabilités, "
            "certification obtenue, missions de plus en plus complexes…"
        ),
    )

st.write("")
st.subheader("Inspiration par ton coach IA")

col_btn_kpi, col_txt_kpi = st.columns([1, 3])

with col_btn_kpi:
    btn_kpi = st.button("Que propose mon coach IA pour mes KPI ?")

with col_txt_kpi:
    if btn_kpi:
        if objectif_principal:
            try:
                texte_kpi = generer_kpi_ia(
                    ambition_affichee,
                    objectif_principal,
                    sous_objectif_1,
                    sous_objectif_2,
                    horizon_mois,
                    str(horizon_annee) if horizon_annee else "",
                )
                st.session_state["kpi_suggestions"] = texte_kpi
            except Exception:
                texte_kpi = kpi_fallback(
                    ambition_affichee,
                    objectif_principal,
                    sous_objectif_1,
                    sous_objectif_2,
                    horizon_mois,
                    horizon_annee,
                )
                st.session_state["kpi_suggestions"] = texte_kpi
                st.warning(
                    "Impossible d'appeler l'IA (clé absente, modèle indisponible ou autre erreur). "
                    "Texte généré avec une version simplifiée."
                )
        else:
            st.warning("Merci de renseigner au minimum ton objectif principal.")

    if st.session_state["kpi_suggestions"]:
        st.info(st.session_state["kpi_suggestions"])
    else:
        st.caption(
            "Ton coach IA peut t'aider à formuler des indicateurs de succès concrets. "
            "Renseigne ton objectif puis clique sur le bouton."
        )

st.write("---")

# ============================================================
# ÉTAPE 3 — MES ATOUTS POUR RÉUSSIR (DASHBOARD)
# ============================================================

st.header("Étape 3 • Mes atouts pour réussir")

st.write(
    "EVERBOARDING agit comme un **coach mental dans ta poche**. "
    "Tu peux activer plusieurs axes pour soutenir ton ambition."
)

dash_col1, dash_col2 = st.columns(2)

with dash_col1:
    st.markdown(
        """
<div style="
    border-radius: 12px;
    border: 1px solid #e6e9ef;
    padding: 16px 18px;
    background-color: #f8f9fc;
    margin-bottom: 12px;">
  <div style="font-size: 22px; margin-bottom: 4px;">🧠 Confiance à toute épreuve</div>
  <div style="font-size: 14px; color: #555;">
    Travailler ta posture mentale, ton discours intérieur et ta capacité à rester solide sous pression.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.caption("Bientôt disponible : un espace dédié à la confiance mentale.")

with dash_col2:
    st.markdown(
        """
<div style="
    border-radius: 12px;
    border: 1px solid #e6e9ef;
    padding: 16px 18px;
    background-color: #f8f9fc;
    margin-bottom: 12px;">
  <div style="font-size: 22px; margin-bottom: 4px;">📈 Mon programme d’entraînement</div>
  <div style="font-size: 14px; color: #555;">
    Construire un plan d’entraînement personnalisé pour ancrer tes soft skills dans la pratique.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.page_link(
        "pages/02_Mon_programme_d_entrainement.py",
        label="Ouvrir mon programme d’entraînement",
    )

dash_col3, dash_col4 = st.columns(2)

with dash_col3:
    st.markdown(
        """
<div style="
    border-radius: 12px;
    border: 1px solid #e6e9ef;
    padding: 16px 18px;
    background-color: #f8f9fc;
    margin-bottom: 12px;">
  <div style="font-size: 22px; margin-bottom: 4px;">🤝 Mes partenaires d’entraînement</div>
  <div style="font-size: 14px; color: #555;">
    Identifier les personnes qui peuvent jouer un rôle de partenaire d’entraînement dans ton quotidien.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.page_link(
        "pages/14_Mes_partenaires_d_entrainement.py",
        label="Ouvrir mes partenaires d’entraînement",
    )

with dash_col4:
    st.markdown(
        """
<div style="
    border-radius: 12px;
    border: 1px solid #e6e9ef;
    padding: 16px 18px;
    background-color: #f8f9fc;
    margin-bottom: 12px;">
  <div style="font-size: 22px; margin-bottom: 4px;">🎯 Mon coach carrière</div>
  <div style="font-size: 14px; color: #555;">
    Un coach (digital ou humain) pour t’aider à prendre du recul, ajuster ta stratégie et garder le cap.
  </div>
</div>
""",
        unsafe_allow_html=True,
    )
    st.page_link(
        "pages/20_Mon_coach_carriere.py",
        label="Ouvrir mon coach carrière",
    )

st.write("---")

# ============================================================
# SAUVEGARDE GLOBALE
# ============================================================

if st.button("💾 Sauvegarder mon espace"):
    try:
        save_current_data()
        st.success("Tes informations ont été sauvegardées. Tu pourras les retrouver à ta prochaine visite.")
    except Exception as e:
        st.error(f"Erreur lors de la sauvegarde : {e}")

st.success("Ton espace est structuré : ambition, objectifs et atouts pour réussir.")
