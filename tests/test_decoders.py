import aff3ct
import streampu as spu
def test_abstract_decoder():
    decoder = aff3ct.decoder.Decoder(K=4, N=8)
    decoder.auto_reset = True
    assert decoder.K == 4
    assert decoder.N == 8
    assert decoder.auto_reset is True


def test_decoder_hiho():
    K = 4
    N = 8
    decoder_class = aff3ct.decoder.Decoder_HIHO(B=spu.int8)
    decoder = decoder_class(K, N)
    assert decoder.K == 4
    assert decoder.N == 8
    assert decoder.auto_reset is True
    assert hasattr(decoder, 'decode_hiho')


def test_decoder_siho():
    K = 4
    N = 8
    decoder_class = aff3ct.decoder.Decoder_SIHO(B=spu.int8, Q=spu.int8)
    decoder = decoder_class(K, N)
    assert decoder.K == 4
    assert decoder.N == 8
    assert decoder.auto_reset is True
    assert hasattr(decoder, 'decode_siho')
    assert hasattr(decoder, 'decode_hiho')    

def test_decoder_siso():
    K = 4
    N = 8
    decoder_class = aff3ct.decoder.Decoder_SISO(B=spu.int8, Q=spu.int8)
    decoder = decoder_class(K, N)
    assert decoder.K == 4
    assert decoder.N == 8
    assert decoder.auto_reset is True
    assert hasattr(decoder, 'decode_siso')
    assert hasattr(decoder, 'decode_siho')
    assert hasattr(decoder, 'decode_hiho')

if __name__ == "__main__":
    test_abstract_decoder()
    test_decoder_hiho()
    test_decoder_siho()
    test_decoder_siso()
