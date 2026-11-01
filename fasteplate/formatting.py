"""Conservative Unicode handling; never infer a missing letter or regional code."""
import unicodedata

def normalize(text):
    text = unicodedata.normalize('NFKC', text)
    chars = []
    for char in text:
        if unicodedata.category(char) == 'Cf' or char == '\u0640':
            continue
        if unicodedata.category(char) == 'Nd':
            char = str(unicodedata.digit(char))
        chars.append(char)
    return ' '.join(''.join(chars).split())

def physical_order(tokens):
    # Keep the OCR's internal token string. Sort boxes by rows then left-to-right.
    # Arabic reading direction must never reverse the entire registration.
    rows = []
    for token in sorted(tokens, key=lambda t: min(p[1] for p in t.box)):
        cy = sum(p[1] for p in token.box) / 4
        h = max(p[1] for p in token.box) - min(p[1] for p in token.box)
        for row in rows:
            if abs(cy-row[0]) <= max(5, min(h,row[1])*.6):
                row[2].append(token)
                break
        else:
            rows.append([cy,h,[token]])
    return '\n'.join(' '.join(t.text for t in sorted(row[2],key=lambda t:min(p[0] for p in t.box))) for row in rows)

def review_warning(text, confidence):
    if not text.strip():
        return 'Aucun texte lu. Essayer un autre traitement ou corriger manuellement.'
    if confidence is None or confidence < .65:
        return 'Lecture incertaine : vérifier les chiffres et la lettre arabe.'
    return 'Lecture automatique à vérifier ; format non certifié.'
