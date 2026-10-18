from aff3ct import factory as fct
from aff3ct import sparse_matrix as spm

import streampu as spu
help(fct.Decoder_LDPC.implem)
factory = fct.Decoder_LDPC()
factory.K = 4
factory.N_cw = 7
factory.type = 'BP_FLOODING'
factory.implem = 'SPA'
factory.max_iterations = 10
factory.B = spu.int64
factory.Q = spu.float64

H = spm.array(3, 7)
H.add_connection(0, 0)
H.add_connection(0, 3)
H.add_connection(0, 4)
H.add_connection(0, 6)
H.add_connection(1, 1)
H.add_connection(1, 3)
H.add_connection(1, 5)
H.add_connection(1, 6)
H.add_connection(2, 2)
H.add_connection(2, 4)
H.add_connection(2, 5)
H.add_connection(2, 6)

info_bits_pos = [0, 1, 2] # Assuming these are info bits for this custom matrix

# Configure the factory and build
decoder = factory.build(H, info_bits_pos)
print(decoder)
decoded = decoder.decode_siho([0.9, -1.1, 0.95, -0.8, 1.2, -0.5, 0.3])
print(decoded)
