import easyocr

reader = easyocr.Reader(['ar'], gpu=False)  # Langue arabe (pour le Maroc)
text = reader.readtext('plate_image.jpg', detail=0)
print("Numéro détecté :", text)



# ------------
import re

def is_valid_plate(text):
    pattern = r'^\d{1,5}\s?[A-Z]{1,3}\s?\d{1,2}$'  # Format général des plaques marocaines
    return bool(re.match(pattern, text))

plate = "12345 ABC 67"
if is_valid_plate(plate):
    print("Plaque valide :", plate)
else:
    print("Erreur de reconnaissance")
    
    
    
    #   base de données
    
import sqlite3

def check_plate_in_db(plate):
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM authorized_vehicles WHERE plate_number = ?", (plate,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

plate_detected = "12345 ABC 67"
if check_plate_in_db(plate_detected):
    print("Véhicule autorisé ✅")
else:
    print("Véhicule interdit ❌")

