from openai import OpenAI  # OpenAI Python library to make API calls
import requests  # used to download images
import os  # used to access filepaths
from PIL import Image  # used to print and edit images
from io import BytesIO

# Initialize OpenAI client
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY", "<Your Dall E API Key>"))

# Set a directory to save DALL-E images to
image_dir_name = "images"
image_dir = os.path.join(os.curdir, image_dir_name)

# Create the directory if it doesn't yet exist
if not os.path.isdir(image_dir):
    os.mkdir(image_dir)

# Print the directory to save to
print(f"{image_dir=}")

# Function to generate images from a list of prompts
def generate_images_from_prompts(prompts):
    images = []

    for i, prompt in enumerate(prompts):
        print(f"Generating image for prompt {i + 1}: {prompt}")

        # Call the OpenAI API with a supported size
        generation_response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            n=1,
            size="1024x1024",  # Ensure this size is supported
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
        generated_image_name = f"generated_image_{i+1}.png"
        generated_image_filepath = os.path.join(image_dir, generated_image_name)

        # Save the resized image
        img.save(generated_image_filepath)
        
        images.append((prompt, generated_image_filepath))
        print(f"Image saved as {generated_image_filepath}")

    return images

# Example usage with a list of hardcoded prompts
prompts = [
    "A futuristic cityscape at sunset",
    "A lush green forest with a waterfall",
    "A bustling space station interior",
    "An ancient castle surrounded by mist"
]
generated_images = generate_images_from_prompts(prompts)

# Display and delete the generated images
for prompt, image_path in generated_images:
    print(f"Prompt: {prompt}")
    img = Image.open(image_path)
    img.show()  # Opens the image in the default image viewer

for prompt, image_path in generated_images:
    # Delete the image file after displaying it
    os.remove(image_path)
    print(f"Deleted {image_path}")