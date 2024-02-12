import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import json


from streamlit_option_menu import option_menu
from langchain.llms import HuggingFaceHub
from langchain.sql_database import SQLDatabase

import warnings
warnings.filterwarnings('ignore')

from llm_query import SQLquery2, chat_response_generation

# Création d'une barre latérale "Main Menu" pour naviguer entre les différentes pages de l'application :
with st.sidebar:
    mainmenu = option_menu("📍 Main Menu", 
                           ['🏠 Information','📊 Tableau de Bord', '🤖 Les offres','🤖 Q/Abot', 'Règles d\'utilisation IA'], # différentes pages de l'application
                           default_index=0) # par défaut, la première page s'affiche

# Clé à entrer dans le menu latéral pour se connecter à l'API de HuggingFace :    
hf_api_key = st.sidebar.text_input('Clé API HuggingFace', type='password') 


conn = sqlite3.connect('joboffers_dw.db') # connexion à une base de données SQL créée préalablement

# Si la page "🏠 Information" est cliquée :  
if mainmenu == '🏠 Information':
    st.title(":red[Offres d'Emploi en Data Science]")
    st.divider()
    st.header('Bienvenue sur cette super application !')
    st.subheader('_Ici, venez plonger dans un monde de données où les offres d\'emploi en data science pleuvent._')
    container = st.container(border=True)
    container.write(""":red[**Information :**] Cette application a été créée dans le cadre d'un projet de groupe à _l'Université
                    Lumière Lyon 2_, pour le cours de :red[_text mining_] supervisé par **Ricco RAKOTOMALALA**. L'application a été 
                    créée par **Naomi KALDJOB**, **Annabelle NARSAMA**, et **Clovis VARANGOT-REILLE**, étudiants dans le Master 2
                    Statistiques et Informatique pour la Science des donnÉes (SISE). Cette application permet ainsi d'afficher 
                    différentes informations liées aux offres d'emploi en :red[data]. Elle inclue des graphiques représentant les offres, les différentes offres avec un chatbot pour communiquer avec ainsi
                    qu'un Q/Abot pour poser des questions à notre base d'information.
                    """)
    st.divider()
    st.image('logo_dalle.png', caption='Dall-E 2: Create a single logo featuring the stylized red abstract brain intertwined with binary code, based on the left image of the previous set. The logo should be isolated on a plain white background. This logo retains the detailed brain with visible lobes and neural connections, with binary code dynamically interwoven. The singular focus on one logo against a white background will highlight its modern, sleek design, making it well-suited for a data science job offer application.')
    st.divider()
    st.caption('_Made by Naomi Kaljob (https://github.com/naomi-kaldjob), Annabelle Narsama (https://github.com/annarsama), & Clovis Varangot-Reille (https://github.com/cvarrei)_')

