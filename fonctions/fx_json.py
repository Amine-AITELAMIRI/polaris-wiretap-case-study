from .fx_include import *

# Fonctions simples
def lire_json(fichier):
    if not os.path.exists(fichier):
        raise FileNotFoundError(f"Le fichier {fichier} est introuvable.")
    with open(fichier, 'r') as f:
        return json.load(f)

def ecrire_json(fichier, donnees):
    with open(fichier, 'w') as f:
        json.dump(donnees, f, indent=4)

# Gestion des erreurs
def ajouter_erreur(nom_programme, message):
    """
    Ajoute une erreur dans le fichier JSON. S'il n'existe pas, il le crée.

    """

    data = {
        "nombres_erreurs": 0,
        "programmes_en_erreur": []
    }
    
    if os.path.exists(ERREURS_JS):
        try:
            with open(ERREURS_JS, "r") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            pass
    
    #Ajoute l'erreur du programme
    programme_trouve = False
    for prog in data.get("programmes_en_erreur", []):
        if prog["nom_programme"] == nom_programme:
            # Le programme existe, on ajoute juste l'erreur à sa liste
            prog["erreurs"].append({"message": message})
            programme_trouve = True
            break
            
    # 4. Si c'est la première erreur pour ce programme
    if not programme_trouve:
        data["programmes_en_erreur"].append({
            "nom_programme": nom_programme,
            "erreurs": [{
                "message": message
            }]
        })
        
    # 5 Mettre à jour 
    data["nombres_erreurs"] = int(data.get("nombres_erreurs")) + 1
    
    with open(ERREURS_JS, "w") as f:
        json.dump(data, f, indent=4)

def lire_erreurs(nom_programme=None):
    """
    Lit les erreurs. 
    Paramètre optionnel 'nom_programme' : pour ne récupérer 
    QUE les erreurs d'un programme spécifique.
    """
    if not os.path.exists(ERREURS_JS):
        return [] # Pas de fichier = pas d'erreur
        
    with open(ERREURS_JS, "r") as f:
        data = json.load(f)

    liste_programmes = data.get("programmes_en_erreur", [])
    nb_err = data.get("nombres_erreurs",0)
    # Pour les erreurs d'un programme en particulier
    if nom_programme:
        for prog in liste_programmes:
            if prog["nom_programme"] == nom_programme:
                return prog["erreurs"]
        return [] # Le programme demandé n'a pas d'erreur
        
    return nb_err,liste_programmes

def effacer_erreurs():
    """
    Efface les erreurs. 
    """

    data = {
        "nombres_erreurs": 0,
        "programmes_en_erreur": []
    }

    ecrire_json(ERREURS_JS, data)



# Fonctions specifiques

def lire_param():
    """
    Lire le param.json et s'assure que les paramètres essentiels sont là.
    Fournit des valeurs par défaut si besoin.
    """
    data = {}
    erreur_detectee = None

    # Tentative de lecture du fichier
    try:
        data = lire_json(PARAM_JS)
    except FileNotFoundError:
        erreur_detectee = f"Le fichier {PARAM_JS} est introuvable. Valeurs par défaut appliquées."
    except json.JSONDecodeError:
        erreur_detectee = f"Le fichier {PARAM_JS} est mal formaté (erreur de syntaxe JSON). Valeurs par défaut appliquées."

    # On lit toutes les valeurs pour etre certain qu'elles sont la et mise par defaut au cas ou 
    nom = data.get("nom", DEFAUT_VAR["nom"])
    mode_securise = data.get("mode_securise", DEFAUT_VAR["mode_securise"])
    amplification_confidentialite = bool(
        data.get(
            "amplification_confidentialite",
            DEFAUT_VAR.get("amplification_confidentialite", False),
        )
    )
    N = data.get("N", DEFAUT_VAR["N"])
    K = data.get("K", DEFAUT_VAR["K"])
    type_canal=data.get("type_canal", DEFAUT_VAR["type_canal"])

    simulation = data.get("simulation", DEFAUT_VAR["simulation"])
    snr_bob, snr_eve, p_bob, p_eve = None, None , None, None

    if simulation:
        param_simu = data.get("parametres_simulation", {})
        type_canal = param_simu.get("type_canal", DEFAUT_VAR["type_canal"])

        if type_canal == "BSC":
            bsc_data = param_simu.get("canal_bsc", {})
            p_bob = bsc_data.get("p_bob", DEFAUT_VAR["p_bob"])
            p_eve = bsc_data.get("p_eve", DEFAUT_VAR["p_eve"])
            
        elif type_canal == "AWGN":
            awgn_data = param_simu.get("canal_awgn", {})
            snr_bob = awgn_data.get("snr_bob", DEFAUT_VAR["snr_bob"])
            snr_eve = awgn_data.get("snr_eve",  DEFAUT_VAR["snr_eve"])


    # Vérification
    if K > N:
        nom = "PARAMETTRES CORRIGÉS"
        erreur_detectee = f"Incohérence: K ({K}) > N ({N}). Les tailles par défaut (1024/512) ont été forcées."
        N = DEFAUT_VAR["N"]
        K = DEFAUT_VAR["K"]

    # reconstruit data dictionnaire
    parametres = {
        "nom": nom,
        "mode_securise": mode_securise,
        "amplification_confidentialite": amplification_confidentialite,
        "simulation": simulation,
        "N": N,
        "K": K,
        "parametres_simulation": {
            "type_canal":type_canal, 
            "canal_bsc": {
            "p_bob": p_bob,
            "p_eve": p_eve
            },
            
            "canal_awgn": {
            "snr_bob": snr_bob,
            "snr_eve": snr_eve
            }
        }
    }

    return parametres, erreur_detectee

