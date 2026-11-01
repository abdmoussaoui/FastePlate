import cv2
import numpy as np
import matplotlib.pyplot as plt
def segment_characters(plate_image):
                # Charger l'image en niveau de gris
                # Si l'image est en couleur, convertir en niveaux de gris
                if len(plate_image.shape) == 3:
                    img = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
                else:
                    img = plate_image

                # 1. Binarisation (noir/blanc)
                _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

                h, w = thresh.shape

                # Stocker les coordonnées des segments
                segments = []
                start = None

                # 2. Parcours colonne par colonne
                for x in range(w):
                    col = thresh[:, x]
                    black_pixels = np.sum(col == 255)  # pixels noirs (inversé)

                    if black_pixels > 5:  # seuil à ajuster
                        if start is None:
                            start = x
                    else:
                        if start is not None:
                            end = x
                            segments.append((start, end))
                            start = None

                # Si le dernier caractère arrive jusqu'à la fin
                if start is not None:
                    segments.append((start, w))

                characters = []
                i = 0

                # 3. Découper chaque segment (crop)
                for (x_start, x_end) in segments:
                    char_img = thresh[:, x_start:x_end]

                    # Nettoyage (enlever trop petites zones)
                    if char_img.shape[1] > 10:  # éviter le bruit
                        cv2.imwrite(f"char_{i}.png", char_img)
                        characters.append(char_img)
                        i += 1

                print(f"{len(characters)} caractères détectés.")
                
                # akm : savoir es ce que chaque chifre s affiche ou non mais c est pas le cas 
                plt.imshow(characters[0], cmap='gray')
                plt.show()
                return characters


# seegmentation histograme :
import cv2
import numpy as np

def segment_characters_histogram(plate_image):
    # Charger l'image en niveau de gris
    # Si l'image est en couleur, convertir en niveaux de gris
    if len(plate_image.shape) == 3:
        img = cv2.cvtColor(plate_image, cv2.COLOR_BGR2GRAY)
    else:
        img = plate_image

    # 2. Binarisation de l’image (inversion : caractères en blanc)
    _, thresh = cv2.threshold(img, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    h, w = thresh.shape

    # 3. Projection verticale (histogramme)
    hist = np.sum(thresh == 255, axis=0)

    # 4. Segmentation via histogram peaks
    segments = []
    start = None
    threshold = 5  # à ajuster selon tes images

    for x in range(w):
        if hist[x] > threshold:
            if start is None:
                start = x
        else:
            if start is not None:
                end = x
                segments.append((start, end))
                start = None

    if start is not None:
        segments.append((start, w))

    # 5. Découper les caractères
    characters = []
    i = 0

    for (x_start, x_end) in segments:
        # Crop vertical (toute la hauteur)
        char_img = thresh[:, x_start:x_end]

        # Éliminer les très petites zones (bruit)
        if char_img.shape[1] > 8:
            char_path = f"char_{i}.png"
            cv2.imwrite(char_path, char_img)
            characters.append(char_path)
            i += 1

    print(f"Segmentation terminée. {len(characters)} caractères détectés.")
    return characters
