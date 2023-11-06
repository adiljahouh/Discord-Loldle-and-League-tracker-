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
