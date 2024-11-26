from openai import OpenAI  # OpenAI Python library to make API calls
import requests  # used to download images
import os  # used to access filepaths
from PIL import Image  # used to print and edit images
from io import BytesIO
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key)

# Set a directory to save DALL-E images to
image_dir = "app/static/images"

# Create the directory if it doesn't yet exist
if not os.path.isdir(image_dir):
    os.mkdir(image_dir)

# Function to apply prompt engineering
def engineer_prompt(base_prompt):
    # General instructions for the prompts
    general_instructions = (
        "A clean, minimalistic image with no text, no labels, and no clutter. Focus on the subject only, with a plain background and simple details.",
        "No text, no captions, no labels, no signage, and no writing anywhere in the image."
    )
    # Combine the general instructions with the specific prompt
    return f"{general_instructions[0]} {base_prompt}{general_instructions[1]}"

# Function to generate images from a list of prompts
def generate_images_from_prompts(prompts):
    images = []

    for i, base_prompt in enumerate(prompts):
        # Engineer the prompt
        engineered_prompt = engineer_prompt(base_prompt)

        # Generate the image using the OpenAI API
        generation_response = client.images.generate(
            model="dall-e-3",
            prompt=engineered_prompt,
            n=1,
            size="1024x1024",
            response_format="url",
        )

        # Extract the image URL from the response
        generated_image_url = generation_response.data[0].url

        # Download the image
        img_response = requests.get(generated_image_url)
        img = Image.open(BytesIO(img_response.content))

        # Resize to 512x512
        img = img.resize((512, 512), Image.LANCZOS)

        # Define a unique name for each generated image
        generated_image_name = f"section_{i}.jpg"
        generated_image_filepath = os.path.join(image_dir, generated_image_name)

        # Save the resized image
        img.save(generated_image_filepath)
        
        images.append((engineered_prompt, generated_image_filepath))

    return images