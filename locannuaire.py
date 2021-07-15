import requests
from fuzzywuzzy import fuzz
import folium
from folium import plugins
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static
from geopy.distance import distance

# CONFIG #

st.set_page_config(page_title="Locannuaire",
                   page_icon="🏠",
                   initial_sidebar_state="collapsed",
                   )

# Si on modifie le background
#    .reportview-container {
#       background: url("https://www.mypopupstore.fr/wp-content/uploads/2018/03/mpups_evenement.png");
#       background-size: cover}

st.markdown("""
    <style>
    .titre {
        font-size:16px;
        font-weight:normal;
        margin:0px;
    }
    .text {
        font-size:16px;
        font-weight:normal;
        color:lightgray;
    }
    .sous_indice {
        font-size:60px;
        font-weight:bold;
    }
    .indice_total {
        font-size:100px;
        font-weight:bold;
    }
    </style>
    """, unsafe_allow_html=True)


# FONCTIONS #


@st.cache(allow_output_mutation=True)
def load_data(url, sep=','):
    return pd.read_csv(url, sep=sep)


def clean_metro_paris(stop_name):
    station = stop_name.upper().replace(' - ', ' ')
    internat = {
        'À': 'A',
        'Â': 'A',
        'Ç': 'C',
        'É': 'E',
        'Ê': 'E',
        'È': 'E',
        'Ë': 'E',
        "'": ' ',
        "’": ' ',
        "-": ' ',
    }
    return ''.join(
        internat[letter] if letter in internat else letter for letter in station
    )


def search_engine(search_street, adresses):
    """
    :param search_street: takes an address selected by the user
    :param adresses: list of addresses
    :return: a dict with all addresses if the match is over 80% between user's address and addresses in the list
    """
    internat = {
        'À': 'A',
        'Â': 'A',
        'Ç': 'C',
        'É': 'E',
        'Ê': 'E',
        'È': 'E',
        'Ë': 'E',
        "'": ' ',
        "’": ' ',
        "-": ' ',
    }

    cible = ''.join(
        internat[letter] if letter in internat else letter
        for letter in search_street.strip().upper()
    )

    return {
        adresse: fuzz.ratio(cible, adresse)
        for adresse in adresses
        if fuzz.ratio(cible, adresse) > 80
    }


def city_park(depatement, data):
    """Return park database for specified location"""
    data['insee'] = data['insee'].astype(str)
    database = data[data['insee'].str.contains(f'{str(depatement)}...')]
    return database[['Xlong', 'Ylat', 'nom', 'nb_places', 'gratuit', 'adresse']]


def clean_soc_name(soc_name):
    """Clean the enterprise's name"""
    ban_words = ['SA', 'SOCIETE', 'CIVILE', 'IMMOBILIERE']
    search_name = [word for word in soc_name.split() if word not in ban_words]
    return ' '.join(search_name)


def population_rating(table):
    """
    Add the column rates to the table index_population.
    :param table: table created when an address is specified by user
    :return: same table with rates
    """
    # population number
    if table.iloc[0, 0] >= 2000:
        table.iloc[0, 1] = 6
    elif table.iloc[0, 0] >= 1000:
        table.iloc[0, 1] = 10
    elif table.iloc[0, 0] >= 200:
        table.iloc[0, 1] = 4

    # median income
    if table.iloc[1, 0] >= 30000:
        table.iloc[1, 1] = 10
    elif table.iloc[1, 0] >= 25000:
        table.iloc[1, 1] = 8
    elif table.iloc[1, 0] >= 20000:
        table.iloc[1, 1] = 6
    elif table.iloc[1, 0] >= 15000:
        table.iloc[1, 1] = 4
    elif table.iloc[1, 0] >= 10000:
        table.iloc[1, 1] = 2
    return table


