from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
import io, base64, os, requests
from PIL import Image

app = Flask(__name__)
CORS(app)

# Initialize OpenAI client with API key from environment variable
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

@app.route("/")
def home():
    return jsonify({"status": "Backend is running"})

@app.route("/generate-mockup", methods=["POST"])
def generate_mockup():
    try:
        # 1. Validate inputs
        if "product_url" not in request.form or "logo" not in request.files:
            return jsonify({"error": "Missing product_url or logo"}), 400

        product_url = request.form["product_url"]
        logo_file = request.files["logo"]

        # 2. Download the product base image
        product_img_data = requests.get(product_url).content
        product_img = Image.open(io.BytesIO(product_img_data)).convert("RGBA")

        # 3. Prepare the mask (full transparent mask means AI will edit whole image)
        #    For a precise mask you'd normally upload a black/white mask.
        #    Here we let AI decide where to place the logo.
        mask_img = Image.new("RGBA", product_img.size, (255,255,255,255))
        mask_bytes = io.BytesIO()
        mask_img.save(mask_bytes, format="PNG")
        mask_bytes.seek(0)

        # 4. Call OpenAI Image Edit (DALL·E-2)
        #    Prompt describes how to blend the uploaded logo realistically.
        prompt = (
            "Place the provided brand logo centered on the product surface in a clean, "
            "studio-style mockup with natural lighting, correct perspective, and realistic blending. "
            "Do not add any extra text or watermark."
        )

        response = client.images.edit(
            model="dall-e-2",
            image=product_img_data,
            mask=mask_bytes.read(),
            prompt=prompt,
            additional_images=[logo_file.read()],   # <-- send uploaded logo
            size="1024x1024"
        )

        # 5. Convert the output back to bytes
        image_b64 = response.data[0].b64_json
        image_bytes = base64.b64decode(image_b64)

        # 6. Return as downloadable PNG
        return send_file(io.BytesIO(image_bytes),
                         mimetype="image/png",
                         as_attachment=False,
                         download_name="mockup.png")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
