# Pop My Data
_Outil de prospection de locaux comemrciaux_

## Sommaire

* [Origine du projet](#origine-du-projet)
* [Screenshots](#interface)
* [Technologies](#technologies)
* [Bases de Données](#bases-de-données)
* [Statut](#statut)
* [La Team](#la-team)

## Origine du projet

Les projet _Pop My Data_ est né d'une volonté de __My Pop Up Store__ de pouvoir avoir un outil pratique et rapide pour prospecter de nouveaux locaux commerciaux où installer des boutiques éphemères. 

Deux thématiques sont étudiées par l'outils :
- Caractériser l'attractivité d'un emplacement
- Fournir les coordonnées du propriétaire (personne morale) d'un local.

Trois villes sont été intégrée dans l'outils dans la version 1.0 : **Paris**, **Bordeaux** et **Lille**

Toutes les données utilisées prennent leurs sources dans l'Open Data. La liste des  bases de données consultées est [disponibles dans le wiki](https://github.com/MyPopUpStore/PopMyData/wiki/Annexe-:-Les-Bases-de-Données)

## Interface

Ces analyses ont été mises à disposition au travers d’une __WebApp__ créée au travers de la plateforme __Streamlit__.

### Adresse du site :

Le site est hébergé sur les serveurs mis à disposition par *Streamlit* :

https://share.streamlit.io/mypopupstore/popmydata/main/locannuaire.py

### Captures d’écran

![screenshot1](https://raw.githubusercontent.com/MyPopUpStore/PopMyData/main/Ressources%20Wiki/capture1.png)
![screenshot2](https://raw.githubusercontent.com/MyPopUpStore/PopMyData/main/Ressources%20Wiki/Capture2.png)
![screenshot3](https://raw.githubusercontent.com/MyPopUpStore/PopMyData/main/Ressources%20Wiki/Capture3.png)

## Technologies 

Projet fait entièrement en **Python**

Utilisations des librairies suivantes : 
 - *Pandas* pour l'exploration de la donnée
 - *KNIME* pour le nettoyage automatique de la donnée
 - *Folium* pour la cartograhie
 - *Streamlit* pour l'interface de la WebApp

## Bases de données 

Toutes les données utilisées sont disponible en Open Data et sont consultées au travers d'API ou de fichiers nettoyées et enregistré dans le **dossier Data**.

La liste des  bases de données consultées est [disponibles dans le wiki](https://github.com/MyPopUpStore/PopMyData/wiki/Annexe-:-Les-Bases-de-Données)

*La dernière mise à jours des données date du 26/07/2021.*

## Statut

La version 1.0 de la WebApp *locannuaire* est disponible depuis le 27/07/2021.

## La Team

Le projet a été réalisé par les élèves de la **Wild Code School** :
- Fanyim Dingue
- Franck Maillet
- Michael Kohler
- Mickael Caceres
- Violaine Harribey
