import os
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from io import BytesIO
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
OPENAI_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_KEY)

app = Flask(__name__)
CORS(app)

@app.route("/generate-mockup", methods=["POST"])
def generate_mockup():
    try:
        product_file = request.files.get("product")
        logo_file    = request.files.get("logo")
        if not product_file or not logo_file:
            return jsonify({"error": "Missing product or logo file"}), 400

        # Pillow composition
        product = Image.open(product_file.stream).convert("RGBA")
        logo    = Image.open(logo_file.stream).convert("RGBA")
        logo_width  = int(product.width * 0.35)
        logo_height = int(logo.height * (logo_width / logo.width))
        logo = logo.resize((logo_width, logo_height))
        x = (product.width  - logo_width) // 2
        y = (product.height - logo_height) // 2

        composite = product.copy()
        composite.alpha_composite(logo, dest=(x, y))

        rough_bytes = BytesIO()
        composite.save(rough_bytes, format="PNG")
        rough_bytes.seek(0)

        prompt = (
            "Create a high-quality, photorealistic product mockup of a paper bag using the provided image. "
            "Use the provided brand logo already placed in the mockup and ensure it is centered on the bag surface. "
            "Produce a clean studio-style mockup with natural lighting, correct perspective, crisp edges, and the logo clearly visible and correctly colored. "
            "No watermarks or UI elements—output a single realistic image."
        )

        response = client.images.edit(
            model="gpt-image-1",
            image=("rough.png", rough_bytes, "image/png"),
            prompt=prompt,
            size="1024x1024"
        )

        image_b64 = response.data[0].b64_json
        return jsonify({"status": "ok", "image_b64": image_b64})

    except Exception as e:
        print("❌ Backend error:", e)
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
