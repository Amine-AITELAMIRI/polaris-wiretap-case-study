from aff3ct import factory as fct
import streampu as spu


factory = fct.Decoder_polar()

factory.K = 4
factory.N_cw = 8
factory.type = 'SC'
factory.implem = 'NAIVE'
factory.simd_strategy = ''
factory.B = spu.int64
factory.Q = spu.float64

decoder = factory.build([1,1,1,0,1,0,0,0])
print(decoder)

y = spu.float64([1.1, -2.1, 1.1, 3.1, -1.1, 1.1, -1.1, 1.1])
out = decoder.decode_siho(y)[1]

print(out)

polar_decoder_args = {
    'K': 4,
    'N': 8,
    'frozen_bits': [1,1,1,0,1,0,0,0],
    'type': 'SCL',
    'L': 1,
    'implem': 'NAIVE',
    'B': spu.int64,
    'Q': spu.float64
}
factory2 = fct.Decoder_polar()
factory2.K = polar_decoder_args['K']
factory2.N_cw = polar_decoder_args['N']
factory2.type = polar_decoder_args['type']
factory2.L = polar_decoder_args['L']
factory2.implem = polar_decoder_args['implem']
factory2.B = polar_decoder_args['B']
factory2.Q = polar_decoder_args['Q']

decoder2 = factory2.build(polar_decoder_args['frozen_bits'])

# decoder2 = fct.Decoder_polar(**polar_decoder_args) # Decoder_polar does not accept kwargs
print(decoder2)
out2 = decoder2.decode_siho(y)[1]
print(out2)