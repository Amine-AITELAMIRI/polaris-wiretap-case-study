import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fonctions.fx_json import *

#Exemple d'utilisation des fonctions :
effacer_erreurs()

n,e=lire_erreurs()
print("----Erreurs vide",e)

ajouter_erreur("mon_programme.py", "ne fonctionne pas")
n,e=lire_erreurs()
print("----Erreur",e)

ecrire_param(nom="Config avec une erreur fait expres",N=1024,K=5120)
configuration = lire_json(PARAM_JS)
print("----Config apres Ecriture des parametres()",configuration)

configuration,e = lire_param()
if e != None:
    ajouter_erreur("lecture_des_param.py", e)

print("----Config renvoiyée (pré-corrigée pour continuer l'execution du programme)",configuration)

n,error=lire_erreurs("lecture_des_param.py")
print("----Nouvelle erreur detectée lors de la lecture des param",error)

print("----On peut corriger l'erreur du fichier des parametres")
ecrire_param()
configuration = lire_json(PARAM_JS)

print("----Parametres par defaut dans le fichier",configuration)

ecrire_message("01100010011011110110111001101010011011110111010101110010",TX_JS)

t,msg,e = lire_message(TX_JS)
print("----Message ecrit ",t,msg,e)