def visibility_rating(table, departement):
    """
    Add the column rates to the table index_visibility
    :param table: table created when an address is specified by user
    :param departement: departement
    :return: same table with rates
    """
    # transport flow
    if departement == 75:
        if table.iloc[5, 0] >= 20000:
            table.iloc[5, 1] = 9
        elif table.iloc[5, 0] >= 10000:
            table.iloc[5, 1] = 6
        elif table.iloc[5, 0] >= 5000:
            table.iloc[5, 1] = 3

    if departement == 59:
        if table.iloc[5, 0] >= 10000:
            table.iloc[5, 1] = 9
        elif table.iloc[5, 0] >= 5000:
            table.iloc[5, 1] = 6
        elif table.iloc[5, 0] >= 2500:
            table.iloc[5, 1] = 3

    if departement in [75, 59]:
        coef_bar_max = -3
        coef_bar_mid = -2
        coef_mall = 1
        if table.iloc[0, 0] >= 100:
            table.iloc[0, 1] = 20
        elif table.iloc[0, 0] >= 70:
            table.iloc[0, 1] = 17
        elif table.iloc[0, 0] >= 50:
            table.iloc[0, 1] = 14
        elif table.iloc[0, 0] >= 40:
            table.iloc[0, 1] = 10
        elif table.iloc[0, 0] >= 30:
            table.iloc[0, 1] = 6
        elif table.iloc[0, 0] >= 20:
            table.iloc[0, 1] = 3
        elif table.iloc[0, 0] >= 10:
            table.iloc[0, 1] = 1
    else:
        if table.iloc[0, 0] >= 100:
            table.iloc[0, 1] = 30
        elif table.iloc[0, 0] >= 70:
            table.iloc[0, 1] = 25
        elif table.iloc[0, 0] >= 50:
            table.iloc[0, 1] = 20
        elif table.iloc[0, 0] >= 40:
            table.iloc[0, 1] = 15
        elif table.iloc[0, 0] >= 30:
            table.iloc[0, 1] = 10
        elif table.iloc[0, 0] >= 20:
            table.iloc[0, 1] = 5
        elif table.iloc[0, 0] >= 10:
            table.iloc[0, 1] = 1
        coef_bar_max = -5
        coef_bar_mid = -3
        coef_mall = 3

    # bar and restaurants proportion
    if table.iloc[1, 0] >= 90:
        table.iloc[1, 1] = coef_bar_max
    elif table.iloc[1, 0] >= 60:
        table.iloc[1, 1] = coef_bar_mid
    elif table.iloc[1, 0] >= 10:
        table.iloc[1, 1] = 0
    elif table.iloc[1, 0] <= 10:
        table.iloc[1, 1] = -1

    # malls
    table.iloc[2, 1] = coef_mall if table.iloc[2, 0] >= 1 else 0
    return table


def access_rating(table):
    """
    Add the column rates to the table index_access.
    :param table: table created when an address is specified by user
    :return: same table with rates
    """
    table.iloc[0, 1] = 4 if table.iloc[0, 0] >= 1 else 0                     # Gare
    table.iloc[1, 1] = 7 if table.iloc[1, 0] >= 3 else table.iloc[1, 0] * 2  # Metro Tram
    table.iloc[2, 1] = 7 if table.iloc[2, 0] >= 3 else table.iloc[2, 0] * 2  # Bus
    table.iloc[3, 1] = 6 if table.iloc[3, 0] >= 3 else table.iloc[3, 0] * 2  # Velo libre Service
    table.iloc[4, 1] = 6 if table.iloc[4, 0] >= 3 else table.iloc[4, 0] * 2  # Parkings
    return table


def district_rating(table):
    """
    Add the column rates to the table index_district.
    :param table: table created when an address is specified by user
    :return: same table with rates
    """
    table.iloc[0, 1] = 1 if table.iloc[0, 0] >= 1 else 0                             # Post Office
    table.iloc[1, 1] = 1 if table.iloc[1, 0] >= 1 else 0                             # primary school
    table.iloc[2, 1] = 1 if table.iloc[2, 0] >= 1 else 0                             # middle/high school
    table.iloc[3, 1] = min(table.iloc[3, 0], 4)                                      # University
    table.iloc[4, 1] = 2 if table.iloc[4, 0] >= 1 else 0                             # Sport
    table.iloc[5, 1] = 2 if table.iloc[5, 0] >= 1 else 0                             # Cinema
    table.iloc[6, 1] = 2 if table.iloc[6, 0] >= 1 else 0                             # Museum
    table.iloc[7, 1] = 1 if table.iloc[7, 0] >= 1 else 0                             # Library
    table.iloc[8, 1] = 6 if table.iloc[8, 0] >= 12 else int(table.iloc[8, 0] * 0.5)  # Hotel
    return table


