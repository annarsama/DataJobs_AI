import pandas as pd
from datetime import datetime
import re
import os

# Fonction pour importer les csv contenant les offres obtenus lors du web scraping
def load_sources():
    # On crée une liste par source
    poleemploi = []
    makesense = []
    empterritorial = []
    # On récupère l'emplacement actuel
    cur_dir = os.getcwd()
    # Pour tous les fichiers du dossier,
    for file in os.listdir(cur_dir):
        # Si c'est un fichier csv
        if file.endswith(".csv"):
            # Et qu'il provient de pole-emploi
            if "poleemploi" in file:
                # On importe le fichier
                df = pd.read_csv(file, encoding='utf-8-sig')
                # On crée une colonne ave le nom de la source
                df["file"] = file
                # On l'ajoute à la liste correspondante
                poleemploi.append(df)
            elif "makesense" in file:
                df = pd.read_csv(file, encoding='utf-8-sig')
                df["file"] = file
                makesense.append(df)
            elif "empterritorial" in file:
                df = pd.read_csv(file, encoding='utf-8-sig')
                df["file"] = file
                empterritorial.append(df)
    # Ensuite, on joint les jeux de données correspondants ensemble
    poleemploi_df = pd.concat(poleemploi, ignore_index=True)
    makesense_df = pd.concat(makesense, ignore_index=True) 
    empterritorial_df = pd.concat(empterritorial, ignore_index=True)

    return poleemploi_df, makesense_df, empterritorial_df

# Fonction pour normaliser les dates selon la source
def normalisation_date(df):
    if "poleemploi" in df["file"][0]:
        # On transforme le type de la colonne date
        df["date_publication"] = pd.to_datetime(df["date_publication"], format='%Y-%m-%dT%H:%M:%S.%fZ')
        # On récupère les différentes informations temporelles
        df["année"] = df["date_publication"].dt.year
        df["mois"] = df["date_publication"].dt.month
        df["jour"] = df["date_publication"].dt.day
        df["date_complete"] = df["date_publication"].dt.strftime('%Y-%m-%d')
    
    elif "empterritorial" in df["file"][0]:
        df["date_publication"] = pd.to_datetime(df["date_publication"], format='%Y-%m-%d')
        df["année"] = df["date_publication"].dt.year
        df["mois"] = df["date_publication"].dt.month
        df["jour"] = df["date_publication"].dt.day
        df["date_complete"] = df["date_publication"].dt.strftime('%Y-%m-%d')

    # On applique une fonction particulière pour jobsthatmakesense qui n'a pas toujours la date dans le même format
    elif "makesense" in df["file"][0]:
        df = df.apply(date_nonspecifie, axis=1)
    
    return df

# Fonction pour s'adapter au format de date de l'offre pour ensuite récupérer les informations temporelles.
def date_nonspecifie(row):
    if row['date_publication'] != 'Non spécifié':
        try: # Permet de s'adapter selon le format de la date
            date_publication = pd.to_datetime(row['date_publication'], format='%Y-%m-%d %H:%M:%S')
        except ValueError:
            date_publication = pd.to_datetime(row['date_publication'], format='%Y-%m-%d')

        row['année'] = int(date_publication.year)
        row['mois'] = int(date_publication.month)
        row['jour'] = int(date_publication.day)
        row['date_complete'] = date_publication.strftime('%Y-%m-%d')
    else:
        row['année'] = None
        row['mois'] = None
        row['jour'] = None
        row['date_complete'] = None
    return row

