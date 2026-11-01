import cv2
import easyocr
from ultralytics import YOLO

# Charger le modèle YOLO entraîné sur les plaques marocaines
model = YOLO("best.pt")  

# Charger l'image
# img = cv2.imread("maroc.jpg")

# # Détecter la plaque
# results = model(img)

# for result in results:
#     for box in result.boxes:
#         x1, y1, x2, y2 = map(int, box.xyxy[0])  # Coordonées de la boîte
#         plate_img = img[y1:y2, x1:x2]  # Extraire la plaque

#         # OCR sur l'image de la plaque
#         reader = easyocr.Reader(['en','ar'])  
#         text = reader.readtext(plate_img, detail=0)
#         print("Numéro détecté :", text)
        
# # -------------------------------------------------

# def clean_plate_number(plate_text):
#     plate_text = plate_text.replace("O", "0")  # Remplace 'O' par '0'
#     plate_text = plate_text.replace("I", "1")  # Remplace 'I' par '1'
#     plate_text = plate_text.replace("S", "5")  # Corrige 'S' en '5'
#     return plate_text

# text = reader.readtext(plate_img, detail=0)
# corrected_text = [clean_plate_number(t) for t in text]
# print("Numéro corrigé :", corrected_text)


# ----------
# Dictionnaire de conversion arabe → latin
arabic_to_latin = {
    "أ": "A", "ب": "B", "ج": "J", "د": "D",
    "ه": "H", "و": "W", "ز": "Z", "ح": "H",
    "ط": "T", "ي": "Y", "ك": "K", "ل": "L",
    "م": "M", "ن": "N", "س": "S", "ع": "3",
    "ف": "F", "ق": "Q", "ر": "R", "ص": "S",
    "ت": "T", "ش": "CH", "ث": "TH", "ظ": "Z",
    "خ": "KH", "غ": "GH", "ض": "D", "ذ": "DH"
}

def convert_arabic_to_latin(text):
    return "".join(arabic_to_latin.get(char, char) for char in text)

# Appliquer EasyOCR
reader = easyocr.Reader(['ar', 'en'])  # Arabe et anglais
text = reader.readtext('maroc.jpg', detail=0)
converted_text = [convert_arabic_to_latin(t) for t in text]

print("Numéro détecté l:", converted_text)

