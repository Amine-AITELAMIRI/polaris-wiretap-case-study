from .fx_include import *
from PIL import Image

def load_css(file_name):
    """Lit un fichier CSS et renvoie la balise HTML correspondante."""
    if os.path.exists(file_name):
        with open(file_name, "r") as f:
            return f'<style>{f.read()}</style>'
    else:
        return ""

def determiner_type_message(message_str, uploaded_file):
    """
    Détermine le type de message selon les règles :
    1. Si un fichier est chargé -> IMAGE
    2. Si le texte ne contient que des 0 et 1 -> BINAIRE
    3. Sinon -> TEXTE
    """
    if uploaded_file is not None:
        return "IMAGE"
    
    # Nettoyage des espaces/retours à la ligne pour le test binaire
    clean_msg = message_str.strip().replace(" ", "").replace("\n", "")
    
    if clean_msg and all(c in '01' for c in clean_msg):
        return "BINAIRE"
    
    return "TEXTE"

def encapsuler_type(bits_str, type_msg):
    """
    Ajoute un header de 8 bits au début pour indiquer le type.
    """
    # Création du header de 8 bits
    code_type = TYPES.get(type_msg, 0) # 0 si inconnu
    header_str = format(code_type, '08b')

    # Retourne [Header Type][Données]
    return header_str+bits_str

def decapsuler_type(bits_str):
    """
    Renvoit le code type du message et le message.
    """
    header_str = bits_str[:8]

    code_type = int(header_str, 2)
    type = CODE_TYPES.get(code_type,"INCONNU")

    # Retourne [Header Type][Données]
    return type, bits_str[8:]

def bits_to_numpy(bit_str):
    """Convertit la string du JSON en vecteur NumPy pour le calcul."""
    return np.array(list(bit_str), dtype=np.int8)

def numpy_to_bits(bit_np):
    """Convertit le vecteur NumPy en string pour le stockage JSON."""
    return "".join(bit_np.astype(str))

def text_to_bits(text):
    """Transforme une chaîne de caractères en une chaîne de bits."""
    return ''.join(format(ord(c), '08b') for c in text)

def bits_to_text(bit_str):
    """Transforme une chaîne de bits en texte."""
    # On découpe par blocs de 8
    chars = [chr(int(bit_str[i:i+8], 2)) for i in range(0, len(bit_str), 8)]
    return ''.join(chars)

def image_to_numpy(image):
    """Transforme une image PIL en array numpy. 
    + dim = (hauteur, largeur de l'image, couleur (noir/blanc ou rgb)"""
    img = Image.open(image)
    array = np.asarray(img)
    h, w ,c = array.shape
    dim = [h,w,c]

    # Pixels
    pixel_bits = np.unpackbits(array).astype(np.int8)

    return pixel_bits,dim

def numpy_to_image(bits_np,dim):
    """Transforme un array numpy en une image PIL a ouvrir avec Image.open() """
    
    uint8_arr = np.packbits(bits_np).reshape(dim)

    return Image.fromarray(uint8_arr)

def teb(bits_envoye,bits_recus):
    N=len(bits_envoye)
    d=np.abs(bits_envoye-bits_recus)

    return (np.sum(d)*100)/N
