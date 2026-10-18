# Construction polaire BSC par information mutuelle (Théorème 6)
#
# Formules de polarisation (§3.1.1) :
#   I₀   = 1 - H₂(p)                                   (capacité initiale)
#   f₁(I) = 1 - H₂( 2·H₂⁻¹(1−I)·(1 − H₂⁻¹(1−I)) )   (canal "−", Théorème 6)
#   f₂(I) = 2I − f₁(I)                                  (canal "+", Lemme 19)

from scipy.optimize import brentq
import numpy as np


def H2(p: float) -> float:
    """Entropie binaire H₂(p) = -p·log₂(p) - (1-p)·log₂(1-p)."""
    p = float(np.clip(p, 0.0, 1.0))
    if p == 0.0 or p == 1.0:
        return 0.0
    return -p * np.log2(p) - (1.0 - p) * np.log2(1.0 - p)


def H2_inv(x: float, tol: float = 1e-12) -> float:
    """Inverse de l'entropie binaire, restreinte à p ∈ [0, 0.5]."""
    x = float(np.clip(x, 0.0, 1.0))
    if x <= 0.0:
        return 0.0
    if x >= 1.0:
        return 0.5
    return brentq(lambda p: H2(p) - x, 0.0, 0.5, xtol=tol)


def f1_bsc(I: float) -> float:
    """Transition canal "−" : f₁(I) = 1 - H₂(2p(1-p)), avec p = H₂⁻¹(1-I)."""
    I = float(np.clip(I, 0.0, 1.0))
    if I <= 0.0:
        return 0.0
    if I >= 1.0:
        return 1.0
    p = H2_inv(1.0 - I)
    return 1.0 - H2(2.0 * p * (1.0 - p))


def f2_bsc(I: float) -> float:
    """Transition canal "+" : f₂(I) = 2I − f₁(I)  (Lemme 19)."""
    return float(np.clip(2.0 * I - f1_bsc(I), 0.0, 1.0))


def mi_construction_bsc(N: int, p: float) -> np.ndarray:
    """Calcule le vecteur d'information mutuelle des N sous-canaux d'un BSC(p).

    Retourne un tableau de taille N : mi[i] = I(W_N^(i+1)).
    """
    if N <= 0 or (N & (N - 1)) != 0:
        raise ValueError(f"N doit être une puissance de 2, reçu {N}.")
    if not (0.0 <= p <= 0.5):
        raise ValueError(f"p doit être dans [0, 0.5], reçu {p}.")

    n_niveaux = int(np.log2(N))
    canaux = np.array([1.0 - H2(p)], dtype=np.float64)

    for k in range(n_niveaux):
        suivants = np.empty(2 * len(canaux), dtype=np.float64)
        for j, I in enumerate(canaux):
            suivants[2 * j]     = f1_bsc(I)  # enfant "−"
            suivants[2 * j + 1] = f2_bsc(I)  # enfant "+"
        canaux = suivants

    return canaux


def generer_masque_bsc(N: int, K: int, p: float) -> np.ndarray:
    """Génère le masque de bits figés via la construction IM-BSC.

    Les K positions avec la plus grande IM deviennent des bits d'information (0),
    les N-K restantes sont figées (1).
    """
    if K > N:
        raise ValueError(f"K={K} ne peut pas dépasser N={N}.")

    mi = mi_construction_bsc(N, p)
    indices_tries = np.argsort(mi)

    frozen_bits = np.ones(N, dtype=np.int32)
    frozen_bits[indices_tries[N - K:]] = 0  # K meilleures positions → info

    return frozen_bits


def afficher_mi_bsc(N: int, p: float) -> np.ndarray:
    """Affiche un résumé du vecteur IM pour un BSC(p) de longueur N."""
    mi = mi_construction_bsc(N, p)
    I0 = 1.0 - H2(p)
    print(f"Construction IM-BSC  (N={N}, p={p})")
    print(f"  Capacite I0 = {I0:.6f}")
    print(f"  IM moyenne  = {mi.mean():.6f}")
    print(f"  Sous-canaux avec IM > 0.9 : {(mi > 0.9).sum()}")
    print(f"  Sous-canaux avec IM < 0.1 : {(mi < 0.1).sum()}")
    return mi