# Fonction pour normaliser le salaire en un salaire moyen annuel
def normalisation_salaire(x):
    if "annuel" in x:
        # On détecte les chiffres
        num = re.findall(r'\d+', x)
        # Si l'on a les deux limites de l'intervalle, on calcule la moyenne
        if len(num) >= 4: 
            mean_sal = int((int(num[0]) + int(num[2])) / 2)
        # Si l'on a qu'une valeur, on garde que cette valeur
        elif len(num) > 0 and len(num) < 4:
            mean_sal = int(num[0])
        # Si c'est un cas particulier, on indique 'Non spécifié'
        else: 
            mean_sal = None
        return mean_sal

    # Si c'est le salaire mensuel, on calcule le salaire annuel 
    elif "mensuel" in x:
        num = re.findall(r'\d+', x)
        mean_sal = int(num[0]) * 12
        return mean_sal

    # Si c'est le salaire horaire,
    elif 'horaire' in x:
        num = re.findall(r'\d+', x)
        # On récupère le salaire horaire moyen ou la valeur unique
        if len(num) >= 4: 
            mean_horaire = int((int(num[0]) + int(num[2])) / 2)
        elif len(num) > 0 and len(num) < 4:
            mean_horaire = int(num[0])
        # On calcule le salaire annuel pour 37,5h/semaine pour 52 semaines         
        mean_sal = mean_horaire * 37.5 * 52
        return mean_sal

    else:
        return None

# Fonction pour normaliser le niveau d'expérience en années d'expérience requises
def normalisation_experience(x):
    # Si l'expérience attendue est en année, on extrait ce chiffre (en évitant la fausse détection de débutant)
    if "an" in x and "débutant" not in x:
        num =  re.findall(r'\d+', x)
        exper = int(num[0]) 
        return(exper)
    # Si l'expérience attendue est mensuelle, on extrait et on transforme en annuel
    elif "mois"in x:
        num =  re.findall(r'\d+', x)
        exper = int(num[0]) /12
        return exper
    # Si les débutants sont acceptés, on assigne 0 année attendue
    elif 'débutant' in x:
        exper = 0
        return exper
    # Sinon, on renvoit une cellule vide
    else:
        return None

# Fonction pour normaliser les types de contrat.
def normalisation_typecontrat(df):
    # On crée un dictionnaire pour traduire les accronymes non connus par les utilisateurs
    dict_typecontrat = {
        "CDI": "CDI",
        "CDD": "CDD",
        "Fonction Publique" : "Fonction Publique",
        "MIS": "Intérim",
        "LIB": "Freelance",
        "FRA": "Freelance",
        "Stage": "Stage"
        }
    df["type_contrat"] = df["type_contrat"].apply(lambda x: dict_typecontrat.get(x, x))
    
    return(df)


# Fonction pour nettoyer les titres et ne garder que les parties clés.
def normalisation_metier(x):
    # On crée l'expression régulière
    patterns = [re.compile(pattern) for pattern in ["\(H/F\)", "\(F/H\)", "H/F", "F/H", 
                                                "\(h/f\)", "\(f/h\)", "h/f", "f/h",
                                                "\(IT\)", "\(it\)", "/ Freelance"]]
    patterns.append(re.compile(r"\(.*?\)")) # Pour enlever les parties entre parenthèses
    # On enlève les références aux genres recherchés de la personne 
    for pattern in patterns:
        x = pattern.sub('', x)

    # Si "-" est présent, cela indique que d'autres informations sont présentes
    if " - " in x:
        # On garde la partie du titre de l'offre qui comporte des mots d'intérets
        splitted = x.split(" - ")
        keywords = ["data", "ingénieur", "donnée", "analyst", "développeur", "developer","intelligence artificielle" ,"ops", "assistant", "responsable", "manager", "chef", "charge", "chargé", "engineer"]

        # On recherche les parties du titre ayant des mots clés (keywords)
        for element in splitted:
            element_lower = element.lower() 
            if any(keyword in element_lower for keyword in keywords): # On garde la partie du titre ayant un des keywords
                return element.capitalize()
        return x.capitalize()
    else:
        return x.capitalize()


# Fonction pour compléter le code postal si ne contient que 4 chiffres (1000 à 01000)
def code_4chiffres(x):
    if len(x) == 4:
        x = '0'+ x
    return x


# Fonction pour créer le code postal quand simplement les deux premiers fiches rentrés (ex: 75 - Paris)
def numeric_dep(x):
    # On récupère les chiffres
    num =  re.findall(r'\d+', x)
    # Si présent,
    if len(num) != 0:
        # Et ayant deux chiffres,
        if len(num[0]) == 2:
            # On construit le code postal
            code_p = str(num[0]) + '000'
            return code_p
    return x

