def page_accueil():
    st.title("🍮 TIRAMISU")
    st.markdown(
        """
        Welcome to **TIRAMISU**, an application for handling
        combustion kinetic mechanisms (only support CHEMKIN format).

        It allows you to:
        - translate and merge mechanisms, or extract sub-mechanisms;
        - reverse reactions;
        - read NASA polynomials.

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

    # --- Button to process the paths: show the first line of each file ---
    if st.button("⚙️ Process files"):
        for mech_key, paths in chemins.items():
            for kind, chemin in zip(["mech", "therm", "trans"], paths):
                if not chemin:
                    continue
                try:
                    with open(chemin, "r", encoding="utf-8", errors="replace") as f:
                        first_line = f.readline().strip()
                except OSError as e:
                    st.error(f"**{mech_key}/{kind}** (`{chemin}`) — cannot read file: {e}")
                    continue
                if first_line:
                    st.write(f"**{mech_key}/{kind}** (`{chemin}`) — first line: `{first_line}`")
