from ultralytics import YOLO

# Charger le modèle entraîné
model = YOLO('best.pt')  # Remplace 'exp' par ton dossier d'expérience

# Tester sur une image
results = model('plate.jpg')

# Afficher les résultats
results = results[0]
results.show()

# print( type(results))

# Sauvegarder les résultats (image annotée)
results.save(save_dir='D:\cours licence')
