def is_arabic_letter(char):
    return "\u0600" <= char <= "\u06FF"



print(is_arabic_letter("ض"))