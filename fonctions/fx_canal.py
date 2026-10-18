from .fx_include import *

def canal_bsc(signal, p):
    """BSC: inverse chaque bit avec probabilité p."""
    N = len(signal)
    bruit = np.random.choice([1, -1], N, p=[1-p, p])

    return (signal*bruit).astype(np.float32)


def canal_awgn(signal, snr_db):
    """AWGN : Ajoute du bruit gaussien sur le signal."""
    N = len(signal)

    sigma = np.sqrt(1/(2*(10**(snr_db/10))))
    bruit = sigma * np.random.randn(N)

    return (signal + bruit).astype(np.float32) # Retourne des signaux bruités

def canal(signal,type,param_bob,param_eve):
    "Simule le canal BSC ou AWGN renvoie le signal pour le recepteur legitime (bob) et l'espion (eve)"

    if type == "BSC":
        signal_bob=canal_bsc(signal,param_bob)
        signal_eve=canal_bsc(signal,param_eve)

    if type == "AWGN":
        signal_bob=canal_awgn(signal,param_bob)
        signal_eve=canal_awgn(signal,param_eve)

    return signal_bob, signal_eve
