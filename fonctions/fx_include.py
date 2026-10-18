# Imports
from scipy.optimize import brentq
from datetime import datetime
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import aff3ct
import streampu as spu
import numpy as np
import math
import random 
import time
import sys
import json
import os

# Constantes et fichiers

DOSSIER_RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PARAM_JS = os.path.join(DOSSIER_RACINE, "json/param.json")
ERREURS_JS = os.path.join(DOSSIER_RACINE, "json/erreurs.json")
TX_JS = os.path.join(DOSSIER_RACINE, "json/tx_message.json")
RX_BOB_JS = os.path.join(DOSSIER_RACINE, "json/rx_message_bob.json")
RX_EVE_JS = os.path.join(DOSSIER_RACINE, "json/rx_message_eve.json")
IMG = os.path.join(DOSSIER_RACINE, "interface", "static", "logo.png")
META_DATA_JS = os.path.join(DOSSIER_RACINE, "json/meta_data.json")
TYPES = {"INCONNU": 0,"TEXTE": 1, "BINAIRE": 2, "IMAGE": 3}
CODE_TYPES = {0:"INCONNU", 1: "TEXTE", 2: "BINAIRE", 3: "IMAGE"}

# Variables par defaut
DEFAUT_VAR = {
        "nom":"DEFAUT",
        "N":1024,
        "K":1024,
        "simulation":True,
        "mode_securise":True,
        "amplification_confidentialite": False,  # PA : optionnel, désactivé par défaut
        "type_canal":"BSC",
        "p_bob":0.05,
        "p_eve":0.15,
        "snr_bob":100,
        "snr_eve":1,
        "MSG_TYPE":"TEXTE",
        "TX_MSG":TX_JS,
        "RX_MSG":RX_BOB_JS
}
