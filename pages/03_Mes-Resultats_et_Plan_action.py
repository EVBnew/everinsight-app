# pages/03_Mes-Resultats_et_Plan_action.py
# Synthèse DISC + plan d'action EverINSIGHT

import os
import json
from datetime import datetime
import io
import math

import streamlit as st
import pandas as pd
import altair as alt
import matplotlib.pyplot as plt
from fpdf import FPDF

st.title("Mes resultats & plan d'action")

# -------------------------------------------------------------------
# 1. Récupération de l'email (session OU saisie manuelle)
# -------------------------------------------------------------------
session_email = (st.session_state.get("email") or "").strip().lower()

st.markdown(
    """
Pour consulter votre profil DISC, nous avons besoin de l’adresse e-mail utilisée
lorsque vous avez rempli le questionnaire.
"""
)

if session_email:
    st.success(f"Email détecté depuis l’onglet Accueil : **{session_email}**")
else:
    st.info(
        "Vous n’avez pas encore renseigné vos informations dans l’onglet **Accueil** "
        "ou vous avez rechargé la page. Vous pouvez saisir directement votre e-mail ci-dessous."
    )

email = st.text_input(
    "Votre adresse e-mail (celle utilisée pour le questionnaire DISC)",
    value=session_email,
).strip().lower()

if not email:
    st.stop()

# -------------------------------------------------------------------
# 2. Chargement du dernier résultat correspondant à cet e-mail
# -------------------------------------------------------------------
PAGES_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(PAGES_DIR)
LOG_DIR = os.path.join(PROJECT_ROOT, "Data", "logs")
LOG_PATH = os.path.join(LOG_DIR, "disc_forced_sessions.jsonl")

if not os.path.exists(LOG_PATH):
    st.error("Aucun résultat trouvé pour l’instant. Le fichier de réponses n’existe pas encore.")
    st.stop()

