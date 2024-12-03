from fuzzywuzzy import process


def find_closest_name(query, names_list):
    # This will return the closest match in the list along with the similarity score
    if 'wukong' in query.lower():
        return 'MonkeyKing', 100  # Assuming a perfect match score of 100
    closest_match = process.extractOne(query, names_list)
    return closest_match