# Si la page "📊 Tableau de Bord" est cliquée :
elif mainmenu == '📊 Tableau de Bord':
    st.title('📊 :red[Tableau de Bord]')
    st.divider()
    st.header('Bienvenue sur le tableau de bord !')
    st.subheader('_Voici quelques chiffres et graphiques en lien avec les offres d\'emploi en data science._')
    # Création d'onglets dans la page (l'ordre des noms d'onglets est important) :
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Offres", "Salaire", "Contrats", 
                                                        "Expérience", "Cartographie", "Wordcloud"])

    # Onglet 1 - Offres :
    with tab1: 
        # Requête sur le nombre de profils groupé par poste (ici "titre")
        requete = """SELECT COUNT(profil) as Nombre, titre as Offres FROM f_offres 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
        GROUP BY Offres 
        ORDER BY Nombre DESC;"""
        position = pd.read_sql_query(requete, conn) # transformation de la requête en df

        jobs = ["Data analyst", "Data scientist", "Data engineer", "Data manager", "Data steward", "Ml engineer"]

        job = st.selectbox("**_Quel poste souhaitez-vous afficher pour l'onglet 'Offres' ?_**", jobs)
        st.subheader(f'**_Global_**')
        st.write("""**_Ici, vous pouvez retrouver le nombre total d'offres, ainsi que le nombre d'offres par 
                 pays selon le poste sélectionné._**""")
        container = st.container(border=True)
        col1, col2 = container.columns([2, 3]) # création de 2 colonnes de tailles différentes

        # Colonne 1 :
        with col1:
            st.write(":red[**_Nombre total d'offres_**]")
            # Requête sur le nombre d'offres :
            query = """SELECT COUNT(titre) as Offres FROM f_offres 
               INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
               ORDER BY Offres DESC;"""
            world = pd.read_sql_query(query, conn) # transformation de la requête en df
            st.dataframe(world, hide_index=True, use_container_width=True) # affichage du df

        # Colonne 2 :   
        with col2:
            st.write(f":red[**_Nombre d’offres de {job.lower()} par pays_**]")
            # Requête sur le nombre d'offres par pays selon le poste sélectionné par l'utilisateur :
            query = f"""SELECT COUNT(titre) as Offres, pays as Pays FROM f_offres 
            INNER JOIN d_geo ON f_offres.id_geo = d_geo.id_geo 
            INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
            WHERE titre LIKE "%{job}%" 
            GROUP BY pays 
            ORDER BY Offres DESC;"""
            europe = pd.read_sql_query(query, conn)
            st.dataframe(europe, hide_index=True, use_container_width=True)
        st.divider()

        st.subheader(f'**_Postes de {job.lower()} par région_**')
        st.write('**_Ici, vous pouvez retrouver le nombre d\'offres par région selon le poste sélectionné._**')
        container = st.container(border=True)
        container.write(f':red[**_Nombre d\'offres de {job.lower()} par région_**]')
        # Requête sur le nombre d'offres par région selon le poste sélectionné par l'user :
        query = f"""SELECT COUNT(titre) as Offers, nom_region as Region FROM f_offres 
        INNER JOIN d_geo ON f_offres.id_geo = d_geo.id_geo 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
        WHERE titre LIKE "%{job}%"
        GROUP BY nom_region 
        ORDER BY Offers DESC;"""
        region = pd.read_sql_query(query, conn)
        custom_colors = ['#900C3F']
        # Barplot de la requête :
        fig=px.bar(region, 
                   x='Offers', y='Region', 
                   orientation='h', 
                   color_discrete_sequence=custom_colors, 
                   width=600, height=600)
        container.write(fig) # affichage du barplot dans l'application
        st.divider()

        st.subheader(f'**_Postes de {job.lower()} par département_**')
        st.write('**_Ici, vous pouvez retrouver le nombre d\'offres par département selon le poste sélectionné._**')
        container = st.container(border=True)
        container.write(f':red[**_Nombre d\'offres de {job.lower()} par département_**]')
        # Requête sur le nombre d'offres par département selon le poste sélectionné par l'utilisateur :
        query = f"""SELECT COUNT(titre) as Offers, nom_departement as Department FROM f_offres 
        INNER JOIN d_geo ON f_offres.id_geo = d_geo.id_geo 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
        WHERE titre LIKE "%{job}%"
        GROUP BY nom_departement 
        ORDER BY Offers DESC;"""
        departement = pd.read_sql_query(query, conn)
        dep_names = departement['Department']
        custom_colors = ['#FFA07A']
        fig=px.bar(departement, 
                   x='Offers', y='Department', 
                   orientation='h', 
                   color_discrete_sequence=custom_colors, 
                   width=600, height=600)
        container.write(fig)
    
    # Onglet 2 - Salaire :
    with tab2:
        requete = """SELECT COUNT(profil) as Nombre, titre as Offres FROM f_offres 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
        GROUP BY Offres 
        ORDER BY Nombre DESC;"""
        position = pd.read_sql_query(requete, conn)
        jobs = ["Data analyst", "Data scientist", "Data engineer", "Data manager"]

        job = st.selectbox("**_Quel poste souhaitez-vous afficher pour l'onglet 'Salaire' ?_**", jobs)
        st.caption("""_Certaines offres n'affichent aucun salaire, il est donc possible que 
                   certaines valeurs soient manquantes et soient marquées comme telle._ Nous avons gardé les métiers où nous avions suffisament d'information sur le salaire.""")
        st.subheader('**_Global_**')
        st.write('**_Ici, vous pouvez retrouver les salaires moyens, global, et par pays selon le poste sélectionné._**')
        container = st.container(border=True)
        col1, col2 = container.columns([2,3])
        with col1:
            st.write(':red[**_Salaire moyen global_**]')
            # Requête sur le salaire moyen global :
            query = """SELECT AVG(salaire_moyen) as Salaire FROM f_offres 
            INNER JOIN d_salaire ON f_offres.id_salaire = d_salaire.id_salaire;"""
            salaire = pd.read_sql_query(query, conn)
            st.dataframe(salaire, hide_index=True, use_container_width=True)

        with col2:
            st.write(f':red[**_Salaire moyen pour le poste de {job.lower()} par pays (si disponible)_**]')
            # Requête sur le salaire moyen par pays selon le poste sélectionné par l'utilisateur :
            query = f"""SELECT AVG(salaire_moyen) as Salaire, pays as Pays FROM f_offres 
            INNER JOIN d_geo ON f_offres.id_geo = d_geo.id_geo 
            INNER JOIN d_salaire ON f_offres.id_salaire = d_salaire.id_salaire 
            INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
            WHERE titre LIKE "%{job}%"
            GROUP BY pays 
            ORDER BY Salaire DESC;"""
            salaire_pays = pd.read_sql_query(query, conn)
            st.dataframe(salaire_pays.fillna("Manquante"), # on remplace les valeurs manquantes de Salaire par pays par "Manquante"
                         hide_index=True, use_container_width=True)
        st.divider()

        st.subheader(f"**_Salaire moyen d'un {job.lower()} par région_**")
        st.write("""**_Ici sont présentés les régions avec les meilleurs salaires, ainsi que les salaires moyens par région, 
                 le tout selon le poste sélectionné._**""")
        container = st.container(border=True)
        col1, col2 = container.columns([2,3])
        with col1:
            # L'utilisateur peut choisir le nombre de région à afficher :
            box = st.selectbox(f'**Choisissez le nombre de régions à afficher pour les meilleurs salaires en tant que {job.lower()} :**', 
                               range(3, 20))
        with col2:
            st.write(f':red[**_Les {box} meilleures régions_**]')
            # Requête sur le salaire moyen par région selon le poste sélectionné par l'utilisateur :
                # le salaire doit être compris entre 10000 et 150000 (sinon, pas de pertinence)
            query = f"""SELECT AVG(salaire_moyen) as Salaire, nom_region as Region FROM f_offres 
            INNER JOIN d_geo ON f_offres.id_geo = d_geo.id_geo 
            INNER JOIN d_salaire ON f_offres.id_salaire = d_salaire.id_salaire 
            INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
            WHERE titre LIKE "%{job}%"
            GROUP BY nom_region 
            HAVING Salaire < 150000 AND Salaire > 10000
            ORDER BY Salaire DESC;"""
            salaire_region = pd.read_sql_query(query, conn)
            top_region = salaire_region.head(box) # df créé en fonction du nombre de régions à afficher
            st.dataframe(top_region, hide_index=True, use_container_width=True)
        container.divider()
        query = f"""SELECT AVG(salaire_moyen) as Salaire, nom_region as Region FROM f_offres 
        INNER JOIN d_geo ON f_offres.id_geo = d_geo.id_geo 
        INNER JOIN d_salaire ON f_offres.id_salaire = d_salaire.id_salaire 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres  
        WHERE titre LIKE "%{job}%"
        GROUP BY nom_region 
        HAVING Salaire < 150000 AND Salaire > 10000
        ORDER BY Salaire DESC;"""
        salaire_region = pd.read_sql_query(query, conn)
        container.write(f":red[**_Salaire moyen d'un {job.lower()} par région_**]")
        # Histogramme de la requête :
        container.bar_chart(data=salaire_region, 
                            x='Region', y='Salaire', 
                            color='#900C3F', 
                            use_container_width=True)
        st.divider()

        st.subheader(f"**_Salaire moyen d'un {job.lower()} par département_**")
        st.write("""**_Ici sont présentés les départements avec les meilleurs salaires, 
                 ainsi que les salaires moyens par département, le tout selon le poste sélectionné._**""")
        container = st.container(border=True)
        col1, col2 = container.columns([2,3])
        with col1:
            box = st.selectbox(f'**Choisissez le nombre de départements à afficher pour les meilleurs salaires en tant que {job.lower()} :**', 
                               range(5, 100))
        with col2:
            st.write(f':red[**_Les {box} meilleurs départements_**]')
            # Requête sur le salaire moyen par département pour le poste sélectionné par l'utilisateur :
                # le salaire doit être compris entre 10000 et 150000
            query = f"""SELECT AVG(salaire_moyen) as Salaire, nom_departement as Departement FROM f_offres 
            INNER JOIN d_geo ON f_offres.id_geo = d_geo.id_geo 
            INNER JOIN d_salaire ON f_offres.id_salaire = d_salaire.id_salaire 
            INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres  
            WHERE titre LIKE "%{job}%"
            GROUP BY nom_departement 
            HAVING Salaire < 150000 AND Salaire > 10000
            ORDER BY Salaire DESC;"""
            salaire_dep = pd.read_sql_query(query, conn)
            top_dep = salaire_dep.head(box)
            st.dataframe(top_dep, hide_index=True, use_container_width=True)
        container.divider()
        query = f"""SELECT AVG(salaire_moyen) as Salaire, nom_departement as Departement FROM f_offres 
        INNER JOIN d_geo ON f_offres.id_geo = d_geo.id_geo 
        INNER JOIN d_salaire ON f_offres.id_salaire = d_salaire.id_salaire 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres  
        WHERE titre LIKE "%{job}%"
        GROUP BY nom_departement 
        HAVING Salaire < 150000 AND Salaire > 10000
        ORDER BY Salaire DESC;"""
        salaire_dep = pd.read_sql_query(query, conn)
        container.write(f":red[**_Salaire moyen d'un {job.lower()} par département_**]")
        container.bar_chart(data=salaire_dep, 
                            x='Departement', y='Salaire', 
                            color='#FFA07A', 
                            use_container_width=True, height=500) 
    
    # Onglet 3 - Contrats :
    with tab3:
        requete = """SELECT COUNT(profil) as Nombre, titre as Offres FROM f_offres 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
        GROUP BY Offres 
        ORDER BY Nombre DESC;"""
        position = pd.read_sql_query(requete, conn)
        jobs = ["Data analyst", "Data scientist", "Data engineer", "Data manager", "Data steward", "Ml engineer"]

        job = st.selectbox("**_Quel poste souhaitez-vous afficher pour l'onglet 'Contrats' ?_**", jobs)
        st.subheader('**_En France_**')
        st.write("**_Ici, vous pouvez retrouver les données liées aux différents types de contrats selon le poste sélectionné._**")
        container = st.container(border=True)
        col1, col2 = container.columns([1,2])
        with col1:
            st.write(':red[**_Types de contrats (global)_**]')
            # Requête sur le nombre d'offres par type de contrat :
                # le type de contrat doit être différent de "Paris" et "Paris, France"
            query = """SELECT COUNT(titre) as Offres, type_contrat as Contrat FROM f_offres
            INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres
            INNER JOIN d_contrat ON f_offres.id_contrat = d_contrat.id_contrat
            WHERE type_contrat NOT IN ('Paris, France', 'Paris')
            GROUP BY type_contrat 
            ORDER BY Offres DESC;"""
            contrat_global = pd.read_sql_query(query, conn)
            st.dataframe(contrat_global, hide_index=True, use_container_width=True)
        with col2:
            st.write(f':red[**_Types de contrats pour le poste de {job.lower()} :_**]')
            # Requête sur le nombre d'offres en France par type de contrat selon le poste sélectionné :
                # le type de contrat doit être différent de "Paris" et "Paris, France"
                # ce n'est pas pertinent de regarder les différents types de contrats hors France, les appellations ne sont pas les mêmes
            query = f"""SELECT COUNT(titre) as Offres, type_contrat as Contrat, pays as Pays FROM f_offres 
            INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
            INNER JOIN d_contrat ON f_offres.id_contrat = d_contrat.id_contrat 
            INNER JOIN d_geo ON f_offres.id_geo = d_geo.id_geo 
            WHERE pays = "France" AND titre LIKE "%{job}%"  AND type_contrat NOT IN ('Paris, France', 'Paris')
            GROUP BY type_contrat;"""
            contrat_pays = pd.read_sql_query(query, conn)
            custom_colors = ['#641e16', '#922b21', '#c0392b', '#F08080', '#E9967A', '#FA8072', '#FFA07A']
            # Donut de la requête :
            fig = px.sunburst(contrat_pays, path=["Pays", "Contrat"], values="Offres",
                                color_discrete_sequence=custom_colors)
            st.plotly_chart(fig, use_container_width=True) # affichage du donut
    
    # Onglet 4 - Expérience :
    with tab4:
        requete = """SELECT COUNT(profil) as Nombre, titre as Offres FROM f_offres 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
        GROUP BY Offres 
        ORDER BY Nombre DESC;"""
        position = pd.read_sql_query(requete, conn)
        jobs = ["Data analyst", "Data scientist", "Data engineer", "Data manager", "Data steward", "Ml engineer"]
        job = st.selectbox("""**_Quels postes souhaitez-vous afficher pour l'onglet 'Expérience' ?_**""", 
                           jobs)
        
        st.subheader('**_Expérience Requise_**')
        st.write("""**_Ici, vous pouvez retrouver le niveau d\'expérience requise (en années, si disponible), 
                 et si les débutants sont acceptés ou non pour le ou les postes sélectionnés._**""")
        
        container = st.container(border=True)
        container.write(':red[**_Répartition des niveaux d\'expérience (global)_**]')
        # Requête sur le nombre d'offres par niveau d'expérience (débutant vs. expérience exigée vs. non spécifié) :
        query = """SELECT COUNT(titre) as Offres, debutant_acceptee as Experience, annee_exper as Annee FROM f_offres
        INNER JOIN d_experience ON f_offres.id_experience = d_experience.id_experience
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres
        GROUP BY Experience 
        ORDER BY Offres DESC;"""
        exp = pd.read_sql_query(query, conn)
        custom_colors = ['#900C3F', '#f5b7b1', '#CD5C5C', '#FFA07A']
        # Camembert de la requête :
        fig = px.pie(exp, names='Experience', values='Offres', 
                     color='Offres', 
                     color_discrete_sequence = custom_colors)
        container.write(fig)
        #container.dataframe(exp, hide_index=True, use_container_width=True)

        container.divider()

        container.write(f":red[**_Répartition des niveaux d'expérience pour le poste de {job.lower()} :_**]")
        # Requête sur le nombre d'offres par niveau d'expérience selon le poste sélectionné par l'utilisateur :
        query = f"""SELECT COUNT(titre) as Offres, debutant_acceptee as Experience, annee_exper as Annee FROM f_offres
        INNER JOIN d_experience ON f_offres.id_experience = d_experience.id_experience
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
        WHERE titre LIKE "%{job}%"
        GROUP BY Experience 
        ORDER BY Offres DESC;"""
        exp = pd.read_sql_query(query, conn)
        custom_colors = ['#900C3F', '#f5b7b1', '#CD5C5C', '#FFA07A']
        fig = px.pie(exp, names='Experience', values='Offres', 
                     color='Offres', 
                     color_discrete_sequence = custom_colors)
        container.write(fig)

        container.write(f":red[**_Nombre d'années requises (quand requises) pour le poste de {job.lower()} :_**]")
        # Requête sur le nombre d'offres par année d'expérience requise selon le poste sélectionné par l'utilisateur :
        query = f"""SELECT COUNT(titre) as Offres, annee_exper as Annee, debutant_acceptee as Experience FROM f_offres
            INNER JOIN d_experience ON f_offres.id_experience = d_experience.id_experience
            INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
            WHERE titre LIKE "%{job}%" AND debutant_acceptee = "Experience Exigée" AND Annee >= 1
            GROUP BY Annee 
            ORDER BY Offres DESC;"""
        exp_deb = pd.read_sql_query(query, conn)
        custom_colors = ['#900C3F', '#f5b7b1', '#CD5C5C', '#FFA07A']
        fig=px.bar(exp_deb, 
                   x='Annee', y='Offres', 
                   color_discrete_sequence = custom_colors, 
                   width=600)
        container.write(fig)
        
        container.caption("_Il est possible que certaines informations liées à l'expérience soient manquantes._")

    # Onglet 5 - Cartographie :
    with tab5:
        container = st.container(border=True)
        container.subheader(":red[**_Cartographie des offres_**]")
        container.write("**_Le nombre d'offres par région :_**")
        # Requête du nombre d'offres par région :
        query = """SELECT COUNT(titre) as Offres, nom_region as Region FROM f_offres 
        INNER JOIN d_offres ON f_offres.id_offres=d_offres.id_offres 
        INNER JOIN d_geo ON f_offres.id_geo=d_geo.id_geo 
        GROUP BY nom_region ORDER BY Region DESC;"""
        map_region = pd.read_sql_query(query, conn)
        # Création de la carte des régions :
        with open("regions.json", "r", encoding="utf-8") as file:
            regions_data = json.load(file) # on récupère le fichier json des coordonnées des régions françaises

        fig_region = px.choropleth(
            map_region,  # notre df
            geojson=regions_data,
            locations='Region',  # noms des régions
            color='Offres',  # valeurs sélectionnées pour colorer chaque région
            color_continuous_scale='YlOrRd',
            featureidkey="properties.libgeo"  # chemin vers les id's du geojson
        )

        #fig_region.update_layout(width=800, height=700)

        # On veut uniquement la carte de la France :
        fig_region.update_geos(
            center={"lat": 45.8, "lon": 1.888334},  # coordonnées des centroïdes français
            projection_scale=17,  # ajustement de l'échelle pour n'afficher que la France
            visible=False  # dissimulation des contours de la carte
        )
        container.plotly_chart(fig_region, use_container_width=True) # affichage de la carte créée précédemment
        container.divider()

        container.write('**_Le nombre d\'offres par département :_**')
        # Requête du nombre d'offres par département :
        query = """SELECT COUNT(titre) as Offres, nom_departement as Departement FROM f_offres 
        INNER JOIN d_offres ON f_offres.id_offres=d_offres.id_offres 
        INNER JOIN d_geo ON f_offres.id_geo=d_geo.id_geo 
        GROUP BY nom_departement ORDER BY Departement DESC;"""
        map_dep = pd.read_sql_query(query, conn)
        
        with open("departement.json", "r",encoding="utf-8") as file:
            dep_data = json.load(file)
        
        fig_dep = px.choropleth(
            map_dep,  
            geojson=dep_data,
            locations='Departement',  
            color='Offres',  
            color_continuous_scale='YlOrRd',
            featureidkey="properties.libgeo" 
        )

        #fig_dep.update_layout(width=800, height=700)

        fig_dep.update_geos(
            center={"lat": 45.8, "lon": 1.888334},  
            projection_scale=17,  
            visible=False  
        )
        container.plotly_chart(fig_dep, use_container_width=True)
        container = st.container(border=True)
        container.subheader(":red[**_Cartographie des salaires_**]")
        container.write('**_Les salaires moyens par région :_**')
        # Requête sur le salaire moyen par région :
        query = """SELECT AVG(salaire_moyen) as Salaire, nom_region as Region, titre as Offres FROM f_offres 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres 
        INNER JOIN d_salaire ON f_offres.id_salaire = d_salaire.id_salaire 
        INNER JOIN d_geo ON f_offres.id_geo=d_geo.id_geo 
        GROUP BY nom_region ORDER BY Region DESC;"""
        map_region = pd.read_sql_query(query, conn)
        
        with open("regions.json", "r",encoding="utf-8") as file:
            regions_data = json.load(file)

        fig_region = px.choropleth(
            map_region,  
            geojson=regions_data,
            locations='Region',  
            color='Salaire',  
            color_continuous_scale='YlOrRd',
            featureidkey="properties.libgeo"  
        )

        #fig_region.update_layout(width=800, height=700)

        fig_region.update_geos(
            center={"lat": 45.8, "lon": 1.888334},  
            projection_scale=17,  
            visible=False  
        )
        container.plotly_chart(fig_region, use_container_width=True)

        container.divider()

    # Onglet 6 - Wordcloud :
    with tab6:
        jobs = ['Métiers de la data', 'Data Analyst', 'Data Scientist', 'Data Steward', 'ML Engineer', 'Data Engineer'] # liste des postes que l'utilisateur peut sélectionner

        job = st.selectbox("**_Quel poste souhaitez-vous afficher pour l'onglet 'Wordcloud' ?_**", jobs)
        job_min = job.lower()
        st.subheader('**_Nuage de mots_**')
        st.write(f':red[**_Voici les termes les plus fréquents dans les offres de "{job_min}" :_**]')

        # Nuage de mots pour chaque poste de la liste créée précédemment :
        if job_min == "data analyst" :
            st.image('wordcloud_data_analyst.png', 
                            caption="Nuage de mots - Data Analyst")
        
        elif job_min == "data scientist":
            st.image('wordcloud_data_scientist.png', 
                            caption="Nuage de mots - Data Scientist")
        
        elif job_min == "data steward":
            st.image('wordcloud_data_steward.png', 
                            caption="Nuage de mots - Data Steward")

        elif job_min == "ml engineer":
            st.image('wordcloud_ml_engineer.png', 
                            caption="Nuage de mots - ML Engineer")

        elif job_min == "data engineer":
            st.image('wordcloud_data_engineer.png', 
                            caption="Nuage de mots - Data Engineer")
        
        else:
            st.image('wordcloud_tout.png', 
                            caption='Nuage de mots (global)')

