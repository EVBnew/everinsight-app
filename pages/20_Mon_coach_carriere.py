import streamlit as st
from datetime import datetime
import uuid

import gspread
from gspread.exceptions import APIError, WorksheetNotFound
from google.oauth2.service_account import Credentials

st.set_page_config(
    page_title="Mes échanges avec mon coach",
    page_icon="💬",
    layout="wide",
)

st.title("💬 Mes échanges avec mon coach carrière")

# ---------------------------------------------------------
# 0) Vérifier qu’on connaît l’utilisateur
# ---------------------------------------------------------
user_id = st.session_state.get("user_id")
first_name = st.session_state.get("first_name")
email = st.session_state.get("email")

if not user_id or not email:
    st.warning(
        "Je ne trouve pas ton profil en mémoire. "
        "Merci de passer d'abord par **Mon espace apprenant**."
    )
    st.stop()

st.info(f"Connecté en tant que **{first_name}** ({email})")

# ---------------------------------------------------------
# 1) Connexion à Google Sheets
# ---------------------------------------------------------
try:
    google_info = dict(st.secrets["google"])
    scopes = st.secrets["scopes"]

    creds = Credentials.from_service_account_info(google_info, scopes=scopes)
    client = gspread.authorize(creds)

    spreadsheet_id = st.secrets["gspread"]["spreadsheet_id"]
    sh = client.open_by_key(spreadsheet_id)

except Exception as e:
    st.error(f"Erreur de connexion à Google Sheets : {repr(e)}")
    st.stop()

# ---------------------------------------------------------
# 2) Ouverture / création de l’onglet MESSAGES
# ---------------------------------------------------------
MESSAGES_SHEET_NAME = "MESSAGES"

try:
    try:
        ws_msg = sh.worksheet(MESSAGES_SHEET_NAME)
    except WorksheetNotFound:
        ws_msg = sh.add_worksheet(title=MESSAGES_SHEET_NAME, rows=2000, cols=10)
        ws_msg.append_row(
            ["msg_id", "user_id", "sender", "message", "created_at", "status"]
        )

    # Récupérer tous les messages
    all_msgs = ws_msg.get_all_records()

    # Filtrer sur l'utilisateur courant
    my_msgs = [
        m for m in all_msgs
        if str(m.get("user_id", "")).strip() == str(user_id)
    ]

    # Trier par date si possible
    def _safe_created_at(m):
        return m.get("created_at", "")

    my_msgs = sorted(my_msgs, key=_safe_created_at)

except APIError as e:
    st.error("Erreur lors de l'accès à l’onglet MESSAGES.")
    st.code(repr(e), language="text")
    st.stop()
except Exception as e:
    st.error(f"Erreur chargement messages : {repr(e)}")
    st.stop()

# ---------------------------------------------------------
# 3) Affichage du fil de discussion
# ---------------------------------------------------------
st.markdown("### 📜 Historique de nos échanges")

if not my_msgs:
    st.info("Tu n’as pas encore échangé avec ton coach. Pose-lui ta première question !")
else:
    chat_container = st.container()
    with chat_container:
        for m in my_msgs:
            sender = m.get("sender", "user")
            message = m.get("message", "")
            created_at = m.get("created_at", "")

            if sender == "user":
                # Message apprenant
                st.markdown(
                    f"""
<div style="
    background-color:#e6f4ff;
    border-radius:12px;
    padding:8px 12px;
    margin-bottom:6px;
    max-width:80%;
">
<b>Toi</b> <span style="font-size:11px;color:#666;">({created_at})</span><br>
{message}
</div>
""",
                    unsafe_allow_html=True,
                )
            else:
                # Message coach
                st.markdown(
                    f"""
<div style="
    background-color:#f5f0ff;
    border-radius:12px;
    padding:8px 12px;
    margin-bottom:6px;
    margin-left:auto;
    max-width:80%;
">
<b>Coach</b> <span style="font-size:11px;color:#666;">({created_at})</span><br>
{message}
</div>
""",
                    unsafe_allow_html=True,
                )

# ---------------------------------------------------------
# 4) Envoi d’un nouveau message au coach
# ---------------------------------------------------------
st.markdown("### ✏️ Envoyer un nouveau message à mon coach")

with st.form("send_message_form"):
    new_message = st.text_area(
        "Ton message",
        placeholder="Pose une question sur ton parcours, ta formation, ta carrière…",
        height=120,
    )
    submitted = st.form_submit_button("📨 Envoyer au coach")

if submitted:
    if not new_message.strip():
        st.warning("Ton message est vide.")
    else:
        try:
            msg_id = str(uuid.uuid4())
            created_at = datetime.utcnow().isoformat() + "Z"
            status = "new"   # le coach verra que c’est un nouveau message

            ws_msg.append_row(
                [msg_id, user_id, "user", new_message.strip(), created_at, status]
            )

            st.success("Message envoyé à ton coach 🎯")
            st.experimental_rerun()  # pour rafraîchir le fil

        except Exception as e:
            st.error(f"Erreur lors de l’envoi du message : {repr(e)}")
