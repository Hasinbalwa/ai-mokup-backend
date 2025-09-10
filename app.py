from flask import Flask, request, jsonify, send_file
from PIL import Image
import io, requests, os

app = Flask(__name__)

def overlay_logo(product_url, logo_file):
    # Download product image from Shopify URL
    response = requests.get(product_url, stream=True)
    if response.status_code != 200:
        raise Exception("Failed to fetch product image from URL")

    product_img = Image.open(io.BytesIO(response.content)).convert("RGBA")
    logo_img = Image.open(logo_file).convert("RGBA")

    pw, ph = product_img.size

    # Resize logo ~25% of product width
    target_w = max(40, int(pw * 0.25))
    logo_ratio = logo_img.height / logo_img.width
    logo_img = logo_img.resize((target_w, int(target_w * logo_ratio)), Image.LANCZOS)

    # Center position
    px = (pw - logo_img.width) // 2
    py = (ph - logo_img.height) // 2

    product_img.paste(logo_img, (px, py), logo_img)

    bio = io.BytesIO()
    product_img.save(bio, "PNG")
    bio.seek(0)
    return bio

@app.route("/")
def home():
    return jsonify({"status": "Backend is running"})

@app.route("/generate-mockup", methods=["POST"])
def generate_mockup():
    if "product_url" not in request.form or "logo" not in request.files:
        return jsonify({"error": "Missing 'product_url' or 'logo'"}), 400

    product_url = request.form["product_url"]
    logo_file = request.files["logo"]

    try:
        img_io = overlay_logo(product_url, logo_file)
        return send_file(img_io, mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
