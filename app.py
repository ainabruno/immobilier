import streamlit as st
import pandas as pd
import os
from ton_script_scraping import main  # ta fonction de scraping

st.markdown(
    """
    <style>
    /* Custom styles to approximate Tailwind look */
    .title {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1.5rem;
    }
    .section {
        background: white;
        padding: 1rem;
        border-radius: 0.5rem;
        box-shadow: 0 2px 6px rgb(0 0 0 / 0.1);
        margin-bottom: 1.5rem;
    }
    .label {
        font-weight: 600;
        margin-bottom: 0.25rem;
        display: block;
        font-size: 0.9rem;
        color: #374151;
    }
    .input, select {
        width: 100%;
        padding: 0.5rem;
        border-radius: 0.375rem;
        border: 1px solid #d1d5db;
        font-size: 1rem;
        outline-offset: 2px;
    }
    .input:focus, select:focus {
        border-color: #3b82f6;
        box-shadow: 0 0 0 2px #bfdbfe;
        outline: none;
    }
    .btn-primary {
        background-color: #2563eb;
        color: white;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
        border-radius: 0.5rem;
        border: none;
        cursor: pointer;
        transition: background-color 0.2s;
        margin-top: 1rem;
    }
    .btn-primary:hover {
        background-color: #1d4ed8;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown('<div class="container mx-auto p-4 max-w-7xl">', unsafe_allow_html=True)

st.markdown('<h1 class="title">Recherche Immobilière</h1>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="section">', unsafe_allow_html=True)
    col1, col2 = st.columns([4,1])
    with col1:
        # ville_input = st.text_input("", placeholder="Rechercher un bien, une ville...")
        ville_input = st.text_input("Ville", placeholder="Rechercher un bien, une ville...", label_visibility="collapsed")

    with col2:
        if st.button("Rechercher", key="btn_rechercher"):
            # st.experimental_rerun()
            st.rerun()

    st.markdown('</div>', unsafe_allow_html=True)

with st.container():
    st.markdown('<div class="section">', unsafe_allow_html=True)
    st.markdown('<h2 class="label">Filtres de recherche</h2>', unsafe_allow_html=True)
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        localisation = st.text_input("Localisation", value="Paris", key="localisation")
    with col2:
        type_bien_label = st.selectbox(
            "Type de bien",
            ["Maison", "Appartement", "Terrain", "Parking", "Autre"],
            key="type_bien_filtre"
        )
    with col3:
        prix_min = st.number_input("Prix min (€)", min_value=0, value=50000, step=1000, key="prix_min")
    with col4:
        prix_max = st.number_input("Prix max (€)", min_value=0, value=100000, step=1000, key="prix_max")
    
    col5, col6 = st.columns(2)
    with col5:
        tri_par = st.selectbox("Trier par", ["Prix", "Pertinence"], key="tri_par")
    with col6:
        ordre = st.selectbox("Ordre", ["Croissant", "Décroissant"], key="ordre")

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<div class="section">', unsafe_allow_html=True)
st.markdown('<div class="text-center">', unsafe_allow_html=True)

# Bouton Lancer le scraping
if st.button("Lancer le scraping", key="btn_lancer_scraping"):
    st.info("⏳ Scraping en cours... cela peut prendre un moment.")
    # Appelle ta fonction main adaptée
    # Exemple d'adaptation des valeurs (ajuste selon ta logique)
    ville = localisation if localisation else "Toulouse"
    type_bien = "1" if type_bien_label == "Maison" else "2"
    pieces_min = 3  # tu peux ajouter un slider si besoin
    prix_max_val = prix_max

    main(ville, type_bien, pieces_min, prix_max_val, "")  # sans mail ici

    nom_fichier = f"annonces_{ville.lower()}_{type_bien}_{prix_max_val}eu.csv"
    if os.path.exists(nom_fichier) and os.path.getsize(nom_fichier) > 0:
        try:
            df = pd.read_csv(nom_fichier)
            if df.empty:
                st.warning("✅ Scraping terminé, mais aucune annonce n'a été trouvée.")
            else:
                st.success("✅ Scraping terminé, fichier exporté.")
                st.dataframe(df)
        except Exception as e:
            st.error(f"❌ Erreur lors de la lecture du fichier : {e}")
    else:
        st.warning("⚠️ Aucun fichier exporté ou fichier vide.")

st.markdown('</div></div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)


