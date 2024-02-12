from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
from langchain.chains import create_sql_query_chain


################ Q/A BOT with DB ################ 

# Création du template du check de securité
def template_security():
    template_security = """<s>[INST]
    Tu es le gardien de notre base de données. Tu agis juste avant que la question soit traduite en requête SQL. Ton rôle est d'identifer des questions qui guiderait à des requêtes SQL qui altererait l'intégrité de la base de données.
    Si la question pourrait guider à une requête qui altererait l'intégrité de la base de données, réponds "Question non ethique". Si la question ne peut pas guider à une requête qui altererait l'intégréité, réponds "RAS".

    Renvoie juste la phrase de réponse "Question non éthique" ou "RAS". Rien de plus.

    Voici la phrase à vérifier: 
    {question}
    [/INST]
    """
    return template_security

# Création du template du correcteur géographique
def template_geocorrector():
    template_geo_correct = """ <s>[INST]
        Ton rôle est de vérifier que les départements et régions soient bien orthographiés. 
        Réalise cela en identifiant les lieux dans la question et en les corrigeant. Ta réponse doit contenir seulement la phrase actualisée, pas plus d'information.
        Transforme toujours les villes en leur département.
        Si PACA ou Provence-Alpes-Cote-D'azur est demandé, renvoies toujours que ses départements (Tu dois inclure seulement ceux dont tu es sur).

        Par exemple: 
        Pour un data scientist, est-il plus intéressant d'aller en Ile de France ou Rhone Alpes?
        [/INST]
        Pour un data scientist, est-il plus intéressant d'aller en Île-de-France ou Auvergne-Rhône-Alpes? </s>
        <s> [INST]
        Phrase à vérifier:
        {question}
        [/INST]
        Phrase corrigée:
    """
    return template_geo_correct

# Création du template du text-to-SQL
def template_sql():
    template_sql = """ <s>[INST] Vous êtes un expert en SQLite. À partir d'une question, créez d'abord une requête SQLite syntaxiquement correcte à exécuter, puis examinez les résultats de la requête et renvoyez la réponse à la question.
        La requête ne doit jamais renvoyer plus de 15 lignes de valeurs.
        Ne renvoies jamais les colonnes id (ex: id_contrat, id_salaire, etc.).
        Ne demandez jamais toutes les colonnes d'une table. Vous ne devez interroger que les colonnes nécessaires pour répondre à la question. 
        Veillez à n'utiliser que les noms de colonnes que vous pouvez voir dans les tableaux ci-dessous. Veillez à ne pas demander des colonnes qui n'existent pas. Faites également attention à ce que chaque colonne se trouve dans chaque tableau.
        Veillez à utiliser la fonction date('now') pour obtenir la date du jour, si la question porte sur "aujourd'hui".
        Utilise la variable AVG(d_entreprise.salaire_moyen) quand l'on te parle de salaire.
        Pour compter, utilises la commande COUNT. Quand on te demande si quelque chose existe, compte l'occurence de cette catégorie.

        Attention, d_offres.titre représente le nom du métier de l'offre. Il est important d'appeler d_offres.titre quand l'utilisateur parle d'un métier, dans ce cas utiliser d_offres.titre LIKE '%métier%'.
        Si l'utilisateur demande des compétences particulières, chercher dans d_offres.titre, d_offres.descriptif et d_offres.profil.
        Si l'utilisateur demande une entreprise particulière, joindre la table d_entreprise et utiliser la variable "entreprise". 
        
        Voici une description des tables pour t'aider à savoir laquelle joindre (JOIN):
        - f_offres: Table de faits des offres avec les différents ids connectant aux différentes tables
        - d_offres: Table sur les données textuelles des offres (nom métier (toujours en minuscule), description de l'offre, profil recherché)
        - d_geo: Table sur les données géographiques de l'offre (pays, nom_région, nom_département)
        - d_temps: Table sur les dates de publications de l'offre
        - d_salaire: Table sur le salaire moyen des offres ("salaire_moyen" est la variable incluant le salaire de l'offre).
        - d_experience: Table sur le niveau d'experience (en année) requis avec annee_exper (nombre d'années requises) et debutant_acceptee (variable avec deux modalitées: "Débutant"/Expérience Requise)
        - d_contrat: Table sur le type de contrat (CDI, CDD, Stage, Alternance). Utilise LIKE.
        - d_entreprise: Table sur les entreprises des offres ("entreprise" est la variable qui regroupe les offres)

        Utilisez le format suivant pour créer une requête SQL:

        Question: Question
        SQLQuery: SQL Query to run
        SQLResult: Result of the SQLQuery
        Answer: Final answer here

        Utilise seulement les tables suivantes:
        {table_info}

        Pour comparer des catégories, utilises la commande GROUP BY.

        Tu ne peux pas utiliser UPDATE ou DELETE.

        Question: {input}[/INST]
        """
    return template_sql