# Fonction pour compléter numeric_dep en cas de grandes villes  (Lyon, Paris, Marseille)
def grande_villes(x): 
    if x == "75000":
        return '75001'
    elif x == '69000':
        return '69001'
    elif x == '13000':
        return '13001'
    else:
        return x
    
# Fonction pour rentrer le nom du pays si indiqué dans la mauvaise colonne ou pas indiqué
def normalisation_pays(x, geo):
    region_set = set(geo['nom_region'])
    # Check for non-NA and match in region set
    if pd.isna(x["nom_region"]) == False and x["nom_region"] in region_set:
        return 'France'

    # Specific location checks
    if x["lieu"] in ["Ile-de-France", "Pays de la Loire"]:
        return 'France'

    # Handling NA in nom_region
    if pd.isna(x["nom_region"]):
        if "France" in x["lieu"] and "Ile-de-France" not in x["lieu"]:
            return 'France'
        elif "Luxembourg" in x["lieu"]:
            return 'Luxembourg'
        elif "Belgique" in x["lieu"]:
            return 'Belgique'
        else: 
            return "Non Spécifié"
    
    return "Non Spécifié"

# On normalise les "Non spécifiés"
def normalisation_pays_inconnu(x):
    if x == "Non spécifié":
        return "Non Spécifié"
    else:
        return x

# Fonction pour normaliser ces deux régions mal indiquées
def normalisation_region(x): 
     if pd.isna(x["nom_region"]) and x["lieu"] == "Ile-de-France":
          return "Île-de-France"
     elif pd.isna(x["nom_region"]) and x["lieu"] == "Pays de la Loire":
          return 'Pays de la Loire'
     else: 
          return x["nom_region"]
     
def normalisation_departement(x):
    if x["ville"] == "Paris":
        return "Paris"
    elif x["ville"] == "Saint-Ouen-sur-Seine":
        return "Seine-Saint-Denis"
    elif x["ville"] == "Montreuil":
        return "Seine-Saint-Denis"
    elif x["ville"] == "Auray":
        return 'Morbihan'
    elif x["ville"] == "Toulouse":
        return "Haute-Garonne"
    elif x["ville"] == "Pantin":
        return "Seine-Saint-Denis"
    
    elif x["pays"] in ["Belgique", "Canada", "Suisse", "Luxembourg"]:
        return x["ville"] 
    else: 
        return x["nom_departement"]
     
# Fonction pour ne pas avoir de données manquantes
def normalisation_null(x):
    if pd.isna(x):
        return "Non spécifié"
    else: 
        return x

# Fonction pour normaliser les départements selon la ville
def normalisation_departement_par_ville(row):
    if "Paris" in row["ville"]:
       return "Paris"
    if row["ville"] == "Bruxelles":
        return "Belgique"
    elif row["ville"] == "Saint-Ouen-sur-Seine":
        return "Seine-Saint-Denis"
    elif row["ville"] == "La Défense":
        return "Paris"
    elif row["ville"] == "L'Isle-Jourdain":
        return "Gers"
    elif row["ville"] == "Marseille":
        return "Bouches-du-Rhône"
    elif row["ville"] == "France":
        return "Non spécifié"
    else:
        return row["nom_departement"]
    
# Fonction pour normaliser les régions selon les départements
def normalisation_region_par_departement(row):
    if row["nom_departement"] in ["Paris", "Seine-Saint-Denis"]:
        return "Île-de-France"
    if row["nom_departement"] == "Belgique":
        return "Belgique"
    elif row["nom_departement"] == "Gers":
        return "Occitanie"
    elif row["nom_departement"] == "Bouches-du-Rhône":
        return "Provence-Alpes-Côte d'Azur" 
    elif row["ville"] == "France":
        return "Non spécifié"
    else:
        return row["nom_region"]