def carte(df, coord):
    m = folium.Map(location=coord, zoom_start=16)

    marker_adresse = folium.Marker(location=coord)
    marker_adresse.add_to(m)

    mcg = plugins.MarkerCluster(control=False)
    m.add_child(mcg)

    # Création des couches pour chaques types de magasins
    g1 = folium.plugins.FeatureGroupSubGroup(mcg, "Tout", show=True)
    m.add_child(g1)
    g2 = folium.plugins.FeatureGroupSubGroup(mcg, "restaurant", show=False)
    m.add_child(g2)
    g3 = folium.plugins.FeatureGroupSubGroup(mcg, "Vetements", show=False)
    m.add_child(g3)
    g4 = folium.plugins.FeatureGroupSubGroup(mcg, "Beauté", show=False)
    m.add_child(g4)
    g5 = folium.plugins.FeatureGroupSubGroup(mcg, "Bar", show=False)
    m.add_child(g5)
    g6 = folium.plugins.FeatureGroupSubGroup(mcg, "Boulangerie", show=False)
    m.add_child(g6)
    g7 = folium.plugins.FeatureGroupSubGroup(mcg, "Café", show=False)
    m.add_child(g7)
    g8 = folium.plugins.FeatureGroupSubGroup(mcg, "Banques", show=False)
    m.add_child(g8)
    g9 = folium.plugins.FeatureGroupSubGroup(mcg, "pharmacie", show=False)
    m.add_child(g9)
    g10 = folium.plugins.FeatureGroupSubGroup(mcg, "commodité", show=False)
    m.add_child(g10)
    g11 = folium.plugins.FeatureGroupSubGroup(mcg, "Supermarché", show=False)
    m.add_child(g11)
    g12 = folium.plugins.FeatureGroupSubGroup(mcg, "Opticien", show=False)
    m.add_child(g12)
    g13 = folium.plugins.FeatureGroupSubGroup(mcg, "Fleuriste", show=False)
    m.add_child(g13)
    g14 = folium.plugins.FeatureGroupSubGroup(mcg, "Bijouterie", show=False)
    m.add_child(g14)
    g15 = folium.plugins.FeatureGroupSubGroup(mcg, "Centre commercial", show=False)
    m.add_child(g15)

    for number, row in df[["X", "Y", "name", "type"]].iterrows():
        if row["type"] == "restaurant":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-cutlery", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-cutlery", prefix='fa')).add_to(g2)
        elif row["type"] == "clothes":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-black-tie", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-black-tie", prefix='fa')).add_to(g3)
        elif row["type"] == "beauty":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-scissors", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-scissors", prefix='fa')).add_to(g4)
        elif row["type"] == "bar":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-beer", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-beer", prefix='fa')).add_to(g5)
        elif row["type"] == "bakery":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-bold", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-bold", prefix='fa')).add_to(g6)
        elif row["type"] == "cafe":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-coffee", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-coffee", prefix='fa')).add_to(g7)
        elif row["type"] == "bank":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-bank", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-bank", prefix='fa')).add_to(g8)
        elif row["type"] == "pharmacy":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-plus", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-plus", prefix='fa')).add_to(g9)
        elif row["type"] == "convenience":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-shopping-basket", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-shopping-basket", prefix='fa')).add_to(g10)
        elif row["type"] == "supermarket":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-shopping-bag", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-shopping-bag", prefix='fa')).add_to(g11)
        elif row["type"] == "optician":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-eye", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-eye", prefix='fa')).add_to(g12)
        elif row["type"] == "florist":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-leaf", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-leaf", prefix='fa')).add_to(g13)
        elif row["type"] == "jewelry":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-diamond", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-diamond", prefix='fa')).add_to(g14)
        elif row["type"] == "department_store":
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-cart-plus", prefix='fa')).add_to(g1)
            folium.Marker(location=[row["Y"], row["X"]], popup=row["name"],
                          icon=folium.Icon(color="cadetblue", icon="fa-cart-plus", prefix='fa')).add_to(g15)

    # Les heatmaps
    plugins.HeatMap(df[["Y", "X"]], min_opacity=0.4).add_to(g1)
    plugins.HeatMap(df[df['type'] == "restaurant"][["Y", "X"]], min_opacity=0.4).add_to(g2)
    plugins.HeatMap(df[df['type'] == "clothes"][["Y", "X"]], min_opacity=0.4).add_to(g3)
    plugins.HeatMap(df[df['type'] == "beauty"][["Y", "X"]], min_opacity=0.4).add_to(g4)
    plugins.HeatMap(df[df['type'] == "bar"][["Y", "X"]], min_opacity=0.4).add_to(g5)
    plugins.HeatMap(df[df['type'] == "bakery"][["Y", "X"]], min_opacity=0.4).add_to(g6)
    plugins.HeatMap(df[df['type'] == "cafe"][["Y", "X"]], min_opacity=0.4).add_to(g7)
    plugins.HeatMap(df[df['type'] == "bank"][["Y", "X"]], min_opacity=0.4).add_to(g8)
    plugins.HeatMap(df[df['type'] == "pharmacy"][["Y", "X"]], min_opacity=0.4).add_to(g9)
    plugins.HeatMap(df[df['type'] == "convenience"][["Y", "X"]], min_opacity=0.4).add_to(g10)
    plugins.HeatMap(df[df['type'] == "supermarket"][["Y", "X"]], min_opacity=0.4).add_to(g11)
    plugins.HeatMap(df[df['type'] == "optician"][["Y", "X"]], min_opacity=0.4).add_to(g12)
    plugins.HeatMap(df[df['type'] == "florist"][["Y", "X"]], min_opacity=0.4).add_to(g13)
    plugins.HeatMap(df[df['type'] == "jewelry"][["Y", "X"]], min_opacity=0.4).add_to(g14)
    plugins.HeatMap(df[df['type'] == "department_store"][["Y", "X"]], min_opacity=0.4).add_to(g15)

    minimap = plugins.MiniMap()
    m.add_child(minimap)

    plugins.LocateControl().add_to(m)

    plugins.Fullscreen(
        position="topleft",
        title="Expand me",
        title_cancel="Exit me",
        force_separate_button=True,
    ).add_to(m)

    plugins.SemiCircle(
        coord,
        radius=400,
        direction=360,
        arc=359.99,
        color="red",
        fill_color="red",
        opacity=0,
    ).add_to(m)

    plugins.SemiCircle(
        coord,
        radius=200,
        direction=360,
        arc=359.99,
        color="red",
        fill_color="red",
        opacity=0,
    ).add_to(m)

    plugins.Geocoder(position="bottomleft").add_to(m)

    folium.LayerControl(collapsed=True).add_to(m)

    return m


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
            if gerant['siren'] is None:
                situation = ' '
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

