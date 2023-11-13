import random
from PIL import Image, ImageOps, ImageFilter
import io

async def blur_invert_image(image_content):
    # Open the image from the binary content
    image = Image.open(io.BytesIO(image_content))
    
    # Convert the image to grayscale
    color_inverted_image = ImageOps.equalize(image, mask = None)
    blurred_image = color_inverted_image.filter(ImageFilter.BLUR)
    # Rotate the grayscale image by 90 degrees
    rotation_angle = random.choice([90, 180, 270])
    
    # Rotate the grayscale image by the chosen angle
    rotated_image = blurred_image.rotate(rotation_angle)
    
    # Save the transformed image to a bytes-like object
    output_stream = io.BytesIO()
    rotated_image.save(output_stream, format="PNG")
    
    return output_stream.getvalue()

async def crop_image(image_content, percentage = 10):
    # Open the image from the binary content
    image = Image.open(io.BytesIO(image_content))
    
    # # Convert the image to grayscale
    # grayscale_image = ImageOps.grayscale(image)

    # Get the dimensions of the image
    width, height = image.size


    # Calculate the crop dimensions for the middle 10%
    crop_percentage = percentage / 100.0
    crop_left = width * (0.5 - crop_percentage / 2)
    crop_upper = height * (0.5 - crop_percentage / 2)
    crop_right = width * (0.5 + crop_percentage / 2)
    crop_lower = height * (0.5 + crop_percentage / 2)

    # Crop the image to the calculated dimensions
    cropped_image = image.crop((crop_left, crop_upper, crop_right, crop_lower))
    
    # Save the transformed image to a bytes-like object
    output_stream = io.BytesIO()
    cropped_image.save(output_stream, format="PNG")
    
    return output_stream.getvalue()


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
