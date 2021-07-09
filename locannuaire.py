import requests
import folium
from folium import plugins
import numpy as np
import pandas as pd
import streamlit as st
from streamlit_folium import folium_static
from geopy.distance import distance

st.set_page_config(page_title="Locannuaire",
                   page_icon="⌂",
                   initial_sidebar_state="collapsed",
                   )


# FONCTIONS #

def load_data(url, sep=','):
    return pd.read_csv(url, sep=sep)


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


# DATA #

FLPM_PRS = 'https://github.com/MickaelKohler/PopMyData/raw/main/Data/FLPM_PRS.csv'
FLPM_BDX = 'https://github.com/MickaelKohler/PopMyData/raw/main/Data/FLPM_BDX.csv'
FLPM_LIL = 'https://github.com/MickaelKohler/PopMyData/raw/main/Data/FLPM_LIL.csv'

BANCO_PRS = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/version-alpha/Data/banco_prs.csv'
BANCO_BDX = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/version-alpha/Data/banco_bdx.csv'
BANCO_LIL = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/version-alpha/Data/banco_lil.csv'

METRO_PRS = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/version-alpha/Data/metro_paris.csv'
PARK = 'https://static.data.gouv.fr/resources/base-nationale-des-lieux-de-stationnement/20210502-172910/bnls-2-.csv'
INSEE = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/version-alpha/Data/insee.csv'
BPE = 'https://raw.githubusercontent.com/MickaelKohler/PopMyData/version-alpha/Data/bpe.csv'

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

st.title('Bienvenu sur PopMyData')
st.subheader('Outil de prospection des locaux commerciaux')
st.title(' ')

# choose city
category = st.selectbox('Choisissez une ville',
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
                        format_func=lambda option: option['city'])

