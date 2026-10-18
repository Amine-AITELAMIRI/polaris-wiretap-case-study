"""
fx_privacy_amp.py — Amplification de confidentialité par hash linéaire GF(2)
=============================================================================
Implémente l'étape d'amplification de confidentialité du schéma de Wyner.

Principe (lemme du hachage résiduel) :
  Après décodage, Bob dispose de K_info bits avec TEB ≈ 0 et
  Eve en dispose avec une information mutuelle partielle MI_Eve.
  On applique une compression linéaire A : {0,1}^K_info → {0,1}^K_secure
  avec K_secure ≤ K_info − MI_Eve_bits.
  L'IM d'Eve sur les K_secure bits de sortie tend alors vers 0.

Construction de A (forme systématique) :
  A = [I_{K_secure} | P]   (K_secure × K_info)
  P est une matrice K_secure × (K_info − K_secure) binaire pseudo-aléatoire
  générée à partir d'une graine publique partagée entre Alice et Bob.

Encodage (Alice) :
  1. Choisir R ∈ {0,1}^(K_info−K_secure) aléatoire (leurre)
  2. Calculer c = P @ R  mod 2
  3. Poser u = [message ⊕ c ; R]
  Vérification : A @ u = (message ⊕ c) ⊕ (P @ R) = message  ✓

Décodage (Bob) :
  M̂ = A @ û  mod 2  =  û[:K_secure] ⊕ (P @ û[K_secure:])
  Bob retrouve message exactement (si aucune erreur sur les K_info bits).

Sécurité (Eve) :
  Eve a une connaissance partielle de u (MI < 1 bit/bit).
  La compression par A mélange cette connaissance sur K_secure < K_info bits.
  Par le lemme du hachage résiduel, son IM sur M̂ est ≈ 0
  dès que K_secure ≤ K_info − H∞(U | Y_Eve).
"""

import numpy as np
from fonctions.fx_construction_mi import H2


# ── Graine publique par défaut ──────────────────────────────────────────────
# Partagée entre Alice et Bob ; rend la matrice A déterministe.
PA_SEED_DEFAUT = 42


def compute_k_secure(K_info: int, p_bob: float, p_eve: float) -> int:
    """Nombre de bits sûrs par trame selon la capacité secrète de Wyner.

    K_secure = floor(K_info × Cs / C_bob)

    où Cs = C_bob − C_eve est la capacité secrète (BSC).
    Ce ratio représente la fraction de la fenêtre d'information réellement
    inaccessible à Eve au sens information-théorique.

    Parameters
    ----------
    K_info : int
        Nombre de sous-canaux I disponibles par trame.
    p_bob  : float
        Probabilité de croisement du canal Bob.
    p_eve  : float
        Probabilité de croisement du canal Eve.

    Returns
    -------
    int
        K_secure ≥ 1.
    """
    C_bob = 1.0 - H2(p_bob)
    C_eve = 1.0 - H2(p_eve)
    Cs    = max(0.0, C_bob - C_eve)
    frac  = Cs / C_bob if C_bob > 1e-9 else 0.0
    return max(1, int(K_info * frac))


def _matrice_P(K_secure: int, K_info: int, seed: int) -> np.ndarray:
    """Partie aléatoire P de A = [I_{K_secure} | P].

    K_secure × (K_info − K_secure), binaire, déterministe via seed.
    """
    rng = np.random.default_rng(seed)
    return rng.integers(0, 2, (K_secure, K_info - K_secure), dtype=np.int8)


def pa_encode(message: np.ndarray, K_info: int, seed: int = PA_SEED_DEFAUT) -> np.ndarray:
    """Encodage PA : K_secure bits message → K_info bits pour les positions I.

    Parameters
    ----------
    message : ndarray, shape (K_secure,), dtype int8
        Bits du message à transmettre.
    K_info  : int
        Taille de la fenêtre I (nombre de positions d'information dans u).
    seed    : int
        Graine publique pour construire P (identique côté Alice et Bob).

    Returns
    -------
    ndarray, shape (K_info,), dtype int8
        Vecteur u à placer dans les positions indices_info_in_u.
    """
    K_secure = len(message)
    K_rand   = K_info - K_secure

    P = _matrice_P(K_secure, K_info, seed)

    # Vecteur de rembourrage aléatoire (leurre pour Eve)
    R = np.random.randint(0, 2, K_rand, dtype=np.int8)

    # Correction pour garantir A @ u = message (mod 2)
    c      = (P.astype(np.int64) @ R.astype(np.int64)) % 2
    u_head = (message.astype(np.int64) ^ c).astype(np.int8)

    return np.concatenate([u_head, R])


def pa_decode(u_hat: np.ndarray, K_secure: int, seed: int = PA_SEED_DEFAUT) -> np.ndarray:
    """Décodage PA : K_info bits reçus → K_secure bits message.

    M̂ = A @ û  mod 2  =  û[:K_secure] ⊕ (P @ û[K_secure:]  mod 2)

    Parameters
    ----------
    u_hat    : ndarray, shape (K_info,), dtype int8
        Bits extraits des positions I après décodage polaire.
    K_secure : int
        Nombre de bits de message attendu.
    seed     : int
        Graine publique (doit correspondre à celle utilisée à l'encodage).

    Returns
    -------
    ndarray, shape (K_secure,), dtype int8
        Bits du message récupérés.
    """
    K_info = len(u_hat)
    P = _matrice_P(K_secure, K_info, seed)

    correction = (P.astype(np.int64) @ u_hat[K_secure:].astype(np.int64)) % 2
    return (u_hat[:K_secure].astype(np.int64) ^ correction).astype(np.int8)
