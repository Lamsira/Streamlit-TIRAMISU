# -*- coding: utf-8 -*-
"""
Created on Wed Nov 25 16:16:23 2026

@author: fages1
"""

import streamlit as st

st.set_page_config(
    page_title="TIRAMISU",
    page_icon="🗂️",
    layout="wide",
)


def page_accueil():
    st.title("🍮 TIRAMISU")
    st.markdown(
    """
    Bienvenue dans **TIRAMISU**, une application de manipulation de
    mécanismes cinétiques de combustion (format CHEMKIN).

    Elle permet notamment de :
    - traduire et fusionner des mécanismes entre eux, ou d'en extraire des sous-mécanismes ;
    - inverser des réactions ;
    - lire des polynômes NASA.

    *Méthode de traduction, fusion et extraction automatique : T. Fages, R. Veillet, R. Fournet, B. Sirjean, P.-A. Glaude,
    « An automatic merging method for large kinetic mechanisms »,
    DOI : 10.1016/j.ces.2024.120870*
    """
    )   
    st.divider()
    st.subheader("📂 Fichiers à traiter")
    for i, nom in enumerate(["Mécanisme 1", "Mécanisme 2", "Fichier supplémentaire"], start=1):
        with st.container(border=True):
            st.markdown(f"**{nom}**")
            fichier = st.file_uploader(
                f"Déposer un fichier ({nom})",
                type=["txt", "csv", "dat", "inp", "ck"],
                key=f"upload_{i}",
            )
            chemin = st.text_input(
                f"Ou indiquer le chemin du fichier ({nom})",
                placeholder="/chemin/vers/fichier.txt",
                key=f"path_{i}",
            )
            if fichier is not None:
                st.caption(f"Fichier déposé : {fichier.name}")
            elif chemin:
                st.caption(f"Chemin saisi : `{chemin}`")
    # col1, col2, col3 = st.columns(3)
    # with col1:
    #     st.metric("Fenêtres", "6")
    # with col2:
    #     st.metric("Version", "1.0")
    # with col3:
    #     st.metric("Statut", "OK")
    # st.info("Astuce : cliquez sur une page dans la barre latérale pour changer de fenêtre.")


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
