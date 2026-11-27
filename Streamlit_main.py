# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 16:16:23 2026

@author: fages1
"""

import streamlit as st
import read_model_new_streamlit as rmn
import make_translation_streamlit as mt
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

#    # --- Shown only after Process has been used: pick one compiled mechanism ---
#    models = st.session_state.get("models", {})
#    if models:
#        # the widget stores its value in st.session_state["selected_mechanism"] by itself
#        st.selectbox(
#            "Select a compiled mechanism",
#            list(models.keys()),
#            key="selected_mechanism",
#        )

def page_translation():
    st.title("🔀 Translation")
    st.markdown(
        """
        **Translate automatically the species from one model into another.**

        Species are grouped into isomer families and matched between the two mechanisms
        by comparing their Gibbs energy ΔG°/RT (computed from the NASA polynomials) over the
        whole temperature range, using the NMAD criterion. Two matching methods are combined:
        best pairwise NMAD first, then the best permutation of the whole isomer group
        (mean-NMAD). A translation is kept only when a confidence threshold is met; otherwise
        it is left to an assisted manual step, helped by comparing the reactions involving
        the species in both mechanisms.
        """
    )
    st.divider()

    models = st.session_state.get("models", {})
    if not models:
        st.info("No mechanism compiled yet. Go to TIRAMISU, add mechanisms and press ⚙️ Process files.")
        return

    # --- Bar like on the home page: pick a source mechanism, an arrow, a target mechanism ---
    with st.container(border=True):
        col_from, col_arrow, col_to = st.columns([3, 1, 3])
        with col_from:
            mech_from = st.selectbox("From mechanism", list(models.keys()), key="trans_from")
        with col_arrow:
            st.markdown(
                "<svg width='60' height='24' style='display:block;margin:auto'>"
                "<defs><marker id='arrowhead' markerWidth='8' markerHeight='8' refX='6' refY='3' orient='auto'>"
                "<path d='M0,0 L6,3 L0,6 z' fill='black'/></marker></defs>"
                "<line x1='0' y1='12' x2='52' y2='12' stroke='black' stroke-width='2' marker-end='url(#arrowhead)'/>"
                "</svg>",
                unsafe_allow_html=True,
            )
            # free text input: no +/- steppers, accepts scientific notation (1e15)
            raw = st.text_input(
                "Maximum number of permutations",
                value="10000",
                key="trans_max_perm",
            )
            try:
                max_perm = int(float(raw))
            except ValueError:
                st.warning("Invalid number, falling back to 10000.")
                max_perm = 10000
        with col_to:
            mech_to = st.selectbox("To mechanism", list(models.keys()), key="trans_to")

    # --- Translate button: does nothing if a mechanism is missing or both are the same ---
    if st.button("🔀 Translate"):
        if not mech_from or not mech_to or mech_from == mech_to:
            st.info("Select two different mechanisms to translate.")
        else:
            try:
                result = mt.streamlit_translation(
                    st.session_state["models"][mech_from],
                    st.session_state["models"][mech_to],
                    max_perm,
                )
                st.session_state["translation_result"] = result
                st.success(
                    f"Translation **{mech_from}** into **{mech_to}** done "
                    f"(maximum number of permutations: {max_perm})."
                )
            except Exception as e:
                st.error(f"Translation **{mech_from}** → **{mech_to}** failed: {e}")

    # --- Display the translation result: one container per member of the list ---
    result = st.session_state.get("translation_result")
    if result:
        for member in result:
            with st.container(border=True):
                st.markdown(f"**{member.name}** — atomic composition: `{member.atomic_composition}`")
                if member.translations != {}:
                    for sub_group in member.translations:
                        col_key, col_sel = st.columns([1, 2])
                        with col_key:
                            st.write(sub_group)
                        with col_sel:
                            st.selectbox(
                                f"Translation of {sub_group}",
                                member.model2_species,
                                key=f"trans_{member.name}_{sub_group}",
                            )
            
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
            st.Page(page_translation, title="Translation", icon="🔀")
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
