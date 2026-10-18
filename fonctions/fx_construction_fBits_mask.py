# Génération du masque de bits gelés (frozen bits) pour un code polaire BSC

import numpy as np
from .fx_construction_mi import generer_masque_bsc as _generer_masque_mi
from .fx_construction_z  import z_construction_bsc  as _z_construction_bsc


def generer_masque(N: int, K: int, p: float, methode: str = 'Z') -> np.ndarray:
    """Génère le masque de bits gelés pour un code polaire BSC(p).

    Paramètres
    ----------
    N       : taille du code (puissance de 2)
    K       : nombre de bits d'information
    p       : probabilité d'erreur du canal BSC
    methode : 'Z' (Bhattacharyya, défaut) ou 'MI' (Information Mutuelle)

    Retourne
    --------
    np.ndarray de taille N, dtype int32 :
        0 → bit d'information (K positions avec la meilleure qualité de canal)
        1 → bit gelé         (N-K positions restantes)

    Méthodes
    --------
    'MI' : utilise la construction exacte par information mutuelle (fx_construction_mi).
           Recommandée — implémente directement le Théorème 6 de Taleb 2022.

    'Z'  : utilise la construction par paramètre de Bhattacharyya (fx_construction_z).
           Implémente le Théorème 4 de Taleb 2022. Mathématiquement équivalente à 'MI'
           pour le BSC ; quelques différences de masque possibles (~5-10% des canaux)
           dues à l'arrondi flottant sur les canaux proches du seuil de sélection.
    """
    methode = methode.upper()

    if methode == 'MI':
        return _generer_masque_mi(N, K, p)

    elif methode == 'Z':
        if K > N:
            raise ValueError(f"K={K} ne peut pas dépasser N={N}.")
        z = _z_construction_bsc(N, p)
        indices_tries = np.argsort(z)          # petits Z = bons canaux
        frozen_bits = np.ones(N, dtype=np.int32)
        frozen_bits[indices_tries[:K]] = 0     # K meilleurs canaux → info
        return frozen_bits

    else:
        raise ValueError(f"Méthode inconnue : '{methode}'. Choisir 'MI' ou 'Z'.")