# load data of the city
flpm = load_data(category['flpm'])
banco = load_data(category['banco'])
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
    st.subheader("Caractérisation de l'emplacement")
    city = category['city']  # add with street and numb

    # geocoding (API)
    search_adr = '+'.join((str(numb) + ' ' + street + ' ' + city).split())
    adresse_geo = f"https://api-adresse.data.gouv.fr/search/?q={search_adr}"
    rep_geo = requests.get(adresse_geo)
    geo = rep_geo.json()
    coord_geo = geo['features'][0]['geometry']['coordinates']
    geo_point = (coord_geo[1], coord_geo[0])
    lat = coord_geo[1]
    lon = coord_geo[0]

    # code iris (API)
    rep_iris = requests.get(PYRIS_link, params={'lat': lat, 'lon': lon})
    code_iris = rep_iris.json()['complete_code']

    # data locales
    metro_tram = None
    tram = None
    bus = None
    velo_lib = None
    if city == 'Paris':
        dep = 75

        # Metro/Tram (via csv pour gager en rapidité
        transport = load_data(METRO_PRS)
        transport['Distance'] = transport['coord_geo'].apply(lambda x: distance(eval(x), geo_point).m)
        metro_tram = transport[transport['Distance'] < 400]

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

        # Bus/Tram
        trans_link = 'https://data.bordeaux-metropole.fr/geojson?key=1566LLMUWW&typename=sv_arret_p&filter={"geom":{"$geoWithin":{"$center":' + f"{[lon, lat]}" + ',"$radius":400}}}'
        r = requests.get(trans_link)
        reponse = pd.json_normalize(r.json(), record_path='features')
        if len(reponse) > 0:
            reponse.drop_duplicates(['properties.libelle', 'properties.vehicule'], inplace=True, keep='last')
            reponse['Distance'] = reponse['geometry.coordinates'].apply(lambda x: distance((x[1], x[0]), geo_point).m)
            transport = reponse[['properties.libelle', 'properties.vehicule', 'Distance']].rename(columns={'properties.libelle': 'Nom de la station',
                                                                                                           'properties.vehicule' : 'Type'})
            bus = transport[transport['Type'] == 'BUS']
            metro_tram = transport[transport['Type'] == 'TRAM']

        # velo libre service
        velo_link = 'https://data.bordeaux-metropole.fr/geojson?key=1566LLMUWW&typename=ci_vcub_p&filter={"geom":{"$geoWithin":{"$center":' + f"{[lon, lat]}" + ',"$radius":400}}}'
        r = requests.get(velo_link)
        reponse = pd.json_normalize(r.json(), record_path='features')
        if len(reponse) > 0:
            reponse.drop_duplicates(['properties.nom'], inplace=True, keep='last')
            reponse['Distance'] = reponse['geometry.coordinates'].apply(lambda x: distance((x[1], x[0]), geo_point).m)
            velo_lib = reponse[['properties.nom', 'Distance']].rename(columns={'properties.nom': 'Nom de la station'})

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
            reponse.drop_duplicates(['fields.commercialstopname', 'fields.publiclinecode'], inplace=True, keep='last')
            transport = reponse[['fields.transportmoderef', 'fields.commercialstopname',
                                 'fields.publiclinecode', 'fields.dist']]
            transport.rename(columns={'fields.commercialstopname': 'Nom de la station',
                                      'fields.dist': 'Distance',
                                      'fields.transportmoderef': 'Type',
                                      'fields.publiclinecode': 'Ligne'}, inplace=True)
            bus = transport[transport['Type'] == 'B']
            tram = transport[transport['Type'] == 'T']
        metro_tram = pd.concat([metro, tram])

        # velo libre service
        r = requests.get('https://opendata.lillemetropole.fr/api/records/1.0/search/',
                         params={'dataset': 'vlille-realtime',
                                 'geofilter.distance': f'{lat}, {lon}, 400'})
        reponse = pd.json_normalize(r.json(), record_path='records')
        reponse['Distance'] = reponse['fields.geo'].apply(lambda x: distance(x, geo_point).m)
        velo_lib = reponse[['fields.nom', 'fields.adresse', 'Distance']].rename(columns={'fields.nom': 'Nom de la station',
                                                                                         'fields.adresse': 'Adresse'})
    # data BANCO
    index = 0
    banco['distance'] = 0
    for geo_shop in zip(banco.iloc[:, 1], banco.iloc[:, 0]):
        banco['distance'][index] = distance(geo_shop, geo_point).m
        index += 1

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

    # indice attractivite
    indice_access = pd.DataFrame(np.zeros(5, int),
                                 index=['Gare', 'Metro/Tram', 'Bus', 'Velo_ls', 'Parking'],
                                 columns=['Total'])
    indice_quartier = pd.DataFrame(np.zeros(9, int),
                                   index=['Bureau de poste', 'École maternelle', 'Enseignement Secondaire',
                                          'Enseignement supérieur', 'Zone Sports', 'Cinéma', 'Espace Culturel',
                                          'Bibliothèque', 'Hôtel'],
                                   columns=['Total'])
    indice_pop = pd.DataFrame(np.zeros(2, int),
                              index=['Population Active', 'Revenus médiant'],
                              columns=['Total'])
    indice_visibilite = pd.DataFrame(np.zeros(1, int),
                                     index=['Tissu commercial'],
                                     columns=['Total'])

    for el, val in zip(zone_bpe.index, zone_bpe):
        if el in indice_quartier.index:
            indice_quartier.loc[el] = val
        elif el in indice_access.index:
            indice_access.loc[el] = val
    if metro_tram is not None:
        indice_access.loc['Metro/Tram'] = len(metro_tram)
    if bus is not None:
        indice_access.loc['Bus'] = len(bus)
    if velo_lib is not None:
        indice_access.loc['Velo_ls'] = len(velo_lib)
    indice_access.loc['Parking'] = nb_parking
    indice_pop.loc['Population Active'] = insee['Population Active']
    indice_pop.loc['Revenus médiant'] = insee['Revenus Medians']
    indice_visibilite.loc['Tissu commercial'] = len(banco[banco['distance'] < 200])

    # print
    col1, col2, col3 = st.beta_columns(3)
    with col1:
        st.markdown(f'**Longitude** : {lon}')
    with col2:
        st.markdown(f'**Latitude** : {lat}')
    with col3:
        st.markdown(f'**Code Iris** : {code_iris}')
    st.title(' ')

    col1, col2 = st.beta_columns(2)
    with col1:
        st.markdown("Indice d'accessiblité")
        st.dataframe(indice_access)
    with col2:
        st.markdown("Indice de vie du quartier")
        st.dataframe(indice_quartier)

    col1, col2 = st.beta_columns(2)
    with col1:
        st.markdown("Indice Population")
        st.dataframe(indice_pop)
    with col2:
        st.markdown("Indice de visiblité")
        st.dataframe(indice_visibilite)

    st.markdown('___')
    st.subheader('Situation du quartier')

    type_name = ['shoes', 'garden_center', 'department_store', 'cosmetics', 'leather', 'perfumery', 'beauty',
                 'cafe', 'restaurant', 'bar', 'interior-decoration', 'florist', 'pharmacy', 'jewelry', 'bank',
                 'hairdresser', 'convenience', 'clothes', 'optician', 'pastry', 'bakery', 'supermarket']
    df_temp = banco[banco['type'].isin(type_name)]

    map = folium.Map([lat, lon], zoom_start=16)

    popups = [item for index, item in df_temp['name'].iteritems()]
    heat_map = plugins.HeatMap(df_temp[["Y", "X"]], name='_heatmap')
    map.add_child(heat_map)

    marker_cluster = plugins.MarkerCluster(df_temp[["Y", "X"]], popups=popups).add_to(map)
    map.add_child(marker_cluster)

    folium_static(map)

    st.markdown('___')
    st.subheader('Coordonnées du Propriétaires')

    # if no owner found
    any_soc = False
    if search.shape[0] == 0:
        st.markdown(
            """
            Il n'y a pas de propriétaire identifié pour le de local commercial situé à cette adresse, 
            ou l'adresse indiquée n'existe pas
            """)
    # if siren is false
    elif any(search['N° SIREN (Propriétaire(s) du local)'].str.contains('U')) \
            or any(search['N° SIREN (Propriétaire(s) du local)'] == np.nan):
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