# Fonction pour normaliser l'adresse (colonne "lieu" dans le jeu de données) et retirer département, région, pays.
def normalisation_adresse(df, file_geo):
    # On importe les variables géographiques
    geo = pd.read_csv(file_geo)
    # On retire les variables n'ayant peu d'intéret
    geo.drop(columns=['code_commune_INSEE', 'nom_commune_postal',
                  'libelle_acheminement', 'ligne_5', 'latitude', 'longitude',
                  'code_commune', 'article',  'nom_commune_complet',
                   'code_departement','code_region'], inplace=True)


    df_merge = pd.DataFrame()
    if "lieu" in df.columns:
        geo.drop(columns=['nom_commune'], inplace=True)
        # On enlève les lignes en doublons suite au retrait des variables
        geo = geo.drop_duplicates()
        # On transforme le type des données pour la future jointure
        df["lieu"] = df["lieu"].astype(str)
        geo["code_postal"] = geo["code_postal"].astype(str)

        # On prépare les codes postales pour la jointure dans les jeux de données respectifs
        geo["code_postal"] = geo["code_postal"].apply(code_4chiffres)
        df["lieu"] = df["lieu"].apply(numeric_dep)
        df["lieu"] = df["lieu"].apply(grande_villes)
        # On réalise une jointure à gauche pour préserver la structure du jeu de données d'offres d'emploi
        df_merge = df.merge(geo,  left_on="lieu", right_on="code_postal", how="left")
        df_merge["code_postal"] = df_merge["code_postal"].apply(normalisation_null)
        df_merge["pays"] = df_merge.apply(lambda x: normalisation_pays(x, geo), axis=1)
        df_merge["nom_region"] = df_merge.apply(normalisation_region, axis=1)

    elif "ville" in df.columns:
        geo.drop(columns=['code_postal'], inplace=True)
        # On enlève les lignes en doublons suite au retrait des variables
        geo = geo.drop_duplicates()
        df_merge = df.merge(geo,  left_on="ville", right_on="nom_commune", how="left")
        df_merge["nom_departement"] = df_merge.apply(normalisation_departement_par_ville, axis=1)
        df_merge["nom_region"] = df_merge.apply(normalisation_region_par_departement, axis=1)
        df_merge.drop(columns=["nom_commune", "ville"], inplace=True)

    # On normalise les différentes colonnes si df_merge s'est bien construit
    if not df_merge.empty:
        df_merge["nom_region"] = df_merge["nom_region"].apply(normalisation_null)
        df_merge["nom_departement"] = df_merge["nom_departement"].apply(normalisation_null)

    df_merge["pays"]  = df_merge["pays"].apply(normalisation_pays_inconnu)


    return df_merge

# Fonction pour ajouter la région en se basant sur les départements.
def ajout_region(df, file_geo):
    # On importe les variables géographiques
    geo = pd.read_csv(file_geo)
    # On retire les variables n'ayant peu d'intéret
    geo.drop(columns=['code_commune_INSEE', 'nom_commune_postal',
                  'libelle_acheminement', 'ligne_5', 'latitude', 'longitude',
                  'code_commune', 'article', 'nom_commune', 'code_postal', 'nom_commune_complet',
                   'code_departement','code_region'], inplace=True)
    geo = geo.drop_duplicates()
    df_merge = pd.DataFrame()
    # On joint notre jeu de données gouv de données géographiques avec notre base de données
    df_merge = df.merge(geo,  left_on="departement", right_on="nom_departement", how="left")
    df_merge.drop(columns=["departement"], inplace=True)

    return df_merge

 # Fonction pour enlever les emojis et emoticons   
def normalisation_emojis(x):
    # Regex avec les différents emojis et symbols
    emoji_pattern = re.compile("["
                           u"\U0001F600-\U0001F64F"  # emoticons
                           u"\U0001F300-\U0001F5FF"  # symbols & pictographs
                           u"\U0001F680-\U0001F6FF"  # transport & map symbols
                           u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
                           u"\U00002702-\U000027B0"
                           u"\U000024C2-\U0001F251"
                           "]+", flags=re.UNICODE)

    # On les enlèves de chaque text
    x_noemoji = emoji_pattern.sub('', x)

    return x_noemoji



