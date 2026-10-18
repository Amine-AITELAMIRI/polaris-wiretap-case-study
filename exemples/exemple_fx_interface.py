import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fonctions.fx_interface import *

#Exemple d'utilisation des fonctions :

# Pour un message TEXTE
bonjour = "bonjour"
print(bonjour)

bonjour=text_to_bits(bonjour)
print(bonjour)
bonjour=encapsuler_type(bonjour,"TEXTE")
print(bonjour)
# On stoque dans le json

# On lit le json
bonjour=bits_to_numpy(bonjour)
print(bonjour)

# On transmet

bonjour=numpy_to_bits(bonjour)
print(bonjour)
# On stoque dans le json

# On lit le json
type,bonjour=decapsuler_type(bonjour)
print(type,bonjour)
bonjour=bits_to_text(bonjour) # Grace aut type on sais que cest un texte
print(bonjour)


# Pour un message BINAIRE
bonjour = "01100010011011110110111001101010011011110111010101110010"
print(bonjour)
bonjour=encapsuler_type(bonjour,"BINAIRE")
print(bonjour)
# On stoque dans le json

# On lit le json
bonjour=bits_to_numpy(bonjour)
print(bonjour)

# On transmet

bonjour=numpy_to_bits(bonjour)
# On stoque dans le json

# On lit le json
type,bonjour=decapsuler_type(bonjour)
print(type,bonjour)

print(bonjour) # On sais que c'est directement du binaire avec type

# Pour un message IMAGE
from PIL import ImageShow
image = Image.open(IMG)
ImageShow.show(image)

image,dim = image_to_numpy(IMG)
print(image)
print(dim)
image = numpy_to_bits(image)
print(image)
image=encapsuler_type(image,"IMAGE")
print(image)
# On stoque dans le json

# On lit le json
type,image=decapsuler_type(image)
print(type,image)
image = bits_to_numpy(image)
print(image)

image = numpy_to_image(image,dim)
ImageShow.show(image)
