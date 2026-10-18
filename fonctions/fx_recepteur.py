from .fx_include import *

def demoduler_bpsk_awgn(signal_recu, snr_db):
    """Reçoit des ondes du canal awgn, calcule les LLR pour chaque bit."""
    N = len(signal_recu)

    # Le modem doit connaître le bruit pour bien estimer les probabilités
    sigma = np.sqrt(1 / (2 * (10 ** (snr_db / 10))))

    llrs = (2 * signal_recu) / sigma
    
    return np.array(llrs, dtype=np.float32)

def demoduler_bpsk_bsc(signal_recu, p):
    """
    Reçoit des ondes du canal bsc, calcule les LLR pour chaque bit.
    """
    llrs = signal_recu * np.log((1 - p) / p)
    
    return llrs.astype(np.float32)

def decoder(llrs, frozen_bits):
    """
    Décodeur Polaire : prend LLRS et le masque envois les bits d'information originaux.
    Le décodeur utilise SCL avec L=4 et l'implémentation NAIVE.
    Ce choix a été retenu pour conserver un comportement stable sur les tailles
    de blocs utilisées dans le projet.
    """
    # L'implémentation FAST de pyaff3ct est instable au-delà de N=1024.
    # On force donc NAIVE avec L=4.
    N = len(llrs)
    L = 4 if N <= 4096 else 4

    cwd, u_hat = aff3ct.polar.decode_siho(
        llrs, frozen_bits,
        decoder_type='SCL', L=L, implem='NAIVE'
    )

    # Premier candidat de la liste SCL = score le plus élevé
    bits_corriges = np.array(u_hat)[0]
    return bits_corriges.astype(np.int8)

def demoduler_bpsk(signal_bob,signal_eve,type,param_bob,param_eve):
    """
    Demodule le signal recu en fonction du canal BSC ou AWGN, renvoie les LLRS pour le decodeur polaire
    """

    if type == "BSC":
        llrs_bob=demoduler_bpsk_bsc(signal_bob,param_bob)
        llrs_eve=demoduler_bpsk_bsc(signal_eve,param_eve)

    if type == "AWGN":
        llrs_bob=demoduler_bpsk_awgn(signal_bob,param_bob)
        llrs_eve=demoduler_bpsk_awgn(signal_eve,param_eve)

    return llrs_bob, llrs_eve
