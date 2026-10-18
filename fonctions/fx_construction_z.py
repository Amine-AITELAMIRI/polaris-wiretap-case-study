import math
import numpy as np


# ─────────────────────────────────────────────────────────────────
#  1. CONSTRUCTION DE L'ARBRE DE BHATTACHARYYA
# ─────────────────────────────────────────────────────────────────

def f1(Z):
    """Canal dégradé : combine deux canaux Z en un canal moins bon."""
    return Z * np.sqrt(2 - Z**2)

def f2(Z):
    """Canal amélioré : combine deux canaux Z en un canal meilleur."""
    return Z**2

def z_construction_bsc(N: int, p: float) -> np.ndarray:
    """
    Calcule le vecteur de Bhattacharyya Z des N sous-canaux d'un BSC(p).

    Paramètres
    ----------
    N : taille du code polaire (doit être une puissance de 2)
    p : probabilité d'erreur du canal BSC

    Retourne
    --------
    np.ndarray de taille N : Z[i] ∈ [0,1], petit = bon canal
    """
    if N <= 0 or (N & (N - 1)) != 0:
        raise ValueError(f"N doit être une puissance de 2, reçu {N}.")
    if not (0.0 <= p <= 0.5):
        raise ValueError(f"p doit être dans [0, 0.5], reçu {p}.")

    n_niveaux = int(np.log2(N))
    z0 = 2.0 * math.sqrt(p * (1.0 - p))   # Z initial du BSC(p)
    canaux = np.array([z0], dtype=np.float64)

    for _ in range(n_niveaux):
        suivants = np.empty(2 * len(canaux), dtype=np.float64)
        for j, z in enumerate(canaux):
            suivants[2 * j]     = f1(z)   # sous-canal dégradé
            suivants[2 * j + 1] = f2(z)   # sous-canal amélioré
        canaux = suivants

    return canaux

# Partition, optimisation des seuils et visualisation Wyner
# → déplacés dans fonctions/fx_construction_wyner.py
