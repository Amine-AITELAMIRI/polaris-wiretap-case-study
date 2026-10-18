import aff3ct
import streampu as spu
import numpy as np
import random 
import sys

# Paramètres :
SEED = 0
p = 0.05          # probabilité du canal BSC
N = 16384         # taille du mot de code 
K_FRAME = 128     # taille trame envoyée

decodage_args = {
    'decoder_type': 'SCL',
    'L': 2,
    'implem': 'NAIVE'
}

random.seed(SEED)


# Fonctions intermédiaires :
def generation_message():
    message = " ".join(sys.argv[1:])    
    print("Message envoyé : ", message)
    message_bytes = message.encode("utf-8")
    bits = ''.join(format(byte, '08b') for byte in message_bytes)
    u_bits = np.array([int(b) for b in bits], dtype=np.int8)
    return message, u_bits

def canal_bsc(bits, p):
    """BSC: inverse chaque bit avec probabilité p."""
    sortie = []
    for bit in bits:
        bit = int(bit)
        if random.random() < p:
            sortie.append(1 - bit)
        else:
            sortie.append(bit)
    return np.array(sortie, dtype=np.int8)

def recuperation_message(bits):
    bits = np.array(bits)
    octets = bits.reshape(-1, 8)
    valeurs = octets.dot(1 << np.arange(7, -1, -1))
    return "".join(chr(v) for v in valeurs)


message, u_bits_all = generation_message()
K_total = len(u_bits_all) # Longueur originale (avant padding)
frozen_bits = np.array([1] * (N - K_FRAME) + [0] * K_FRAME, dtype=np.int32) # Frozen bits

# 0-padding pour trames dont la longeur < K_FRAME
pad_len = (K_FRAME - (K_total % K_FRAME)) % K_FRAME
if pad_len > 0:
    u_bits_padded = np.concatenate([u_bits_all, np.zeros(pad_len, dtype=np.int8)])
else:
    u_bits_padded = u_bits_all

# Boucle while sur les trames
i = 0

x_all = []          # tous les x (encodés) concaténés
y_all = []          # toutes les sorties canal concaténées
u_hat_all = []      # tous les bits décodés concaténés

while i < len(u_bits_padded):
    trame = u_bits_padded[i:i + K_FRAME]          # K_FRAME bits
    u = spu.int8(trame)

    # Encodage
    x = aff3ct.polar.encode(u, frozen_bits)
    x_array = np.array(x).flatten().astype(np.int8)
    x_all.append(x_array)

    # Canal
    y = canal_bsc(x_array, p)
    y_all.append(y)

    # LLR (BSC)
    L0 = np.log((1 - p) / p)
    llrs = np.array([(1 - 2*bit) * L0 for bit in y], dtype=np.float32)

    # Décodage
    cwd, u_hat = aff3ct.polar.decode_siho(llrs, frozen_bits, **decodage_args)
    u_hat = np.array(u_hat).flatten().astype(np.int8)
    u_hat_all.append(u_hat)

    i += K_FRAME

# Concaténation
x_concat = np.concatenate(x_all)
y_concat = np.concatenate(y_all)
u_hat_concat = np.concatenate(u_hat_all)

# on enlève le padding côté décodé : on revient à la longueur originale
u_hat_concat = u_hat_concat[:K_total]

# Reconstruction du message reçu
bits = u_hat_concat.copy()

# on garde un multiple de 8 bits
bits = bits[:len(bits) - (len(bits) % 8)]

octets = bits.reshape(-1, 8)
valeurs = octets.dot(1 << np.arange(7, -1, -1))

message_recu = bytes(valeurs.tolist()).decode("utf-8", errors="replace")
print("Message reçu : ", message_recu)
