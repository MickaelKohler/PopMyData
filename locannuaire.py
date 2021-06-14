import requests
import numpy as np
import pandas as pd
import streamlit as st
from geopy.geocoders import BANFrance


# FONCTIONS
@st.cache
def load_data(url):
    return pd.read_csv(url)


# API CONFIG
geolocator = BANFrance(user_agent="mygeo")

key = '0036e5513cdb2eb3135d2d96f81760dc46452322158e1edd'
pappers_enterprise = 'https://api.pappers.fr/v2/entreprise'
pappers_reaserch = 'https://api.pappers.fr/v2/recherche'


# DATA
FLPM_PRS = 'https://github.com/MickaelKohler/PopMyData/raw/main/Data/FLPM_PRS.csv'
FLPM_BDX = 'https://github.com/MickaelKohler/PopMyData/raw/main/Data/FLPM_BDX.csv'
FLPM_LIL = 'https://github.com/MickaelKohler/PopMyData/raw/main/Data/FLPM_LIL.csv'


# MAIN PAGE
st.title('Bienvenu sur PopMyData')
st.subheader('Outil de prospection des locaux commerciaux')

category = st.selectbox('Choisissez une ville',
                        [
                            {'city': 'Paris',
                             'data': FLPM_PRS},
                            {'city': 'Bordeaux',
                             'data': FLPM_BDX},
                            {'city': 'Lille',
                             'data': FLPM_LIL}
                        ],
                        format_func=lambda option:option['city'])

flpm = load_data(category['data'])

with st.form(key='local_finder'):
    col1, col2 = st.beta_columns([1, 2])
    with col1:
        numb = st.number_input('Numéro de rue :', value=1, step=1)
    with col2:
        street = st.selectbox('Selectionnez la rue', flpm['Nom voie (Adresse du local)'])
    submit = st.form_submit_button('Rechercher')

search = flpm[(flpm['Nom voie (Adresse du local)'] == street) &
              (flpm['N° voirie (Adresse du local)'] == numb)]

if search.shape[0] > 1:
    st.markdown('Il y a plusieurs propriétaires à cette adresse.')
    select = search[['Dénomination (Propriétaire(s) du local)',
                     'Forme juridique abrégée (Propriétaire(s) du local)',
                     'N° SIREN (Propriétaire(s) du local)',
                     'Section (Références cadastrales)',
                     'Bâtiment (Identification du local)',
                     'Indice de répétition (Adresse du local)']]
    select.drop_duplicates(['N° SIREN (Propriétaire(s) du local)'], inplace=True)
    st.dataframe(select)
    index = st.selectbox("Selectionner l'index du propriétaire souhaité", select.index)
    search = search[search.index == index]

if search.shape[0] == 0:
    st.markdown("Il n'y a pas de propriétaire de local commercial identifié à cette adresse")
else:
    # search on pappers
    if any(search['N° SIREN (Propriétaire(s) du local)'].str.contains('U')) or any(search['N° SIREN (Propriétaire(s) du local)'] == np.nan):
        name = search['Dénomination (Propriétaire(s) du local)']
        info = requests.get(pappers_reaserch, params={'api_token': key, 'q': name, 'precision': 'exacte'})
        societe = info.json()
        siren = societe['resultats'][0]['siren']
    else:
        siren = search['N° SIREN (Propriétaire(s) du local)']

    # request
    info = requests.get(pappers_enterprise, params={'api_token': key, 'siren': siren})
    status = info.json()

    st.markdown('___')

    col1, col2 = st.beta_columns(2)
    with col1:
        siege = status['siege']
        st.markdown(
            f"""
            **SIEGE** : \n
            {status['denomination']},\n
            {siege['adresse_ligne_1'].lower()}, \n
            {siege['code_postal']} - {siege['ville']} ({siege['pays']})
            """)

    with col2:
        gerant = status['representants'][0]
        nom_gerant = gerant['nom_complet']
        age_gerant = f"{gerant['date_de_naissance_formate']}, {gerant['age']} ans"
        ad1_gerant = gerant['adresse_ligne_1']
        ad2_gerant = f"{gerant['code_postal']} - {gerant['ville'].upper()} ({gerant['pays']})"

        st.markdown(
            f"""
            **GERANT** : \n
            {nom_gerant}  - {age_gerant} \n
            {ad1_gerant}, \n
            {ad2_gerant}
            """)