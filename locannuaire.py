import requests
import numpy as np
import pandas as pd
import streamlit as st


# FONCTIONS #
@st.cache
def load_data(url):
    return pd.read_csv(url)


# API CONFIG #
pappers_key = '0036e5513cdb2eb3135d2d96f81760dc46452322158e1edd'
pappers_enterprise = 'https://api.pappers.fr/v2/entreprise'
pappers_reaserch = 'https://api.pappers.fr/v2/recherche'


# DATA #
FLPM_PRS = 'https://github.com/MickaelKohler/PopMyData/raw/main/Data/FLPM_PRS.csv'
FLPM_BDX = 'https://github.com/MickaelKohler/PopMyData/raw/main/Data/FLPM_BDX.csv'
FLPM_LIL = 'https://github.com/MickaelKohler/PopMyData/raw/main/Data/FLPM_LIL.csv'


# MAIN PAGE #
st.title('Bienvenu sur PopMyData')
st.subheader('Outil de prospection des locaux commerciaux')
st.title(' ')

# choose city
category = st.selectbox('Choisissez une ville',
                        [
                            {'city': 'Paris',
                             'data': FLPM_PRS},
                            {'city': 'Bordeaux',
                             'data': FLPM_BDX},
                            {'city': 'Lille',
                             'data': FLPM_LIL}
                        ],
                        format_func=lambda option: option['city'])

# load data of the city
flpm = load_data(category['data'])
address_temp = flpm['Nom voie (Adresse du local)'].unique()

# choose address
col1, col2 = st.beta_columns([1, 2])
with col1:
    numb = st.number_input('Numéro de rue :', value=1, step=1,
                           help="Ne pas indiquer l'indice de répétition")
with col2:
    street = st.selectbox('Selectionnez le nom de la rue', address_temp,
                          help='Ne pas indiquer le type de rue (cours, allée, etc)')

# filter data
search = flpm[(flpm['Nom voie (Adresse du local)'] == street) &
              (flpm['N° voirie (Adresse du local)'] == numb)]

# if multiple owners, select one
if search.shape[0] > 1:
    st.title(' ')
    st.markdown('Il y a plusieurs propriétaires à cette adresse :')
    select = search[['Dénomination (Propriétaire(s) du local)',
                     'Forme juridique abrégée (Propriétaire(s) du local)',
                     'N° SIREN (Propriétaire(s) du local)',
                     'Section (Références cadastrales)',
                     'Bâtiment (Identification du local)',
                     'Indice de répétition (Adresse du local)']]
    select.drop_duplicates(['N° SIREN (Propriétaire(s) du local)'], inplace=True)
    st.dataframe(select)
    name = st.selectbox("Selectionnez le nom du propriétaire souhaité",
                        list(select['Dénomination (Propriétaire(s) du local)']))
    search = search[search['Dénomination (Propriétaire(s) du local)'] == name]

st.title(' ')
requete = st.button('Rechercher')
st.markdown('___')

if requete:
    # if no owner found
    if search.shape[0] == 0:
        st.markdown("Il n'y a pas de propriétaire de local commercial identifié à cette adresse")
        any_soc = False
    # if siren is false
    elif any(search['N° SIREN (Propriétaire(s) du local)'].str.contains('U')) or any(search['N° SIREN (Propriétaire(s) du local)'] == np.nan):
        name = search['Dénomination (Propriétaire(s) du local)']
        info = requests.get(pappers_reaserch, params={'api_token': pappers_key, 'q': name, 'precision': 'exacte'})
        societe = info.json()
        siren = societe['resultats'][0]['siren']
        any_soc = True
    # if siren is good
    else:
        siren = search['N° SIREN (Propriétaire(s) du local)']
        any_soc = True

    # if siren found
    if any_soc:
        info = requests.get(pappers_enterprise, params={'api_token': pappers_key, 'siren': siren})
        status = info.json()

        # display the address
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
