import aff3ct
import streampu as spu
u = spu.int8([1, 0, 1, 0])
frozen_bits = [1, 1, 1, 0, 1, 0, 0, 0]

# Encoding
x = aff3ct.polar.encode(u, frozen_bits)
print("Encoded codeword:", x)
print("Encoded codeword dtype:", x.dtype)
# Decoding
decodage_args = {
    'decoder_type': 'SCL',
    'L': 2,
    'implem': 'NAIVE'
}
llrs = [0.9, -1.2, 2.5, -0.7, -1.0, 0.5, -0.3, 0.8]
cwd, u_hat = aff3ct.polar.decode_siho(llrs, frozen_bits, **decodage_args)
print(u_hat)
