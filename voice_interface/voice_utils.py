from fuzzywuzzy import process

def string_similarity(string, options, similarity_treshold=80):
    best_match = process.extractOne(string, options)
    if best_match is None:
      return None

    text, probability = best_match
    #print(f"Znaleziono napis: {text} z prawdopodobienstwem {probability} na podstawie słowa {string}")

    if probability >= similarity_treshold:
      return text

    return None