# Si la page "🤖 Les offres" est cliquée :
elif mainmenu == '🤖 Les offres':
    # On indique le LLM que nous allons choisir
    repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    st.title('💻 Les offres de la data')

    # On vérifie que la clé d'accès Huggingface a bien été indiqué (et son format)
    if not hf_api_key.startswith('hf_') and len(hf_api_key) != 37:
        st.warning('Entrez une 🤗 HuggingFace API key!', icon='⚠️')
    else:
        st.success("Thanks for the key! ", icon='🤖')

    # On crée une liste de métiers que l'utilisateur peut cliquer
    job_options = ['Data Analyst', 'ML Engineer', 'Data Scientist', 'Data Engineer']
    selected_job = st.radio('Quel emploi?', job_options)
    # On propose également la possibilité de pouvoir l'écrire
    st.markdown("Ton métier de rêve ne se trouve pas dans la liste? Ecris le pour voir si des offres existes ! ")
    custom_job = st.text_input('Entre le métier de tes rêves: (Attention, tant que des termes seront présent ici, vous ne pourrez pas choisir un métier de la liste en haut.)')

    # On indique le métier choisi actuellement pour tracer un possible changement
    if 'last_job_search' not in st.session_state:
        st.session_state.last_job_search = None

    # Si l'utilisateur a rentré un input tex, celui ci prend la priorité sur la liste pré-établi
    if custom_job:
        job_to_search = custom_job.lower()
    elif selected_job:
        job_to_search = selected_job.lower()
    else:
        job_to_search = None

    # On réinitialise la page si la recherche a changé
    if job_to_search != st.session_state.last_job_search:
        st.session_state.page = 0
        st.session_state.last_job_search = job_to_search

    con = sqlite3.connect('joboffers_dw.db') # Connexion à une base de données SQL créée préalablement

    # On réalise une requête SQL qui s'adapte au métier recherché.
    if job_to_search:
        like_clauses = " OR ".join(f"titre LIKE '%{job}%'" for job in job_to_search)
        query = f"""
        SELECT titre, profil, descriptif, source, date_complete, entreprise
        FROM f_offres 
        INNER JOIN d_offres ON f_offres.id_offres = d_offres.id_offres
        INNER JOIN d_source ON f_offres.id_source = d_source.id_source
        INNER JOIN d_temps ON f_offres.id_temps = d_temps.id_temps
        INNER JOIN d_entreprise ON f_offres.id_entreprise = d_entreprise.id_entreprise
        WHERE titre LIKE "%{job_to_search}%"
        ORDER BY date_complete DESC;
        """
    else:
        st.write("Please select or enter a job position.")

    # On réalise la requête SQL en insérer un try/except loop pour bloquer au cas où il y aurait une erreur (métier non retrouvé)
    try: 
        offres_df = pd.read_sql_query(query, con)   
        offres_df = offres_df.drop_duplicates()
        # S'il existe au moins une offre
        if offres_df.shape[0] > 0: 
            if 'page' not in st.session_state:
                # On indique que l'on est sur la première page
                st.session_state.page = 0

            # On crée des boutons précédent et suivant pour naviguer entre les offres
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                btn_prev, btn_next = st.columns(2)  # Deux colonnes pour les boutons
            # Si le bouton "précédent est cliqué",
            with btn_prev:
                if st.button('Précédent', type="primary"):
                    if st.session_state.page > 0: # Tant que la page est supérieur à 0 (pour rester dans la plage possible d'index)
                        st.session_state.page -= 1 # On diminue l'index de 1
                        st.session_state.messages = [] # On réinitialise les messages du chabtot
            # Si le bouton "suivant" est cliqué,
            with btn_next:
                if st.session_state.page != offres_df.shape[0]:
                    if st.button('Suivant', type="primary"):
                        if st.session_state.page < offres_df.shape[0] - 1: # Tant que l'on est pas sur la dernière page (les index commençant à 0)
                            st.session_state.page += 1 # On augmente l'index de 1
                            st.session_state.messages = []

            # Afficher les données de l'offre actuelle
            offre_display = offres_df.iloc[st.session_state.page, :]
            st.header(offre_display["titre"])
            st.markdown("**Source de l'offre:** " + offre_display["source"])
            st.markdown("**Date de publication:** " + offre_display["date_complete"])
            st.markdown("**Entreprise:** " + offre_display["entreprise"])
            st.markdown(offre_display["descriptif"])

            # Affichage du profil conditionnel à sa présence pour ne pas dénaturer l'affichage
            if "Non spécifié" not in offre_display["profil"]:
                st.markdown("Profil " + offre_display["profil"])
            
            # PARTIE CHATBOT ############################
            st.title("Avez-vous des questions sur l'offre?")
            texte_orange = "<p style='color: #f06f05; font-weight: bold;'> Mixtral est là pour toi!  Pensez à réinitialiser le chat entre les annonces!</p>"
            st.markdown(texte_orange, unsafe_allow_html=True)
            # Affichage conditionnel à la présence de la clé d'accès huggingface
            if hf_api_key.startswith('hf_') and len(hf_api_key) == 37:
                # Connexion avec le LLM
                llm = HuggingFaceHub(
                repo_id=repo_id,
                huggingfacehub_api_token=hf_api_key,
                model_kwargs={"temperature": 0.2, "max_new_tokens": 500}) # On indique certains paramètres (temperature [0/1]: ajout d'aléatoire, nbre de tokens par réponse)
                
                # On crée un document avec le titre, le descriptif et le profil requis de l'offre
                current_joboffer = offre_display["titre"] + offre_display["descriptif"] + offre_display["profil"]

                # On initialise le chat
                if "messages" not in st.session_state:
                    st.session_state.messages = []
                
                # On affiche les messsages de l'utilisateur et de l'IA entre chaque message
                for message in st.session_state.messages:
                    with st.chat_message(message["role"]):
                        st.markdown(message["content"])

                # Si présence d'un input par l'utilisateur,
                if prompt := st.chat_input(""):
                    if prompt.strip(): 
                        # On affiche le message de l'utilisateur
                        with st.chat_message("user"):
                            st.markdown(prompt)
                        # On ajoute le message de l'utilisateur dans l'historique de la conversation
                        st.session_state.messages.append({"role": "user", "content": prompt})
                        # On récupère la réponse du chatbot à la question de l'utilisateur
                        response = chat_response_generation(llm=llm, query=prompt, joboffer=current_joboffer, history = st.session_state.messages)
                    # On affiche la réponse du chatbot
                        with st.chat_message("assistant"):
                            st.markdown(response)
                    # On ajoute le message du chatbot dans l'historique de la conversation
                        st.session_state.messages.append({"role": "assistant", "content": response})
                # On ajoute un bouton pour réinitialiser le chat 
                if st.button("Réinitialiser le Chat", type="primary"):
                    st.session_state.messages = []
            else:
                st.error("Veuillez entrer la clé d'accès HuggingFace pour afficher le chatbot")
        else: 
            st.markdown("Il n'y a pas d'offres pour ce métier.")
    except: 
        st.warning("Nous ne trouvons pas ce métier dans notre base de données. Essayez un autre!")

