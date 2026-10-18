# Documentation : Projet POLARIS

## Imports et dépendances (fonctions/fx_include.py)


Ce module centralise les imports les dependances, constantes globales, chemins des fichiers et paramètres par défaut qui sont neséssaire pour faire fonctionner les fonctions ou les scripts.

---

```python
from fonctions.fx_include import *
```

###  Imports

Bibliothèques utilisées :

- datetime  
- time  
- aff3ct  
- streampu (spu)  
- numpy  
- random  
- sys  
- json  
- os  

###  Constantes et variables globales
- DOSSIER_RACINE : `/POLARIS_S8`
- PARAM_JS: Fichier json des paramètres de la simulation.
- ERREURS_JS: Fichier d'erreurs.
- TX_JS: Fichier message envoyé.
- RX_BOB_JS: Fichier message recu par Bob (destinataire légitime).
- TX_JS: Fichier message recu par Eve (espion).

- TYPE et CODE_TYPE : Valeur possibles repésentant les types de messages envoyés.

- DEFAUT_VAR: Dictionnaires des valeurs par défaut (parametrage,type de message par defaut,fichier message par defaut...)

---
# I. Gestion des Données et Interface

## 1. Structure des fichiers JSON (/json)

Le projet utilise plusieurs fichiers JSON pour configurer la simulation et stocker les messages ou gerer les erreurs.

- Voir `exemple_fx_json.py` pour tester les fonctions et comprendre leur utilisation.

### param.json

Définit les paramètres des transmissions ou des simulations :

