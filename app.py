import os, io, requests
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
        if "product_url" not in request.form or "logo" not in request.files:
            return jsonify({"error": "Missing product_url or logo in form-data."}), 400

        product_url = request.form["product_url"]
        logo_file = request.files["logo"]

        # --- Download product image ---
        try:
            product_resp = requests.get(product_url, timeout=10)
            product_resp.raise_for_status()
        except Exception as e:
            return jsonify({"error": f"Failed to fetch product image: {str(e)}"}), 400

        product_bytes = product_resp.content
        logo_bytes = logo_file.read()

        # --- Create mockup overlay using PIL ---
        product_img = Image.open(io.BytesIO(product_bytes)).convert("RGBA")
        logo_img = Image.open(io.BytesIO(logo_bytes)).convert("RGBA")

        # Resize logo to ~1/3 of product width
        base_w = product_img.width // 3
        wpercent = (base_w / float(logo_img.width))
        hsize = int((float(logo_img.height) * float(wpercent)))
        logo_resized = logo_img.resize((base_w, hsize))

        # Center position
        px = (product_img.width - logo_resized.width)//2
        py = (product_img.height - logo_resized.height)//2

        mockup = product_img.copy()
        mockup.alpha_composite(logo_resized, (px, py))

        # Create mask for logo area
        mask = Image.new("L", product_img.size, 0)
        mask.paste(255, (px, py, px + logo_resized.width, py + logo_resized.height))

        # Convert to bytes
        mockup_bytes = io.BytesIO()
        mask_bytes = io.BytesIO()
        mockup.save(mockup_bytes, format="PNG")
        mask.save(mask_bytes, format="PNG")
        mockup_bytes.seek(0)
        mask_bytes.seek(0)

        # --- Prompt from your Colab ---
        prompt = (
            "Take the provided product photo and logo image.\n"
            "• Place the logo on the product surface in a realistic way (natural perspective, lighting, shadows).\n"
            "• Preserve the exact shapes and colors of the logo icon/text – do NOT redraw or modify the logo.\n"
            "• If the logo already has a background:\n"
            "    – keep it if it looks premium and balanced,\n"
            "    – otherwise remove it and make it clean/transparent.\n"
            "• Add subtle designer-style finishing (slight texture, gentle reflections, photographic realism)."
        )

        # --- Call OpenAI edit endpoint ---
        try:
            response = client.images.edit(
                model="gpt-image-1",
                image=mockup_bytes,
                mask=mask_bytes,
                prompt=prompt,
                size="1024x1024",  # standard quality
                quality="medium"    # medium quality for faster generation
            )
        except Exception as e:
            return jsonify({"error": f"OpenAI API call failed: {str(e)}"}), 502

        # --- Decode Output ---
        image_b64 = response.data[0].b64_json
        image_bytes = io.BytesIO(base64.b64decode(image_b64))

        return send_file(
            image_bytes,
            mimetype="image/png",
            as_attachment=False,
            download_name="mockup.png"
        )

    except Exception as e:
        return jsonify({"error": f"Server error: {str(e)}"}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