PYRIS_link = 'https://pyris.datajazz.io/api/coords'
pappers_key = '0036e5513cdb2eb3135d2d96f81760dc46452322158e1edd'
pappers_enterprise = 'https://api.pappers.fr/v2/entreprise'
pappers_reaserch = 'https://api.pappers.fr/v2/recherche'

type_name = 'shoes|garden_center|department_store|cosmetics|leather|perfumery|beauty|cafe|restaurant|bar|interior-decoration|florist|pharmacy|jewelry|bank|hairdresser|convenience|clothes|optician|pastry|bakery|supermarket|alcohol'


# DATA #

FLPM_PRS = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/FLPM_PRS.csv'
FLPM_BDX = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/FLPM_BDX.csv'
FLPM_LIL = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/FLPM_LIL.csv'

BANCO_PRS = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/banco_prs.csv'
BANCO_BDX = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/banco_bdx.csv'
BANCO_LIL = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/banco_lil.csv'

METRO_PRS = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/metro_paris.csv'
FREQ_PRS = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/frequentation_metro_paris.csv'
FREQ_LIL = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/metro_lil.csv'
PARK = 'https://static.data.gouv.fr/resources/base-nationale-des-lieux-de-stationnement/20210502-172910/bnls-2-.csv'
INSEE = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/insee.csv'
BPE = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/main/Data/bpe.csv'

data_park = load_data(PARK, sep=';')
bpe = load_data(BPE)


# SIDEBAR #

st.sidebar.title('Sources')
st.sidebar.subheader('Base de Données')
st.sidebar.markdown(
    '''
    Données Nationales en OpenData :
    - Identification des propriétaires, personnes morales, de locaux commerciaux grâce au  
    [Fichiers des locaux et des parcelles des personnes morales]
    (https://www.data.gouv.fr/fr/datasets/fichiers-des-locaux-et-des-parcelles-des-personnes-morales/), disponible sous 
    _Data.gouv.fr_.
    
    - Identification des commerces via la
    [BAse Nationale des Commerces Ouverte]
    (https://www.data.gouv.fr/fr/datasets/base-nationale-des-commerces-ouverte/),
    mise à disposition par _OpenStreetMap_.
    
    - Localisation des stationnements : 
    [Base nationale des lieux de stationnement]
    (https://transport.data.gouv.fr/datasets/base-nationale-des-lieux-de-stationnement/#dataset-other-datasets)
    
    Données pour PARIS en OpenData :
    - Localisation des [Stations de Metro, RER et Tram]
    (https://www.data.gouv.fr/fr/datasets/stations-et-gares-de-metro-rer-et-tramway-de-la-region-ile-de-france/)
    via _OpenStreetMap_ 

    ''')

st.sidebar.subheader('API')
st.sidebar.markdown(
    '''
    - Conversion des adresses en coordonnées GPS en adresse et inversement grace à l'
    [API ADRESSE](https://geo.api.gouv.fr/adresse) mis à disposition par Etalab.
    
    - Conversion de coordonnées géographiques en code IRIS pour faire le lien avec l'INSEE grace 
    à [PYRIS](https://pyris.datajazz.io).

    - Recherche des gérants d'une société via l'API de [PAPPERS](https://www.pappers.fr/api/documentation) 
    qui centralise les données de l'INSEE et du BODACC. 
    ''')


# MAIN PAGE #

st.title('Bienvenue sur PopMyData')
st.subheader('Outil de prospection des locaux commerciaux')
st.title(' ')

# choose city
category = st.selectbox('Choisissez une ville : ',
                        [
                            {'city': 'Paris',
                             'flpm': FLPM_PRS,
                             'banco': BANCO_PRS},
                            {'city': 'Bordeaux',
                             'flpm': FLPM_BDX,
                             'banco': BANCO_BDX},
                            {'city': 'Lille',
                             'flpm': FLPM_LIL,
                             'banco': BANCO_LIL}
                        ],
                        format_func=lambda x: x['city'])

# load data of the city
flpm = load_data(category['flpm'])
banco = load_data(category['banco'])

# choose address
col1, col2 = st.beta_columns([1, 2])
with col1:
    numb = st.number_input('Numéro du local :', value=1, step=1,
                           help="Ne pas indiquer l'indice de répétition")
with col2:
    street = st.text_input('Indiquez le nom de la rue : ',
                           help='La recherche va chercher le nom de rue le plus proche dans la base de données.')

# choose option
col1, col2, col3, col4 = st.beta_columns([4, 3, 3, 3])
with col1:
    indice_attractivite = st.checkbox("Indice d'attractivité", value=True)