# Si la page "🤖 Q/Abot" est cliquée :
elif mainmenu == '🤖 Q/Abot':
    
    # On connecte la base de donnée avec notre Q/Abot
    db = SQLDatabase.from_uri("sqlite:///joboffers_dw.db")
    
    # On indique le modèle de LLM
    repo_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"

    st.title('Chatbot 🗣️')
    st.toast('Here you can chat with Oliver')
    st.markdown("Bienvenue dans la partie 2.0 de notre application ! A votre tour d'être créatif et de poser les questions qui vous tarodent! ")
    st.markdown("Vous êtes mis en contact avec notre LLM français: Mixtral-8x7B !")

    # On affiche le Q/Abot qu'à la présence de la clé d'accès respectant le format requis
    if hf_api_key.startswith('hf_') and len(hf_api_key) == 37:
        st.header("Notre module de Question/Réponse")
        # On crée un formulaire d'envoie
        with st.form('my_form'):
            query = st.text_area('Quelle est votre question?', '')

            if not hf_api_key.startswith('hf_') and len(hf_api_key) != 37:
                    st.warning('Entrez une 🤗 HuggingFace API key!', icon='⚠️')
            else:
                    st.success("Thanks for the key! ", icon='🤖')
            
            # On crée un bouton pour envoyer la question
            submitted = st.form_submit_button('Submit')
            # Si le bouton est cliqué,
            if submitted:
                # Si la question n'est pas vide,
                if len(query) == 0:
                    st.error("Attention votre requête est vide !")
                else:
                    try:
                        # On se connecte au LLM
                        llm = HuggingFaceHub(
                            repo_id=repo_id,
                            huggingfacehub_api_token=hf_api_key,
                            model_kwargs={"temperature": 0.2, "max_new_tokens": 400}
                        )
                        # On récupère la réponse à la question
                        result = SQLquery2(query=query, llm=llm, db=db,verbose=True)
                        print(f'Sortie: {result}')
                        # On affiche la réponse
                        st.markdown(result)
                    except Exception as e:
                        # On renvoie un message d'erreur si le Q/Abot n'a pas pu répondre (question trop complexe ou non présente dans la base de donnée)
                        st.error('Je n\'ai pas réussi à répondre a votre question...', icon="🚨")
                        st.text("1) Vérifiez que votre clé API est correcte; 2) Essayez de reformuler votre réponse pour qu'elle soit plus claire")
                
            
        st.markdown("Je ne suis qu'un ChatBot étudiant, je n'ai pas encore été dopé ! Mes réponses peuvent tarder jusqu'à 20-30 secondes, soyez patient!\
                     Plus vous serez clair dans votre question, plus je serais rapide et plus je serais également précis dans ma réponse. N'hésitez pas à reformuler vos questions ou les rendre plus détaillé, surtout les plus complexes.")
        st.markdown("Attention, la base de donnée contient le département et la région de l'offre (pas la ville). Elle répondra donc toujours sur le département ou la région de la ville si cette dernière est précisée.")
        st.markdown("**Exemple de questions:**")
        st.caption('Le salaire d\'un data analyst est il plus élevé à Paris ou Lyon?')
        st.caption('Quel est le nombre d\'offres de data scientist à Lyon?')
        st.caption("Existe-t-il des offres de stage à Lille?")
    else: 
        st.error("Veuillez rentrer une clé d'accès HuggingFace pour pouvoir faire apparaître le Q/Abot.")    

elif mainmenu == 'Règles d\'utilisation IA':
    st.header("Quelques règles d'utilisation:")
    st.markdown("""
                - Pour pouvoir utiliser cette partie, il est nécessaire d'avoir créer un compte HuggingFace et d'avoir généré une clé API \
                pour pouvoir connecter Mixtral avec l'application. Voici un petit tutoriel: https://huggingface.co/docs/api-inference/quicktour#get-your-api-token \
                """)
    st.markdown("""
                - Le modèle large de langage (LLM) avec lequel vous intéragissez peut se tromper ou mal interpréter votre question. Soyez le plus précis et concis possible. Si le modèle renvoie une erreur, \
                pas de panique! Essayez simplement de reformuler votre question ou votre phrase.
                """)
    st.markdown("""
                - Une absence de réponse peut être du à l'absence de la réponse dans notre base d'information. 
                """)
    st.markdown("""
                - Plus la question est complexe, plus elle sera dur et risque de lui prendre du temps à interpréter. Ne soyez pas trop exigent avec lui, il fait de son mieux !! 
                """)
    st.markdown("""
                - Un comportement éthique est attendu quand vous intéragissez avec lui.
                """)