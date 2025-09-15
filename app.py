import os, io, base64, requests
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from openai import OpenAI
from PIL import Image

app = Flask(__name__)
CORS(app)

# Load OpenAI client
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise RuntimeError("❌ Environment variable OPENAI_API_KEY is missing.")
client = OpenAI(api_key=api_key)

@app.route("/")
def home():
    return jsonify({"status": "Backend is running"})

@app.route("/generate-mockup", methods=["POST"])
def generate_mockup():
    try:
        # --- Validate Inputs ---
        if "product_url" not in request.form or "logo" not in request.files:
            return jsonify({"error": "Missing product_url or logo in form-data."}), 400

        product_url = request.form["product_url"]
        logo_file   = request.files["logo"]

        # --- Download Product Image ---
        try:
            product_resp = requests.get(product_url, timeout=10)
            product_resp.raise_for_status()
        except Exception as e:
            return jsonify({"error": f"Failed to fetch product image: {str(e)}"}), 400

        product_bytes = product_resp.content
        logo_bytes = logo_file.read()

        # Quick sanity check (are these valid images?)
        try:
            Image.open(io.BytesIO(product_bytes))
        except Exception:
            return jsonify({"error": "Product URL is not a valid image."}), 400
        try:
            Image.open(io.BytesIO(logo_bytes))
        except Exception:
            return jsonify({"error": "Uploaded logo is not a valid image."}), 400

        # --- Prepare base64 for OpenAI ---
        product_b64 = base64.b64encode(product_bytes).decode("utf-8")
        logo_b64    = base64.b64encode(logo_bytes).decode("utf-8")

        # --- Build Prompt ---
        prompt = (
            "Create a high-resolution product mockup. "
            "Use the first image as the product background. "
            "Blend the second image as a brand logo on the product surface. "
            "Ensure natural lighting, realistic shadows, and a clean studio style. "
            "Do not add any extra text or watermark."
        )

        # --- Call OpenAI API ---
        try:
            response = client.images.generate(
                model="gpt-image-1",
                prompt=prompt,
                size="1024x1024",
                images=[
                    {"image": product_b64},
                    {"image": logo_b64}
                ]
            )
        except Exception as e:
            return jsonify({"error": f"OpenAI API call failed: {str(e)}"}), 502

        # --- Decode Output ---
        try:
            image_b64 = response.data[0].b64_json
            image_bytes = base64.b64decode(image_b64)
        except Exception as e:
            return jsonify({"error": f"Failed to decode API response: {str(e)}"}), 500

        return send_file(
            io.BytesIO(image_bytes),
            mimetype="image/png",
            as_attachment=False,
            download_name="mockup.png"
        )

    except Exception as e:
        # Catch any unexpected server-side issue
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