# Création du template pour le RAG
def template_response():
    template_response = """
    <s>[INST]
    Tu es un agent français chargé de répondre à des questions concernant des offres de travail sur la Data.\
    Tu dois utiliser l'information donnée ('Réponse à la requête") pour répondre à cette question entre guillements,\
    c'est la réponse de la base de données à la requête entre guillements. \
    
    Si la zone "Réponse à la requête" est une liste de plus de 10 éléments uniques, n'en décrire que 10 maximum et expliquer à l'utilisateur\
    que ce sont certains exemples pour sa requête.  Attention, ne pas citer toute la liste.
    Les salaires sont en euro. Les années d'expériences sont en année.
    
    {sql_query}

    Réponse à la requête:
    {sql_answer}

    Question:
    "{query}"

    Réalisons cela pas à pas: 
    - Identifie si tu as suffisament d'information pour répondre à la question.
    - Si tu as suffisament d'information pour répondre précisément ou en partie à la question, tu dois répondre en français à la question  comme un humain (exemple: Il y a...).\
    - Si tu ne peux pas la déduire dépuis l'information retournée,\
    tu dois expliquer que tu ne peux pas répondre de façon polie, n'invente pas.\

    Ton output doit suivre le format suivant: 
    Explication : Une explication de ton raisonneent
    Réponse : Ta réponse finale
    [/INST]
    """
    return template_response

# Réponse de l'outil check de securité
def generate_security(llm, query, template_security):
    # On crée un template du prompt avec avec la variable que nous allons introduire
    prompt_security = PromptTemplate(input_variables=["question"], template=template_security)
    # On crée une chaine qui réalisera l'intéraction avec le LLM choisi
    chain = LLMChain(prompt=prompt_security, llm=llm)
    # On active notre chaine pour notre question
    corrected_query = chain.invoke({"question": query})
    # On renvoie la réponse.
    return corrected_query["text"]

# Réponse de l'outil correcteur geographique
def generate_geocorrect(llm, query, template_geo_correct):
    prompt_geo = PromptTemplate(input_variables=["question"], template=template_geo_correct)
    chain = LLMChain(prompt=prompt_geo, llm=llm)
    corrected_query = chain.invoke({"question": query})
    return corrected_query["text"]

# Réponse de l'outil text-to-SQL
def generate_sql_query(llm, query, db, template_sql):
    prompt_sql = PromptTemplate(input_variables=["input", "table_info"], template=template_sql)
    chain = create_sql_query_chain(llm, db, prompt=prompt_sql)
    sql_query = chain.invoke({"question": query})
    return sql_query

# Execution de la requête SQL
def run_sql_query(sql_query, db):
    sql_answer = db.run(sql_query)
    if len(sql_answer) == 0:
        sql_answer = "Cette information n'est pas présente dans la database."
    return sql_answer

# Réponse de l'outil RAG
def generate_response(llm, query,sql_query, sql_answer, template_response, verbose=True):
    prompt = PromptTemplate(template=template_response, input_variables=["sql_query","sql_answer","query"])
    print(sql_answer)
    llm_chain = LLMChain(prompt=prompt, llm=llm)
    response = llm_chain.run({"sql_query": sql_query,
                           "sql_answer": sql_answer,
                           "query": query})
    # Garde seulement la partie réponse (sans l'explication)
    if "Explication :" in response: 
        explication, final_response = response.split("Réponse :")
        if verbose == True:
            print(f'Explication: {explication}')
    else:
        final_response = response


    return final_response


# Fonction générale du Q/A bot.
def SQLquery2(query, llm, db, verbose=False):
    temp_sql = template_sql()
    temp_response = template_response()
    template_geo_correct = template_geocorrector()
    template_sec = template_security()
    # Lance le contrôle de sécurité
    security_check = generate_security(llm, query, template_sec).rstrip()
    if verbose == True:
        print(security_check)
    # Si l'indicateur de danger n'est pas présent, nous réalisons la suite des étapes
    if "non éthique" not in security_check: 
        # On lance le correcteur d'étiquettes géographiques
        geo_q = generate_geocorrect(llm, query,template_geo_correct).rstrip()
        if verbose == True:
            print(geo_q)
        # On lance le text-to-SQL
        sql_q = generate_sql_query(llm, geo_q, db, temp_sql).replace("\\","")
        if verbose == True:
            print(sql_q)
        # On exécute la requête SQL
        sql_a = run_sql_query(sql_q, db)
        if verbose == True:
            print(sql_a)
        # On lance le RAG pour la réponse finale.
        response_sqlquery2 = generate_response(llm, geo_q,sql_q, sql_a, temp_response, verbose=verbose)
        if verbose == True:
            print(response_sqlquery2)
        return response_sqlquery2
    else: 
        response = "Attention, votre question est destinée à mettre en péril notre base de données. Nous ne le permettrons pas! "
        return response


################ CHATBOT ################ 

# Création du prompt du Chatbot conversationnel
def template_chat_prompt():
    template_chat = """
    <s>[INST] Tu es Oliver, un agent chargé de converser avec des utilisateurs sur des offres d'emploi.
    Adapte toi à la question pour répondre, si besoin tu disposes de l'offre d'emploi et de l'historique pour répondre.

    Offre d'emploi: 
    {job_offer}

    Historique de la conversation:
    {historique}

    Format de la réponse: 
    - Réponds en français seulement à la Question. Tu disposes de l'offre d'emploi et de l'historique pour répondre. N'invente pas d'information.
    - Réponds uniquement à la question, sois le plus concis possible.
    - Si tu n'a pas les informations pour répondre, réponds que tu ne peux pas répondre à la question, n'inventes pas.\
     
    Question:
    {query}
    [/INST]

    Réponse:
    """
    return template_chat

# Fonction du ChatBot conversationnel
def chat_response_generation(llm, query, joboffer, history):
    template_chat = template_chat_prompt()
    prompt_chat = PromptTemplate(input_variables=["job_offer", "historique", "query"], template=template_chat)
    chain = LLMChain(llm=llm, prompt=prompt_chat)
    chat_response = chain.run({"query": query,
                               "job_offer": joboffer,
                               "historique": history
                               })
    return chat_response