- **nom** : Identifiant de la configuration  
- **N** : Taille du mot de code (ex: 1024)  
- **K** : Taille du message d'information (ex: 512)  
- **simulation** : Booléen activant le mode simulation
- **mode_securise** : Booléen activant l'encodage sécurisé  
- **parametres_simulation** :
  - Canal BSC : (progabilité d'inversions des bits du canal pour bob et eve)
    - `p_bob`
    - `p_eve`
  - Canal AWGN : (rapport signal sur bruit du canal pour bob et eve)
    - `snr_bob`
    - `snr_eve`

---

### tx_message.json

Stock le message à envoyer :

- **timestamp** : Date de création du message  
- **corps_message** : Chaîne (de caracteres) de bits représentant le message (texte, binaire ou image)

---

### rx_message_bob.json / rx_message_eve.json

Stockent les messages reçus et décodés par Bob (destinataire légitime) ou Eve (espion) :

- **timestamp** : Date de création du message  
- **corps_message** : Chaîne (de caracteres) de bits représentant le message (texte, binaire ou image)

---

### erreurs.json

Permet le stockage et la gestions des erreurs rencontrées durant l'exécution :

- **nombres_erreurs** : Stock le nombre d'erreur, utile pour savoir si une nouvelle erreur est apparue 
- **programmes_en_erreur** : Liste des programmes ayant une ou plus erreurs :

  - **nom_programme** : Nom du programme
    - **erreurs**: Liste des erreurs de ce programme.
      - **message** : Message d'erreur.

---

## 2. Fonctions JSON (fx_json.py)

Ce module gère toutes les interactions avec les fichiers JSON.

### lire_json(fichier)
  - Simple lecture du fichier json spécifié.

### ecrire_json(fichier, donnees)
  - Ecriture de `donnees` dans le fichier json spécifié.

### lire_param()

- Charge les paramètres depuis `param.json`
- Renvoie des valeurs par défaut (DEFAUT_VAR) si le fichier est manquant ou mal formaté :

### ecrire_param(nom,mode_securise,simulation,N,K,type_canal,p_bob,p_eve,snr_bob,snr_eve)

- Ecrit les paramètres dans `param.json`
- Met les valeurs par défaut (DEFAUT_VAR) le parametre n'est pas fourni

### ecrire_message(donnees, fichier)

- Enregistre une chaîne de bits dans le fichier spécifié (par defaut le fichier est TX_JS)
- Ajoute un horodatage automatique

### lire_message(fichier)

- Extrait le timestamp et le corps du message  (par defaut le fichier est RX_JS)
- Retourne une erreur si le message est vide

### ajouter_erreur(nom_programme, message)

- Ajoute une erreur dans `erreurs.json`
- Si le programme a deja une erreur, ellle est ajoutée à sa liste.

### lire_erreurs(nom_programme)

- Lit les erreurs dans `erreurs.json`
- Si on ne fourni pas de parametre la fonction renvoie toutes les erreurs, et si on donne un nom de programme on recois uniquement les erreurs de ce programme.

### effacers_erreur()

- Efface totutes les erreurs dans `erreurs.json`

---

## 3. Fonctions Interface (fx_interface.py)

Fonctions permettant la gestion des types de message et de la conversion de données lisible pour l'interface ou formatées pour la transmission. 

- Voir `exemple_fx_interface.py` pour tester les fonctions et comprendre leur utilisation.

### Gestion du Type

Pour envoyer des messages typés on ajoute un entete de 8 bits qui représente le type dans le corps du message (`corps_message`)
#### encapsuler_type(bits_str, type_msg)

Ajoute un en-tête de 8 bits :

- 0 → INCONNU
- 1 → TEXTE
- 2 → BINAIRE
- 3 → IMAGE

- Cela concatène le message (chaine de caractère de bits) `bits_str` et les 8 bits coresspondant a `type_msg` (TEXTE,...).

#### decapsuler_type(bits_str)

Sépare :

- En-tête
- Corps du message

- La fonction renvois le message (chaine de caractère de bits) et le type (TEXTE,...) représenté par le 8 premier bits de `bits_str`.
---

### Conversions de format

#### bits_to_numpy(bit_str)

- Convertit la chaine de caractère `bits_str` (stoquée dans le json par exemple) en vecteur NumPy.


#### numpy_to_bits(bit_np)
- Convertit le vecteur NumPy `bit_np` en chaine de caratère


#### text_to_bits(text)
- Conversion texte → bits (8 bits par caractère)
- L'entrée et la sortie sont des chaine de caractères

#### bits_to_text(bit_str)
- Conversion inverse bits → texte
- L'entrée et la sortie sont des chaine de caractères

#### image_to_numpy(image)

- Convertit une image PIL en bits
- Ajoute un en-tête de 40 bits :
  - 16 bits : hauteur
  - 16 bits : largeur
  - 8 bits : nombre de canaux

#### numpy_to_image(bits_np)

- Reconstruit une image PIL
- Utilise l'en-tête de 40 bits
- L'image renvoyée peut etre lue grace a ImageShow.show(image)

---

# II. Chaîne de Transmission

## 4. Fonctions emmeteur (fx_emmeteur)

Fonctions utiles du coté de l'emmeteur du message.

### generer_masque_polaire(K, N)

- Crée un vecteur de frozen bits
- Les (N-K) premiers bits → figés (1)
- Les K derniers bits → information (0)

### encoder(u_bits, K, N)

- Encodage polaire via la bibliothèque AFF3CT
- Utilise le masque de frozen bits

### moduler_bpsk(bits)

Conversion bits (1 ; 0) vers signal (-1 ; 1) :

- 0 → +1.0
- 1 → -1.0

---

## 5. fx_canal

Simule les perturbations du signal.

### canal_bsc(signal, p)

- Canal Binaire Symétrique
- Inversion de signe avec probabilité p

### canal_awgn(signal, snr_db)

- Ajout de bruit gaussien blanc additif en fonction de `snr_db`.

### canal(signal, type, param_bob, param_eve)

- Fait passer le signal dans le canal en fonction de son type.
- Applique les paramètres de Bob et Eve et renvoie leurs signaux recus respectifs.

---

## 6. fx_recepteur

Fonctions utiles du coté du recepteur du message.


#### demoduler_bpsk_awgn(signal_recu, snr_db)

- Calcule les LLR pour un canal AWGN

#### demoduler_bpsk_bsc(signal_recu, p)

- Calcule les LLR pour un canal BSC

#### demoduler_bpsk(signal_bob,signal_eve, type_canal, param_bob, param_eve)

- Calcule les LLR pour Eve et Bob en fonction du `type_canal`.


#### decoder(llrs, frozen_bits)

- Décodage du code polaire en fonction des `llrs` et des `frozen_bits`

---

# III. Exemple d'une simulation

Script `main_simulation.py` :

Le script suppose qu'un message a été écrit pars l'interface dans le fichier `TX_JS` et que les paramètres `PARAM_JS` sont renseignés. A la fin de la simulation on l'interface peut lire les fichiers `RX_BOB_JS` et `RX_EVE_JS` pour voir le resulat de la simulation.

## 1. Etapes du script

- Effacement des erreurs précédentes
- Lecture des paramètres depuis `param.json`
- Lecture du message depuis `tx_message.json`
- Conversion en vecteur NumPy
- Encodage
- Modulation
- Passage dans le canal simulé
- Bob et Eve reçoivent des signaux différents
- Calcul des LLR
- Décodage polaire
- Reconversion en chaîne de bits
- Enregistrement dans :
  - `rx_message_bob.json`
  - `rx_message_eve.json`

---