records = []
with open(LOG_PATH, "r", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        user_field = (rec.get("user") or "").strip().lower()
        # On matche sur l'email si possible
        if user_field == email:
            records.append(rec)

if not records:
    st.warning(
        "Aucun résultat DISC trouvé pour cet e-mail. "
        "Vous n’avez peut-être pas encore validé le questionnaire, "
        "ou vous avez utilisé une autre adresse."
    )
    st.stop()

# On prend le dernier résultat (le plus récent dans le fichier)
last_rec = records[-1]

scores = last_rec.get("scores", {})
style_code = last_rec.get("style", "")
top_dims = last_rec.get("top_dims", [])

# Sécurité pour éviter les KeyError
for k in ["D", "I", "S", "C"]:
    scores.setdefault(k, 0)

# -------------------------------------------------------------------
# 3. Table des scores + radar
# -------------------------------------------------------------------
DIM_LABELS = {
    "D": ("Dominance", "Résultats / décision / vitesse"),
    "I": ("Influence",  "Relation / énergie / inspiration"),
    "S": ("Stabilité",  "Coopération / patience / fiabilité"),
    "C": ("Conformité", "Qualité / précision / normes"),
}

st.subheader("Vos scores DISC")

df = pd.DataFrame(
    [
        {
            "Dimension": k,
            "Libellé": DIM_LABELS[k][0],
            "Score": scores[k],
            "Description": DIM_LABELS[k][1],
        }
        for k in ["D", "I", "S", "C"]
    ]
).sort_values("Score", ascending=False).reset_index(drop=True)

st.dataframe(df, use_container_width=True)

chart = alt.Chart(df).mark_bar().encode(
    x=alt.X("Libellé:N", sort="-y"),
    y="Score:Q",
    tooltip=["Libellé", "Score", "Description"],
).properties(height=260)

st.altair_chart(chart, use_container_width=True)

if len(df) >= 2:
    top1, top2 = df.iloc[0], df.iloc[1]
    st.success(
        f"Votre profil est principalement **{top1['Libellé']} ({top1['Dimension']})**, "
        f"avec une énergie secondaire **{top2['Libellé']} ({top2['Dimension']})**."
    )

# ---------- Radar / spider chart ----------
st.subheader("Votre profil DISC (radar)")

COLOR = {"D": "#E41E26", "I": "#FFC107", "S": "#2ECC71", "C": "#2E86DE"}
ANGLE_DEG = {"D": 45, "I": 135, "S": 225, "C": 315}

def pol2xy(angle_deg, r):
    a = math.radians(angle_deg)
    return (r * math.cos(a), r * math.sin(a))

def xy2pol(x, y):
    r = math.hypot(x, y)
    a = (math.degrees(math.atan2(y, x)) + 360) % 360
    return a, r

def scale_r(score, rmin=0.10, rmax=0.95, max_score=25):
    score = max(0, min(score, max_score))
    return rmin + (rmax - rmin) * (score / max_score)

rD = scale_r(scores["D"])
rI = scale_r(scores["I"])
rS = scale_r(scores["S"])
rC = scale_r(scores["C"])

radar_pts = {
    "D": pol2xy(45, rD),
    "I": pol2xy(135, rI),
    "S": pol2xy(225, rS),
    "C": pol2xy(315, rC),
}

ordered = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
dims_top2 = [ordered[0][0], ordered[1][0]]
x1, y1 = radar_pts[dims_top2[0]]
x2, y2 = radar_pts[dims_top2[1]]
xm, ym = (x1 + x2) / 2.0, (y1 + y2) / 2.0
marker_angle_deg, marker_r = xy2pol(xm, ym)

fig = plt.figure(figsize=(4.8, 4.8))
ax = plt.subplot(111, projection="polar")
plt.subplots_adjust(left=0.06, right=0.94, top=0.94, bottom=0.06)

sectors = {
    "D": (math.radians(0), math.radians(90)),
    "I": (math.radians(90), math.radians(180)),
    "S": (math.radians(180), math.radians(270)),
    "C": (math.radians(270), math.radians(360)),
}
for k, (start, end) in sectors.items():
    theta = [start + t * (end - start) / 120 for t in range(121)]
    rr = [1.0] * len(theta)
    ax.fill(theta, rr, alpha=0.24, color=COLOR[k], edgecolor="none")

for r, lw in [(0.30, 1), (0.42, 1), (0.90, 1.2)]:
    ax.plot([0, 2 * math.pi], [r, r], color="#bdbdbd", linewidth=lw)

for ang in [45, 135, 225, 315]:
    ax.plot(
        [math.radians(ang), math.radians(ang)],
        [0, 1],
        color="#d9d9d9",
        linewidth=1,
        linestyle="--",
        zorder=2,
    )

ax.spines["polar"].set_visible(False)

dominant_dim = ordered[0][0]
radar_color = COLOR[dominant_dim]
thetas = [
    math.radians(45),
    math.radians(135),
    math.radians(225),
    math.radians(315),
    math.radians(45),
]
radii = [rD, rI, rS, rC, rD]

ax.fill(thetas, radii, color=radar_color, alpha=0.10, zorder=3)
ax.plot(thetas, radii, color=radar_color, linewidth=1.8, zorder=4)
ax.scatter(thetas[:-1], [rD, rI, rS, rC], s=28, c=radar_color, zorder=5)

ax.plot([math.radians(45), math.radians(45)], [0, rD], color=radar_color, linewidth=1.0)
ax.plot([math.radians(135), math.radians(135)], [0, rI], color=radar_color, linewidth=1.0)
ax.plot([math.radians(225), math.radians(225)], [0, rS], color=radar_color, linewidth=1.0)
ax.plot([math.radians(315), math.radians(315)], [0, rC], color=radar_color, linewidth=1.0)

name_display = email or "participant"
ax.scatter(
    math.radians(marker_angle_deg),
    marker_r,
    s=170,
    c="#D32F2F",
    edgecolors="none",
    zorder=6,
)
label_r = max(0.05, marker_r - 0.08)
ax.text(
    math.radians(marker_angle_deg),
    label_r,
    name_display,
    ha="center",
    va="top",
    fontsize=11,
    color="#333",
    zorder=7,
)

ax.text(math.radians(45), 1.03, "D", color=COLOR["D"], ha="center", va="center",
        fontsize=14, fontweight="bold")
ax.text(math.radians(135), 1.03, "I", color=COLOR["I"], ha="center", va="center",
        fontsize=14, fontweight="bold")
ax.text(math.radians(225), 1.03, "S", color=COLOR["S"], ha="center", va="center",
        fontsize=14, fontweight="bold")
ax.text(math.radians(315), 1.03, "C", color=COLOR["C"], ha="center", va="center",
        fontsize=14, fontweight="bold")

ax.set_theta_zero_location("N")
ax.set_theta_direction(-1)
ax.set_rticks([])
ax.set_thetagrids([])
ax.set_rlim(0, 1.05)

left, mid, right = st.columns([1, 2, 1])
with mid:
    st.pyplot(fig, clear_figure=True)

st.caption(
    "Le point rouge est placé au **milieu** entre vos deux énergies les plus fortes. "
    "Le radar coloré représente l’intensité relative de chaque dimension DISC."
)

# -------------------------------------------------------------------
# 4. Lecture de profil + axes de réflexion
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("Lecture de votre profil")

DIM_NATURAL_STRENGTHS = {
    "D": "Vous aimez relever des défis, aller vite et orienter les décisions.",
    "I": "Vous mettez facilement de l’énergie et du lien dans le groupe.",
    "S": "Vous favorisez la coopération, l’écoute et un climat stable.",
    "C": "Vous apportez de la rigueur, de la précision et le sens des normes.",
}

DIM_EXCESS = {
    "D": "En excès, vous pouvez aller trop vite, imposer vos vues ou prendre peu de temps pour écouter.",
    "I": "En excès, vous pouvez beaucoup parler, vous disperser ou perdre de vue l’objectif.",
    "S": "En excès, vous pouvez éviter les conflits, trop vous adapter ou avoir du mal à dire non.",
    "C": "En excès, vous pouvez sur-structurer, rechercher trop de détails ou avoir du mal à décider.",
}

DIM_DEV = {
    "D": "Gagner à écouter davantage, poser des questions et partager la décision quand c’est utile.",
    "I": "Gagner à structurer vos messages, prioriser et conclure plus clairement.",
    "S": "Gagner à exprimer vos désaccords, poser des limites et oser dire non.",
    "C": "Gagner à simplifier, aller à l’essentiel et accepter une part d’incertitude.",
}

top_code = "".join([ordered[0][0], ordered[1][0]])

st.write(
    f"Vous avez un profil principalement **{DIM_LABELS[ordered[0][0]][0]} ({ordered[0][0]})**, "
    f"avec une énergie secondaire **{DIM_LABELS[ordered[1][0]][0]} ({ordered[1][0]})**."
)

st.markdown(
    "Concrètement, dans votre manière naturelle d’agir et de communiquer, cela se traduit souvent ainsi :"
)

for dim in [ordered[0][0], ordered[1][0]]:
    st.markdown(f"- **{DIM_LABELS[dim][0]} ({dim})** : {DIM_NATURAL_STRENGTHS[dim]}")

st.subheader("Vos points forts naturels")

for dim in [ordered[0][0], ordered[1][0]]:
    st.markdown(f"- **{DIM_LABELS[dim][0]} ({dim})** : {DIM_NATURAL_STRENGTHS[dim]}")

st.subheader("Axes de réflexion pour progresser")

st.markdown("**1. Utiliser vos forces sans tomber dans leurs excès**")
for dim in [ordered[0][0], ordered[1][0]]:
    st.markdown(f"- **Énergie {DIM_LABELS[dim][0]} ({dim})** : {DIM_EXCESS[dim]}")

st.markdown("**2. Développer davantage vos énergies moins naturelles**")
for dim in ["D", "I", "S", "C"]:
    if dim not in [ordered[0][0], ordered[1][0]]:
        st.markdown(f"- **{DIM_LABELS[dim][0]} ({dim})** : {DIM_DEV[dim]}")

# -------------------------------------------------------------------
# 5. Plan d'action – micro-comportements
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("Pistes de plan d’action personnel")

st.markdown(
    """
L’objectif est de relier votre profil DISC à **des situations concrètes**.

**1. Situation où vous avez atteint un bon résultat**  
- Quelle était la situation ?  
- Qu’avez-vous fait concrètement ?  
- Quelles énergies DISC avez-vous mobilisées (D, I, S, C) ?  
- Quels micro-comportements aimeriez-vous réutiliser plus souvent ?

**2. Situation plus difficile / moins satisfaisante**  
- Quelle était la situation ?  
- Comment avez-vous réagi spontanément ?  
- Quelle autre énergie DISC auriez-vous pu activer ?  
- Quels micro-comportements pourriez-vous tester la prochaine fois ?
"""
)

col1, col2 = st.columns(2)

with col1:
    situation_success = st.text_area(
        "Plan d'action – Situation réussie",
        height=220,
        placeholder=(
            "Décrivez une situation où vous avez obtenu un bon résultat.\n"
            "- Ce qui s'est passé\n"
            "- Ce que vous avez fait concrètement\n"
            "- Les énergies DISC mobilisées\n"
            "- Les micro-comportements à garder"
        ),
    )

with col2:
    situation_difficult = st.text_area(
        "Plan d'action – Situation difficile",
        height=220,
        placeholder=(
            "Décrivez une situation plus difficile.\n"
            "- Ce qui s'est passé\n"
            "- Votre réaction spontanée\n"
            "- L'énergie DISC que vous pourriez activer autrement\n"
            "- Les micro-comportements à tester"
        ),
    )

# -------------------------------------------------------------------
# 6. Export PDF de synthèse
# -------------------------------------------------------------------
st.markdown("---")
st.subheader("Exporter ma synthèse en PDF")

def build_pdf(
    email: str,
    scores: dict,
    ordered_dims,
    situation_success: str,
    situation_difficult: str,
) -> bytes:
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Profil DISC - Synthese personnelle", ln=True)

    pdf.set_font("Arial", "", 11)
    pdf.cell(0, 8, f"Email : {email}", ln=True)
    pdf.ln(2)

    # Scores
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Scores detaillees :", ln=True)
    pdf.set_font("Arial", "", 11)
    scores_line = (
        f"D : {scores['D']}, I : {scores['I']}, "
        f"S : {scores['S']}, C : {scores['C']}"
    )
    pdf.cell(0, 8, scores_line, ln=True)
    pdf.ln(4)

    # Points forts
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Vos points forts naturels :", ln=True)
    pdf.set_font("Arial", "", 11)
    for dim in [ordered_dims[0][0], ordered_dims[1][0]]:
        txt = f"- {DIM_LABELS[dim][0]} ({dim}) : {DIM_NATURAL_STRENGTHS[dim]}"
        pdf.multi_cell(0, 6, txt)
    pdf.ln(2)

    # Axes de réflexion
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Axes de reflexion pour progresser :", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, "Utiliser vos forces sans tomber dans leurs exces :")
    for dim in [ordered_dims[0][0], ordered_dims[1][0]]:
        txt = f"- {DIM_LABELS[dim][0]} ({dim}) : {DIM_EXCESS[dim]}"
        pdf.multi_cell(0, 6, txt)
    pdf.ln(1)
    pdf.multi_cell(0, 6, "Developper davantage vos energies moins naturelles :")
    for dim in ["D", "I", "S", "C"]:
        if dim not in [ordered_dims[0][0], ordered_dims[1][0]]:
            txt = f"- {DIM_LABELS[dim][0]} ({dim}) : {DIM_DEV[dim]}"
            pdf.multi_cell(0, 6, txt)
    pdf.ln(2)

    # Plan d'action
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Plan d'action - Situation reussie :", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, situation_success or "(non renseigne)")
    pdf.ln(1)

    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Plan d'action - Situation difficile :", ln=True)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, situation_difficult or "(non renseigne)")

    # IMPORTANT : convertir en latin-1 en ignorant les caracteres non supportes
    pdf_bytes = pdf.output(dest="S").encode("latin-1", "ignore")
    return pdf_bytes

if st.button("Générer le PDF de ma synthèse"):
    pdf_bytes = build_pdf(
        email=email,
        scores=scores,
        ordered_dims=ordered,
        situation_success=situation_success,
        situation_difficult=situation_difficult,
    )
    st.download_button(
        "⬇️ Télécharger le PDF",
        data=io.BytesIO(pdf_bytes),
        file_name="profil_disc_synthese.pdf",
        mime="application/pdf",
    )