def ecrire_param(nom=DEFAUT_VAR["nom"],mode_securise=DEFAUT_VAR["mode_securise"],simulation=DEFAUT_VAR["simulation"],N=DEFAUT_VAR["N"],K=DEFAUT_VAR["K"],type_canal=DEFAUT_VAR["type_canal"],p_bob=DEFAUT_VAR["p_bob"],p_eve=DEFAUT_VAR["p_eve"],snr_bob=DEFAUT_VAR["snr_bob"],snr_eve=DEFAUT_VAR["snr_eve"],amplification_confidentialite=DEFAUT_VAR.get("amplification_confidentialite", False)):
    """
    Ecrire le param.json.
    Fournit des valeurs par défaut si besoin.
    """

    parametres = {
        "nom": nom,
        "mode_securise": mode_securise,
        "amplification_confidentialite": bool(amplification_confidentialite),
        "simulation": simulation,
        "N": N,
        "K": K,
        "parametres_simulation": {
            "type_canal": type_canal, 
            
            "canal_bsc": {
            "p_bob": p_bob,
            "p_eve": p_eve
            },
            
            "canal_awgn": {
            "snr_bob": snr_bob,
            "snr_eve": snr_eve
            }
        }
    }
    
    ecrire_json(PARAM_JS,parametres)


def ecrire_message(donnees,fichier=DEFAUT_VAR["TX_MSG"],temps=datetime.now().isoformat(timespec='seconds')):
    """
    Ecrit un message dans le fichier JSON tx_message.
    """

    data = {
        "timestamp": temps,
        "corps_message": donnees
    }

    ecrire_json(fichier, data)

def lire_message(fichier=DEFAUT_VAR["RX_MSG"]):
    """
    Lit et renvoie fichier message JSON .
    Retourne: (time_message, donnees, erreur ou None)
    """
    try:
        data = lire_json(fichier)
    except FileNotFoundError:
        return None, None, f"Le fichier {fichier} est introuvable."

    donnees = data.get("corps_message", None)
    time_message = data.get("timestamp", None)
    erreur_detectee = None

    if donnees is None or donnees == "":
        donnees = None
        erreur_detectee = f"Le message est vide ou le champ 'donnees' est manquant."

    if time_message is None:
        time_message = datetime.now().isoformat(timespec='seconds',)

    return time_message, donnees, erreur_detectee

def lire_meta_data():
    """Lit les métadonnées du message. Ne plante pas si le fichier n'existe pas encore."""
    try:
        data = lire_json(META_DATA_JS)
        return data if data is not None else {}
    except FileNotFoundError:
        # Si le fichier n'a pas encore été créé par Alice, on renvoie du vide
        return {}

def ecrire_meta_data(data):
    ecrire_json(META_DATA_JS,data)
