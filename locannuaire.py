import requests
import numpy as np
import pandas as pd
import streamlit as st


# FONCTIONS #
@st.cache
def load_data(url):
    return pd.read_csv(url)


def clean_soc_name(soc_name):
    """Clean the enterprise's name"""
    ban_words = ['SA', 'SOCIETE', 'CIVILE', 'IMMOBILIERE']
    search_name = []
    for word in soc_name.split():
        if word not in ban_words:
            search_name.append(word)
    return ' '.join(search_name)


def print_associates(indice, db):
    """Print associates names"""
    gerant = db['representants'][indice]
    fonction = db['representants'][indice]['qualite'].split()[0].upper()
    nom_gerant = gerant['nom_complet']
    try:
        situation = f"né le {gerant['date_de_naissance_formate']}, {gerant['age']} ans"
    except KeyError:
        try:
            situation = f"siren : {gerant['siren']}"
        except KeyError:
            situation = ' '

    if gerant['adresse_ligne_1'] is not None:
        ad1_gerant = gerant['adresse_ligne_1'].lower()
    else:
        ad1_gerant = ' '
    if gerant['adresse_ligne_2'] is not None:
        ad2_gerant = gerant['adresse_ligne_2'].lower()
    else:
        ad2_gerant = ' '
    ad3_gerant = f"{gerant['code_postal']} - {gerant['ville']} ({gerant['pays'].capitalize()})"
    return f"""
        **{fonction}** : \n
        {nom_gerant} \n
        {situation} \n
        {ad1_gerant} \n
        {ad2_gerant} \n
        {ad3_gerant}
        """


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
    any_soc = False
    if search.shape[0] == 0:
        st.markdown(
            """
            Il n'y a pas de propriétaire identifié pour le de local commercial situé à cette adresse, 
            ou l'adresse indiquée n'existe pas
            """)
    # if siren is false
    elif any(search['N° SIREN (Propriétaire(s) du local)'].str.contains('U')) or any(search['N° SIREN (Propriétaire(s) du local)'] == np.nan):
        name = search['Dénomination (Propriétaire(s) du local)']
        clean_name = clean_soc_name(name.iloc[0])
        info = requests.get(pappers_reaserch, params={'api_token': pappers_key, 'q': clean_name})
        societe = info.json()
        if societe['total'] == 0:
            st.markdown(
                f"""
                La société n'a pas pu être correctement identifiée. 
                Nous vous invitons à effectuer manuellement la recherche de la société **{name.iloc[0]}**.
                """)
        else:
            siren = societe['resultats'][0]['siren']
            any_soc = True

    # if siren is good
    else:
        siren = search['N° SIREN (Propriétaire(s) du local)'].drop_duplicates().iloc[0]
        print(siren)
        any_soc = True

    # if siren found
    if any_soc:
        info = requests.get(pappers_enterprise, params={'api_token': pappers_key, 'siren': siren})
        status = info.json()

        try:
            # display the address
            siege = status['siege']
            nom_soc = status['denomination']
            col1, col2 = st.beta_columns(2)
            with col1:
                if siege['adresse_ligne_1'] is not None:
                    ad1_soc = siege['adresse_ligne_1'].lower()
                else:
                    ad1_soc = ' '
                if siege['adresse_ligne_2'] is not None:
                    ad2_soc = siege['adresse_ligne_2'].lower()
                else:
                    ad2_soc = ' '
                ad3_soc = f"{siege['code_postal']} - {siege['ville']} ({siege['pays']})"

                st.markdown(
                    f"""
                    **SIEGE** : \n
                    {nom_soc}\n
                    {ad1_soc.lower()} \n
                    {ad2_soc.lower()} \n
                    {ad3_soc}
                    """)
            with col2:
                if len(status['representants']) == 1:
                    st.markdown(print_associates(0, status))

            st.title(' ')
            index = 0
            if len(status['representants']) > 1:
                for ligne in range((len(status['representants'])//2)):
                    cols = st.beta_columns(2)
                    for i, col in enumerate(cols):
                        col.markdown(print_associates(index, status))
                        index += 1
                    st.title(' ')
                if len(status['representants']) % 2 == 1:
                    col1, col2 = st.beta_columns(2)
                    with col1:
                        st.markdown(print_associates(index, status))

        except KeyError:
            st.markdown(
                f"""
                Une erreure s'est produite lors de la récupération des données.
                Nous vous invitons à effectuer manuellement la recherche de la société
                **{search['Dénomination (Propriétaire(s) du local)'].iloc[0]}**, 
                numéro de **SIREN {siren}**.
                """)
