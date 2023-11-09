import random
from PIL import Image

def process_image(image_path):
    # Open the image file
    img = Image.open(image_path)
    # Convert the image to grayscale
    img = img.convert('L')
    # Generate a random angle between 0 and 360
    angle = random.choice([90, 180, 270, 360])
    # Rotate the image
    img = img.rotate(angle)  # Rotate by a random angle
    # Save the image
    img.save('/assets/loldle.png')


def compare_dicts_and_create_text(dict1, dict2)-> tuple:
    cross_emoji = "❌"
    check_emoji = "✅"
    up_arrow_emoji = "⬆️"
    down_arrow_emoji = "⬇️"
    result_text = ""
    
    # Initialize a flag to track if all values match
    all_values_match = True

    # Compare the dictionaries
    for key in dict1:
        if key in dict2:
            if isinstance(dict1[key], list) and isinstance(dict2[key], list):
                # Both values are lists, compare items
                matching_items = [f"{check_emoji} {item}" for item in dict1[key] if item in dict2[key]]
                non_matching_items = [f"{cross_emoji} {item}" for item in dict1[key] if item not in dict2[key]]
                if non_matching_items:
                    all_values_match = False  # Set flag to False if there are non-matching items
                items_str = ' '.join(matching_items + non_matching_items)
                result_text += f"{key}: {items_str}\n"
            elif dict1[key] == dict2[key]:
                # Values match
                result_text += f"{key}: {check_emoji} {dict1[key]}\n"
            elif key == "ReleaseDate":
                # Values don't match and key is releaseDate
                if float(dict1[key]) > float(dict2[key]):
                    result_text += f"{key}: {down_arrow_emoji} {dict1[key]}\n"
                else:
                    result_text += f"{key}: {up_arrow_emoji} {dict1[key]}\n"
                all_values_match = False
            else:
                # Values don't match
                result_text += f"{key}: {cross_emoji} {dict1[key]}\n"
                all_values_match = False
        else:
            # Key doesn't exist in the second dictionary
            result_text += f"{key}: {cross_emoji} {dict1[key]} -> Key not found\n"
            all_values_match = False

    return (all_values_match, result_text.strip())