with col2:
    cartographie = st.checkbox("Cartographie", value=True)
with col3:
    coordonnees_proprio = st.checkbox("Coordonnées", value=True)
with col4:
    history = st.checkbox("Historique", value=False)

# search correspondance between street and flpm data
search_in_flpm = False
match = search_engine(street, flpm['Adresse'])

if len(match) > 1:
    st.title(' ')
    street = st.selectbox("Veuillez préciser l'adresse selectionnée", list(match.keys()),
                          help='''Si aucune adresse ne correspond à votre rechercher, 
                                  veuillez faire une nouvelle recherche.''')
elif len(match) == 1:
    street = list(match.keys())[0]
else:
    search_in_flpm = True

# filter data
search = flpm[(flpm['Adresse'] == street) &
              (flpm['N° voirie (Adresse du local)'] == str(numb))]

# if multiple owners, select one
if search.shape[0] > 1:
    st.title(' ')
    st.markdown('Il y a plusieurs propriétaires à cette adresse :')
    select = search[['Dénomination (Propriétaire(s) du local)',
                     'Forme juridique abrégée (Propriétaire(s) du local)',
                     'Indice de répétition (Adresse du local)',
                     'N° SIREN (Propriétaire(s) du local)']]
    select.drop_duplicates(['N° SIREN (Propriétaire(s) du local)'], inplace=True)
    st.dataframe(select)
    name = st.selectbox("Selectionnez le nom du propriétaire souhaité",
                        list(select['Dénomination (Propriétaire(s) du local)']))
    search = search[search['Dénomination (Propriétaire(s) du local)'] == name]

st.title(' ')
requete = st.button('Rechercher')

if requete and street == '':
    st.warning("Vous n'avez pas renseigné d'adresse")
