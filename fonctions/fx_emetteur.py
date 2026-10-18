from .fx_include import *
from .fx_construction_fBits_mask import generer_masque

def generer_masque_polaire(K, N, type, param, methode='Z'):
    """Génère le masque optimal de bits figés (Frozen bits)"""
    if type == "BSC":
        frozen_bits = generer_masque(N, K, param, methode=methode)

    if type == "AWGN":
        # Pour l'instant pas de placement particulier (frozen bits au debut)
        frozen_bits = np.array([1]*(N-K) + [0]*K, dtype=np.int32)

    return frozen_bits

def encoder(u_bits, frozen_bits):
    """
    Encode les bits d'informations (u) en un mot de code (x) de taille N.
    Retourne le mot de code et le masque utilisé.
    """
    
    u_spu = spu.int8(u_bits)
    x_spu = aff3ct.polar.encode(u_spu, frozen_bits)
    
    x_bits = np.array(x_spu).flatten().astype(np.int8)
    return x_bits, frozen_bits

def moduler_bpsk(bits):
    """
    Modulation BPSK : Convertit les bits (0 et 1) en (+1.0 et -1.0).
    """
    signal = 1.0 - 2.0 * bits
    return np.array(signal, dtype=np.float32)

