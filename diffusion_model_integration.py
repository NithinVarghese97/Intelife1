import requests
from PIL import Image
from io import BytesIO

# Function to generate images from a list of hardcoded prompts
def generate_images_from_prompts(dall_e_api_key):
    # Step 1: Define hardcoded prompts
    prompts = [
        "A futuristic cityscape at sunset",
        "A lush green forest with a waterfall",
        "A bustling space station interior",
        "An ancient castle surrounded by mist",
        # Add more prompts as needed
    ]

    # Step 2: Set up headers for DALL-E API request
    headers = {
        "Authorization": f"Bearer {dall_e_api_key}",
        "Content-Type": "application/json",
    }
    images = []

    # Step 3: Loop through each prompt and request image generation
    for i, prompt in enumerate(prompts):
        print(f"Generating image for prompt {i + 1}: {prompt}")

        # DALL-E API call
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json={"prompt": prompt, "n": 1, "size": "512x512"}
        )
        
        if response.status_code == 200:
            image_url = response.json()["data"][0]["url"]
            images.append((prompt, image_url))
            print(f"Image generated for prompt {i + 1}")

            # Download and display the image
            img_response = requests.get(image_url)
            img = Image.open(BytesIO(img_response.content))
            
            # Resize to 512x512 in case the API returns a different size
            img = img.resize((512, 512), Image.LANCZOS)
            
            img.show(title=f"Prompt {i + 1}")
            
            # Optionally save the image locally
            img.save(f"image_prompt_{i+1}.png")
            print(f"Image saved as image_prompt_{i+1}.png")
        else:
            # Print error details for troubleshooting
            error_message = response.json().get("error", {}).get("message", "No additional error information available.")
            print(f"Error generating image for prompt {i + 1}: {response.status_code} - {error_message}")

    return images

# Example usage
generated_images = generate_images_from_prompts(API_KEY)

# Each entry in generated_images will contain the section text and the corresponding image URL


import os
import glob

def delete_generated_images():
    # Use glob to find all images matching the pattern
    image_files = glob.glob("image_prompt_*.png")

    for image_file in image_files:
        try:
            os.remove(image_file)
            print(f"Deleted {image_file}")
        except Exception as e:
            print(f"Error deleting {image_file}: {e}")

# Call this function when you want to delete the images
delete_generated_images()