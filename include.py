# Imports
from fonctions.fx_include import *

from fonctions import fx_json
from fonctions import fx_interface
from fonctions import fx_emetteur
from fonctions import fx_canal
from fonctions import fx_recepteur
from fonctions import fx_construction_mi
from fonctions import fx_privacy_amp


import subprocess, os, io, base64, time, threading
from PIL import Image

ROLES = ("alice", "bob", "eve")