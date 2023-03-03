from flask import Flask, jsonify, request
import requests
from PIL import Image
from io import BytesIO
import numpy as np
import cv2

app = Flask(__name__)

# Set the OpenAI API endpoint and your API key
API_ENDPOINT = "https://api.openai.com/v1/images/generations"
API_KEY = "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"


@app.route('/generate-image', methods=['POST'])
def generate_image():
    # Get the user's text input from the request
    user_input = request.json.get('text')

    # Set the text prompt and model parameters
    prompt = f"3D model of a equirectangular panorama. {user_input}"
    model = "image-alpha-001"
    size = "1024x1024"

    # Send the API request to generate the image
    response = requests.post(
        API_ENDPOINT,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}",
        },
        json={
            "model": model,
            "prompt": prompt,
            "num_images": 1,
            "size": size,
            "response_format": "url",
        },
    )

    # Check if the request was successful
    if response.status_code == 200:
        # Get the URL of the generated image from the response
        image_url = response.json()["data"][0]["url"]

        # Download the image using Pillow and convert to a numpy array
        image_data = requests.get(image_url).content
        image = Image.open(BytesIO(image_data))
        image_array = np.array(image)

        # Set the parameters for inpainting
        window_size = 15
        search_range = 30

        # Inpaint the left side of the image
        left = image_array[:, :512, :]
        left_gray = cv2.cvtColor(left, cv2.COLOR_RGB2GRAY)
        left_mask = np.zeros(left_gray.shape, dtype=np.uint8)
        left_mask[left_gray == 0] = 255
        left_inpaint = cv2.inpaint(left, left_mask, window_size, cv2.INPAINT_TELEA)

        # Inpaint the right side of the image
        right = image_array[:, 512:, :]
        right_gray = cv2.cvtColor(right, cv2.COLOR_RGB2GRAY)
        right_mask = np.zeros(right_gray.shape, dtype=np.uint8)
        right_mask[right_gray == 0] = 255
        right_inpaint = cv2.inpaint(right, right_mask, window_size, cv2.INPAINT_TELEA)

        # Combine the left and right sides of the image
        combined_inpaint = np.concatenate((left_inpaint, right_inpaint), axis=1)

        # Convert the combined image to a Pillow Image object
        combined_image = Image.fromarray(combined_inpaint)

        # Convert the Pillow Image object to bytes
        img_bytes = BytesIO()
        combined_image.save(img_bytes, format='PNG')
        img_bytes = img_bytes.getvalue()
        # Display the combined image using Pillow
        combined_image = Image.fromarray(combined_inpaint)
        combined_image.show()
        temp = user_input.replace(" ","")
        # Set the filename based on the user input
        filename = f"combined_image-{temp}.png"

        # Save the combined image to a file using Pillow
        combined_image.save(filename)

               
        # Return the combined image as a response
        return jsonify({'image': str(img_bytes)})

    else:
        # Return the error message if the request failed
        return jsonify({'error': response.text})

    res = requests.get(f"http://localhost:3000/upload?file={filename}")
    if res.status_code == 200:
        return res.text

if __name__ == '__main__':
    app.run(debug=True)
