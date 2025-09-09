from flask import Flask, request, jsonify, send_file, abort
from PIL import Image
import io, os

app = Flask(__name__)

# sample product list (maps product key -> static image path)
PRODUCTS = {
    "cup": "static/products/cup.png",
    "box": "static/products/box.png",
    "bag": "static/products/bag.png"
}

def overlay_logo(product_path, logo_file):
    product_img = Image.open(product_path).convert("RGBA")
    logo_img = Image.open(logo_file).convert("RGBA")

    pw, ph = product_img.size

    # scale logo to be ~25% of product width (adjustable)
    target_w = max(40, int(pw * 0.25))
    logo_ratio = logo_img.height / logo_img.width
    logo_img = logo_img.resize((target_w, int(target_w * logo_ratio)), Image.LANCZOS)

    # position: center (you can change logic to bottom or custom)
    px = (pw - logo_img.width) // 2
    py = (ph - logo_img.height) // 2

    # Paste with alpha mask
    product_img.paste(logo_img, (px, py), logo_img)

    bio = io.BytesIO()
    product_img.save(bio, "PNG")
    bio.seek(0)
    return bio

@app.route("/generate-mockup", methods=["POST"])
def generate_mockup():
    """
    Expects form-data:
      - product : product key (cup, box, bag)
      - logo    : uploaded file (image)
    Returns: PNG image (mockup) or JSON error.
    """
    if "product" not in request.form or "logo" not in request.files:
        return jsonify({"error": "Missing 'product' or 'logo'"}), 400

    product_key = request.form["product"]
    logo_file = request.files["logo"]

    if product_key not in PRODUCTS:
        return jsonify({"error": "Unknown product key."}), 400

    product_path = PRODUCTS[product_key]
    if not os.path.exists(product_path):
        return jsonify({"error": "Product image not found on server."}), 500

    try:
        img_io = overlay_logo(product_path, logo_file)
        return send_file(img_io, mimetype="image/png")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/products", methods=["GET"])
def list_products():
    return jsonify(list(PRODUCTS.keys()))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))