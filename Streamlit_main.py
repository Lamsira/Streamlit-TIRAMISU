# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 16:16:23 2026

@author: fages1
"""

import streamlit as st
import read_model_new_streamlit as rmn
import chardet
st.set_page_config(
    page_title="TIRAMISU",
    page_icon="🗂️",
    layout="wide",
)


def page_accueil():
    st.title("🍮 TIRAMISU")
    st.markdown(
        """
        Welcome to **TIRAMISU**, an application for handling
        combustion kinetic mechanisms (only support CHEMKIN format).

        It allows you to:
        - translate and merge mechanisms, or extract sub-mechanisms;
        - reverse reactions;
        - read NASA polynomials;
        - generate trasport properties.

        *Automatic translation and merging method: T. Fages, R. Veillet, R. Fournet, B. Sirjean, P.-A. Glaude,
        « An automatic merging method for large kinetic mechanisms »,
        DOI : 10.1016/j.ces.2024.120870*
        """
    )
    st.divider()

    import os
    import tempfile

    upload_dir = os.path.join(tempfile.gettempdir(), "tiramisu_uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # Number of mechanism containers (starts at 0: nothing shown until "+" is pressed)
    if "n_mechanisms" not in st.session_state:
        st.session_state["n_mechanisms"] = 0

    col_plus, col_reset = st.columns(2)
    with col_plus:
        if st.button("➕ Add a mechanism"):
            st.session_state["n_mechanisms"] += 1
    with col_reset:
        if st.button("🔄 Reset"):
            st.session_state["n_mechanisms"] = 0
            st.session_state["mechanism_paths"] = {}
            for key in list(st.session_state.keys()):
                if key.startswith("upload_"):
                    del st.session_state[key]

    if st.session_state["n_mechanisms"] == 0:
        st.caption("No mechanism yet. Press ➕ to add one.")

    chemins = {}  # {"mech1": [mech_1, therm_1, trans_1], ...}, '' if a file is missing
    for i in range(1, st.session_state["n_mechanisms"] + 1):
        with st.container(border=True):
            st.markdown(f"**Mechanism {i}**")
            paths_i = []
            for kind, label in [
                ("mech", "Gas-phase kinetics file"),
                ("therm", "Thermodynamics data file"),
                ("trans", "Gas transport data file"),
            ]:
                name = f"{kind}_{i}"
                uploaded = st.file_uploader(label, key=f"upload_{name}")
                if uploaded is not None:
                    chemin = os.path.join(upload_dir, uploaded.name)
                    with open(chemin, "wb") as f:
                        f.write(uploaded.getbuffer())
                    st.caption(f"File received, path: `{chemin}`")
                else:
                    chemin = ""
                    st.caption("No file provided yet.")
                paths_i.append(chemin)
            chemins[f"mech{i}"] = paths_i

    # Paths stored in session state so the other pages can use them
    st.session_state["mechanism_paths"] = chemins

    # --- Button to process: build a rmn.Model for each mechanism ---
    if st.button("⚙️ Process files"):
        # {"mech1": model1, "mech2": model2, ...}, shared with the other pages via session_state
        if "models" not in st.session_state:
            st.session_state["models"] = {}
        for mech_key, paths in chemins.items():
            path_mech, path_therm, path_trans = paths
            if not path_mech and not path_therm and not path_trans:
                continue
            try:
                # detect the encoding of the mechanism file (fallback: utf-8)
                enc = "utf-8"
                if path_mech:
                    with open(path_mech, "rb") as f:
                        enc = chardet.detect(f.read())["encoding"] or "utf-8"
                mechi = rmn.Model(path_mech, path_therm, path_trans, encoding=enc)
                st.session_state["models"][mech_key] = mechi
                st.success(f"{mech_key} — Model created : {len(mechi.spe)} species, {len(mechi.rea)} reactions (encoding: {enc})")
            except Exception as e:
                st.error(f"**{mech_key}** — Model failed: {e}")




# ============================================================
# 2. DONNÉES
# ============================================================
def page_donnees():
    st.title("📊 Données")
    st.markdown("Importez ou consultez vos données ici.")
    fichier = st.file_uploader("Déposer un fichier CSV", type=["csv"])
    if fichier is not None:
        import pandas as pd
        df = pd.read_csv(fichier)
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Aucun fichier chargé pour le moment.")


# ============================================================
# 3. ANALYSE
# ============================================================
def page_analyse():
    st.title("🔍 Analyse")
    st.markdown("Lancez une analyse sur vos données.")
    methode = st.selectbox("Méthode d'analyse", ["Résumé statistique", "Corrélation", "Détection de valeurs aberrantes"])
    seuil = st.slider("Seuil de confiance (%)", 80, 99, 95)
    if st.button("Lancer l'analyse"):
        st.success(f"Analyse « {methode} » lancée avec un seuil de {seuil} %.")


# ============================================================
# 4. VISUALISATION
# ============================================================
def page_visualisation():
    st.title("📈 Visualisation")
    st.markdown("Visualisez vos résultats sous forme de graphiques.")
    import numpy as np
    import pandas as pd
    donnees = pd.DataFrame(
        {"Mois": ["Jan", "Fév", "Mar", "Avr", "Mai", "Juin"],
         "Valeur": np.random.randint(10, 100, 6)}
    )
    type_graph = st.radio("Type de graphique", ["Barres", "Ligne", "Aire"], horizontal=True)
    if type_graph == "Barres":
        st.bar_chart(donnees.set_index("Mois"))
    elif type_graph == "Ligne":
        st.line_chart(donnees.set_index("Mois"))
    else:
        st.area_chart(donnees.set_index("Mois"))


# ============================================================
# 5. PARAMÈTRES
# ============================================================
def page_parametres():
    st.title("⚙️ Paramètres")
    st.markdown("Configurez l'application selon vos préférences.")
    with st.form("form_parametres"):
        theme = st.selectbox("Thème", ["Clair", "Sombre"])
        langue = st.radio("Langue", ["Français", "English"], horizontal=True)
        notifications = st.checkbox("Activer les notifications")
        sauvegarde = st.form_submit_button("💾 Enregistrer")
    if sauvegarde:
        st.success(f"Paramètres enregistrés : thème={theme}, langue={langue}, notifications={notifications}.")


# ============================================================
# 6. À PROPOS
# ============================================================
def page_apropos():
    st.title("ℹ️ À propos")
    st.markdown("### Mon Application Streamlit")
    st.write("Application de démonstration avec **6 fenêtres** navigables via la barre latérale.")
    st.markdown("- 🏠 Accueil\n- 📊 Données\n- 🔍 Analyse\n- 📈 Visualisation\n- ⚙️ Paramètres\n- ℹ️ À propos")
    st.caption("Conçue avec Streamlit.")


# ============================================================
# NAVIGATION ENTRE LES 6 FENÊTRES
# ============================================================
pg = st.navigation(
    {
        "Principal": [
            st.Page(page_accueil, title="Accueil", icon="🏠", default=True),
            st.Page(page_donnees, title="Données", icon="📊"),
        ],
        "Explorer": [
            st.Page(page_analyse, title="Analyse", icon="🔍"),
            st.Page(page_visualisation, title="Visualisation", icon="📈"),
        ],
        "Configuration": [
            st.Page(page_parametres, title="Paramètres", icon="⚙️"),
            st.Page(page_apropos, title="À propos", icon="ℹ️"),
        ],
    }
)

pg.run()