elif requete:

    # geocoding (API)
    city = category['city']
    search_adr = '+'.join((str(numb) + ' ' + street + ' ' + city).split())
    adresse_geo = f"https://api-adresse.data.gouv.fr/search/?q={search_adr}"
    geo = requests.get(adresse_geo).json()
    coord_geo = geo['features'][0]['geometry']['coordinates']
    geo_point = (coord_geo[1], coord_geo[0])
    lat = coord_geo[1]
    lon = coord_geo[0]

    # code iris (API)
    rep_iris = requests.get(PYRIS_link, params={'lat': lat, 'lon': lon})
    code_iris = rep_iris.json()['complete_code']

    if indice_attractivite:
        st.markdown('___')
        with st.spinner("Calcul de l'indice d'attractivtié..."):
            # data locales
            metro_tram, metro, tram, bus, velo_lib = None, None, None, None, None
            if city == 'Paris':
                dep = 75

                # Metro/Tram (via csv pour gager en rapidité
                transport = load_data(METRO_PRS)
                freq_metro = load_data(FREQ_PRS)
                transport['Distance'] = transport['coord_geo'].apply(lambda x: distance(eval(x), geo_point).m)
                metro_prox = transport[transport['Distance'] < 400]
                metro_prox['Arrêt'] = metro_prox['Arrêt'].apply(clean_metro_paris)
                metro_tram = pd.merge(metro_prox, freq_metro, left_on='Arrêt', right_on='nom', how='left')

                # Bus
                r = requests.get('https://data.ratp.fr/api/records/1.0/search/',
                                 params={'dataset': 'accessibilite-des-arrets-de-bus-ratp',
                                         'geofilter.distance': f'{lat}, {lon}, 400'})
                reponse = pd.json_normalize(r.json(), record_path='records')
                if len(reponse) > 0:
                    reponse.drop_duplicates(['fields.nomptar'], inplace=True, keep='first')
                    bus = reponse[['fields.nomptar', 'fields.dist']].rename(columns={'fields.name': 'Nom de la station',
                                                                                     'fields.dist': 'Distance'})

                # velo libre service
                r = requests.get('https://opendata.paris.fr/api/records/1.0/search/',
                                 params={'dataset': 'velib-disponibilite-en-temps-reel',
                                         'geofilter.distance': f'{lat}, {lon}, 400'})
                reponse = pd.json_normalize(r.json(), record_path='records')
                if len(reponse) > 0:
                    reponse['Distance'] = reponse['fields.coordonnees_geo'].apply(lambda x: distance(x, geo_point).m)
                    velo_lib = reponse[['fields.name', 'Distance']].rename(columns={'fields.name': 'Nom de la station'})

            elif city == 'Bordeaux':
                dep = 33
                API = 'https://data.bordeaux-metropole.fr/geojson?key=1566LLMUWW'
                geom = '&filter={"geom":{"$geoWithin":{"$center":' + f"{[lon, lat]}" + ',"$radius":400}}}'

                # Bus/Tram
                r = requests.get(API + '&typename=sv_arret_p' + geom)
                reponse = pd.json_normalize(r.json(), record_path='features')
                if len(reponse) > 0:
                    reponse.drop_duplicates(['properties.libelle', 'properties.vehicule'], inplace=True, keep='last')
                    reponse['Distance'] = reponse['geometry.coordinates'].apply(lambda x: distance((x[1], x[0]),
                                                                                                   geo_point).m)
                    transport = reponse[['properties.libelle', 'properties.vehicule', 'Distance']]
                    transport.rename(columns={'properties.libelle': 'Nom de la station',
                                              'properties.vehicule': 'Type'}, inplace=True)
                    bus = transport[transport['Type'] == 'BUS']
                    metro_tram = transport[transport['Type'] == 'TRAM']

                # velo libre service
                r = requests.get(API + '&typename=ci_vcub_p' + geom)
                reponse = pd.json_normalize(r.json(), record_path='features')
                if len(reponse) > 0:
                    reponse.drop_duplicates(['properties.nom'], inplace=True, keep='last')
                    reponse['Distance'] = reponse['geometry.coordinates'].apply(lambda x: distance((x[1], x[0]),
                                                                                                   geo_point).m)
                    velo_lib = reponse[['properties.nom', 'Distance']]
                    velo_lib.rename(columns={'properties.nom': 'Nom de la station'}, inplace=True)

            elif city == 'Lille':
                dep = 59

                # Metro
                r = requests.get('https://opendata.lillemetropole.fr/api/records/1.0/search/',
                                 params={'dataset': 'stations-metro',
                                         'geofilter.distance': f'{lat}, {lon}, 400'})
                reponse = pd.json_normalize(r.json(), record_path='records')
                if len(reponse) > 0:
                    metro = reponse[['fields.nom_statio', 'fields.dist', 'fields.ligne']]
                    metro.rename(columns={'fields.nom_statio': 'Nom de la station',
                                          'fields.dist': 'Distance', 'fields.ligne': 'Ligne'}, inplace=True)

                # Bus/Tram
                r = requests.get('https://opendata.lillemetropole.fr/api/records/1.0/search/',
                                 params={'dataset': 'ilevia-physicalstop',
                                         'geofilter.distance': f'{lat}, {lon}, 400'})
                reponse = pd.json_normalize(r.json(), record_path='records')
                if len(reponse) > 0:
                    reponse.drop_duplicates(['fields.commercialstopname', 'fields.publiclinecode'],
                                            inplace=True,
                                            keep='last')
                    transport = reponse[['fields.transportmoderef', 'fields.commercialstopname',
                                         'fields.publiclinecode', 'fields.dist']]
                    transport.rename(columns={'fields.commercialstopname': 'Nom de la station',
                                              'fields.dist': 'Distance',
                                              'fields.transportmoderef': 'Type',
                                              'fields.publiclinecode': 'Ligne'}, inplace=True)
                    bus = transport[transport['Type'] == 'B']
                    tram = transport[transport['Type'] == 'T']

                # frequentation
                if metro is not None and tram is not None:
                    metro_tram = pd.concat([metro, tram])
                elif metro is not None:
                    metro_tram = metro
                else:
                    metro_tram = tram
                freq_metro = load_data(FREQ_LIL)
                metro_tram = pd.merge(metro_tram, freq_metro, left_on='Nom de la station', right_on='nom', how='left')

                # velo libre service
                r = requests.get('https://opendata.lillemetropole.fr/api/records/1.0/search/',
                                 params={'dataset': 'vlille-realtime',
                                         'geofilter.distance': f'{lat}, {lon}, 400'})
                reponse = pd.json_normalize(r.json(), record_path='records')
                if len(reponse) > 0:
                    reponse['Distance'] = reponse['fields.geo'].apply(lambda x: distance(x, geo_point).m)
                    velo_lib = reponse[['fields.nom', 'fields.adresse', 'Distance']]
                    velo_lib.rename(columns={'fields.nom': 'Nom de la station', 'fields.adresse': 'Adresse'},
                                    inplace=True)
            # data BANCO
            index = 0
            banco['distance'] = 0
            # ATTENTION : revoir le filtre par types
            for geo_shop in zip(banco.iloc[:, 1], banco.iloc[:, 0]):
                banco['distance'][index] = distance(geo_shop, geo_point).m
                index += 1
            local_banco = banco[banco['distance'] < 200]

            # data nationale : parking
            index = 0
            parking = city_park(dep, data_park)
            parking['Distance'] = 0
            for geo_park in zip(parking.iloc[:, 1], parking.iloc[:, 0]):
                parking['Distance'].iloc[index] = distance(geo_park, geo_point).m
                index += 1
            nb_parking = len(parking[parking['Distance'] < 400])

            # data nationale : BPE
            bpe = bpe[bpe['DEP'] == dep]
            bpe['Distance'] = bpe['coord_geo'].apply(lambda x: distance(eval(x), geo_point).m)
            zone_bpe = bpe[bpe['Distance'] < 400].sort_values('Distance').value_counts('Equipement')

            # data nationale : INSEE
            insee = load_data(INSEE).set_index('IRIS').loc[int(code_iris)]

            # empty indices
            indice_access = pd.DataFrame(np.zeros((5, 2), int),
                                         index=['Gare', 'Metro/Tram', 'Bus', 'Velo_ls', 'Parking'],
                                         columns=['Total', 'Note'])
            indice_quartier = pd.DataFrame(np.zeros((9, 2), int),
                                           index=['Bureau de poste', 'École maternelle', 'Enseignement Secondaire',
                                                  'Enseignement supérieur', 'Zone Sports', 'Cinéma', 'Espace Culturel',
                                                  'Bibliothèque', 'Hôtel'],
                                           columns=['Total', 'Note'])
            indice_pop = pd.DataFrame(np.zeros((2, 2), dtype=int),
                                      index=['Population Active', 'Revenu médian'],
                                      columns=['Total', 'Note'])
            indice_visibilite = pd.DataFrame(np.zeros((5, 2), int),
                                             index=['Tissu commercial', 'Proportion Restaurants/Bars',
                                                    'Centres Commerciaux', 'Proportion Grandes Enseignes',
                                                    "Proportion d'Indépendants"],
                                             columns=['Total', 'Note'])

            if dep == 75:
                indice_visibilite.loc['Affluance des transports'] = [int(metro_tram.loc[:, 'validations'].sum()), 0]
            elif dep == 59:
                indice_visibilite.loc['Affluance des transports'] = [int(metro_tram.loc[:, 'validations'].sum()), 0]

            for el, val in zip(zone_bpe.index, zone_bpe):
                if el in indice_quartier.index:
                    indice_quartier.loc[el, 'Total'] = val
                elif el in indice_access.index:
                    indice_access.loc[el, 'Total'] = val
            if metro_tram is not None:
                indice_access.loc['Metro/Tram', 'Total'] = len(metro_tram)
            if bus is not None:
                indice_access.loc['Bus', 'Total'] = len(bus)
            if velo_lib is not None:
                indice_access.loc['Velo_ls', 'Total'] = len(velo_lib)
            indice_access.loc['Parking', 'Total'] = nb_parking
            indice_pop.loc['Population Active', 'Total'] = insee['Population Active']
            indice_pop.loc['Revenu médian', 'Total'] = insee['Revenus Medians']
            indice_visibilite.loc['Tissu commercial', 'Total'] = len(local_banco)
            indice_visibilite.loc['Centres Commerciaux'] = [len(local_banco[local_banco['type'] == 'supermarket']), 0]
            if len(local_banco) > 0:
                temp_tab_bar = len(local_banco[local_banco['type'].isin(['bar', 'restaurant'])]) / len(local_banco)
                indice_visibilite.loc['Proportion Restaurants/Bars'] = [round(temp_tab_bar*100, 2), 0]
                temp_tab_com = local_banco['cat_mag'].value_counts(normalize=True)
                if len(temp_tab_com) == 2:
                    indice_visibilite.loc['Proportion Grandes Enseignes'] = [(temp_tab_com.loc[1]*100).round(2), 0]
                    indice_visibilite.loc["Proportion d'Indépendants"] = [(temp_tab_com.loc[0]*100).round(2), 0]
                else:
                    if temp_tab_com.index == 0:
                        indice_visibilite.loc["Proportion d'Indépendants"] = [(temp_tab_com.loc[0]*100).round(2), 0]
                    else:
                        indice_visibilite.loc["Proportion Grandes Enseignes"] = [(temp_tab_com.loc[1]*100).round(2), 0]

            # calculate rates
            final_viz = visibility_rating(indice_visibilite, dep)
            final_access = access_rating(indice_access)
            final_pop = population_rating(indice_pop)
            final_dist = district_rating(indice_quartier)

            # calculate final rate
            for indice_table in [final_viz, final_access, final_pop, final_dist]:
                if sum(indice_table.iloc[:, 1]) >= 0:
                    indice_table.loc['Total'] = [' ', sum(indice_table.iloc[:, 1])]
                else:
                    indice_table.loc['Total'] = [' ', 0]
            final_note = 0
            for total_final in [final_viz, final_access, final_pop, final_dist]:
                final_note += total_final.iloc[-1, 1]

            # print indices
            col1, col2 = st.beta_columns([2, 1])
            with col1:
                st.title(' ')
                st.subheader("Indice d'attractivité de l'emplacement")
                st.write(geo['features'][0]['properties']['label'])
            with col2:
                color = 'green' if final_note > 70 else 'tomato'
                st.markdown(
                    f'''
                    <p class="indice_total", style="color:{color}">{final_note}
                        <span class="text">/ 100</span> </p>
                    ''', unsafe_allow_html=True)
            st.title(' ')
            col1, col2, col3, col4 = st.beta_columns(4)
            with col1:
                color = 'green' if final_viz.iloc[-1, 1] > 15 else 'tomato'
                st.markdown(
                    f'''
                    <p class="titre">Indice de visibilité</p>
                    <p class="sous_indice", style="color:{color}">{int(final_viz.iloc[-1, 1])} 
                        <span class="text">/ 30</span> </p>
                    ''', unsafe_allow_html=True)
            with col2:
                color = 'green' if final_access.iloc[-1, 1] > 15 else 'tomato'
                st.markdown(
                    f'''
                    <p class="titre">Indice d'accessiblité</p>
                    <p class="sous_indice", style="color:{color}">{int(final_access.iloc[-1, 1])}
                        <span class="text">/ 30</span></p>
                    ''', unsafe_allow_html=True)
            with col3:
                color = 'green' if final_pop.iloc[-1, 1] > 10 else 'tomato'
                st.markdown(
                    f'''
                    <p class="titre">Indice de Population</p>
                    <p class="sous_indice", style="color:{color}">{int(final_pop.iloc[-1, 1])}
                        <span class="text">/ 20</span></p>
                    ''', unsafe_allow_html=True)
            with col4:
                color = 'green' if final_dist.iloc[-1, 1] > 10 else 'tomato'
                st.markdown(
                    f'''
                    <p class="titre">Indice du Quartier</p>
                    <p class="sous_indice", style="color:{color}">{int(final_dist.iloc[-1, 1])}
                        <span class="text">/ 20</span></p>
                    ''', unsafe_allow_html=True)

            # expander
            st.title(' ')
            option = st.beta_expander("Afficher le détail des indices")
            option.write(' ')
            col1, col2, col3 = option.beta_columns(3)
            with col1:
                st.markdown(f'Longitude : {lon}')
            with col2:
                st.markdown(f'Latitude : {lat}')
            with col3:
                st.markdown(f'Code Iris : {code_iris}')
            col1, col2 = option.beta_columns([3, 2])
            with col1:
                st.markdown("**Indice de Visiblité**")
                st.dataframe(final_viz)
            with col2:
                st.markdown("**Indice d'Accessiblité**")
                st.dataframe(final_access)
            col1, col2 = option.beta_columns([8, 9])
            with col1:
                st.markdown("**Indice de Population**")
                st.dataframe(final_pop)
            with col2:
                st.markdown("**Indice du Quartier**")
                st.dataframe(final_dist)

            # add to history
            histo_adresse = f'{numb} {street}'
            if histo_adresse not in st.session_state:
                st.session_state[histo_adresse] = [final_note,
                                                   int(final_viz.iloc[-1, 1]), int(final_access.iloc[-1, 1]),
                                                   int(final_pop.iloc[-1, 1]), int(final_dist.iloc[-1, 1])]

    if cartographie:
        st.markdown('___')
        st.subheader('Situation du quartier')
        st.subheader(' ')

        with st.spinner('Construction de la carte...'):
            folium_static(carte(banco, (lat, lon)), height=650)

    if coordonnees_proprio:
        st.markdown('___')
        st.subheader('Coordonnées du Propriétaire')
        st.subheader(' ')

        with st.spinner('Recherche des coordonnées du propriétaire...'):
            # if no owner found
            any_soc = False
            if search.shape[0] == 0 or search_in_flpm:
                st.info(
                    """
                    Il n'y a pas de propriétaire identifié pour le de local commercial situé à cette adresse, 
                    ou l'adresse indiquée n'existe pas dans la base de donnée.
                    """)
            # if siren is false
            elif (search.iloc[0, 10].startswith('U')) or (search.iloc[0, 10] == np.nan):
                name = search['Dénomination (Propriétaire(s) du local)']
                clean_name = clean_soc_name(name.iloc[0])
                info = requests.get(pappers_reaserch, params={'api_token': pappers_key, 'q': clean_name})
                societe = info.json()
                if societe['total'] == 0:
                    st.error(
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

                        st.warning(
                            f"""
                            **SIEGE** : \n
                            {nom_soc}\n
                            {ad1_soc.lower()} \n
                            {ad2_soc.lower()} \n
                            {ad3_soc}
                            """)
                    with col2:
                        if len(status['representants']) == 1:
                            st.info(print_associates(0, status))

                    st.title(' ')
                    index = 0
                    if len(status['representants']) > 1:
                        for ligne in range((len(status['representants'])//2)):
                            cols = st.beta_columns(2)
                            for i, col in enumerate(cols):
                                col.info(print_associates(index, status))
                                index += 1
                        if len(status['representants']) % 2 == 1:
                            col1, col2 = st.beta_columns(2)
                            with col1:
                                st.info(print_associates(index, status))

                except KeyError:
                    st.error(
                        f"""
                        Une erreure s'est produite lors de la récupération des données.
                        Nous vous invitons à effectuer manuellement la recherche de la société
                        **{search['Dénomination (Propriétaire(s) du local)'].iloc[0]}**, 
                        numéro de **SIREN {siren}**.
                        """)

    if history:
        st.markdown('___')
        st.subheader("Historique des recherches")
        st.subheader(' ')

        histo = pd.DataFrame(columns=['Total', 'Visibilité', 'Accessibilité', 'Population', 'Quartier'])
        for address, rate_list in st.session_state.items():
            histo.loc[address] = rate_list
        st.table(histo)
