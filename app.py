# ============================================
# MUSEORA — AI VISUAL DISCOVERY BACKEND
# ============================================

import os
import uuid

import torch
import torchvision
import numpy as np

from PIL import Image
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename

from torchvision.models import resnet18, ResNet18_Weights
from sklearn.metrics.pairwise import cosine_similarity

from fusion import (
    remove_background,
    create_composition,
    FUSION_FOLDER
)


# ============================================
# 1. INITIALIZE FLASK
# ============================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = Flask(
    __name__,
    static_folder=None
)

CORS(app)


# ============================================
# 2. CONFIGURATION
# ============================================

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
IMAGE_FOLDER = os.path.join(BASE_DIR, "images")
MODEL_FOLDER = os.path.join(BASE_DIR, "model")

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

MAX_FILE_SIZE = 10 * 1024 * 1024

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FUSION_FOLDER, exist_ok=True)

print("APP BASE DIR:", BASE_DIR)
print("FUSION FOLDER:", FUSION_FOLDER)
print("FUSION FOLDER EXISTS:", os.path.exists(FUSION_FOLDER))


# ============================================
# 3. LOAD SAVED SEARCH DATA
# ============================================

DATA_PATH = os.path.join(
    MODEL_FOLDER,
    "museora_search_data.npz"
)

if not os.path.isfile(DATA_PATH):
    raise FileNotFoundError(
        f"MUSEORA search data not found: {DATA_PATH}"
    )

search_data = np.load(DATA_PATH)

IMAGE_FEATURES = search_data["features"]
IMAGE_LABELS = search_data["labels"]

if IMAGE_FEATURES.shape != (500, 512):
    raise ValueError(
        f"Unexpected feature shape: {IMAGE_FEATURES.shape}"
    )

if len(IMAGE_LABELS) != len(IMAGE_FEATURES):
    raise ValueError(
        "The number of labels does not match the number of features."
    )

print("MUSEORA search data loaded!")
print("Feature matrix:", IMAGE_FEATURES.shape)
print("Label array:", IMAGE_LABELS.shape)


# ============================================
# 4. LOAD RESNET18 FEATURE EXTRACTOR
# ============================================

device = torch.device(
    "cuda" if torch.cuda.is_available() else "cpu"
)

weights = ResNet18_Weights.DEFAULT

model = resnet18(weights=weights)

model.fc = torch.nn.Identity()

model = model.to(device)
model.eval()

preprocess = weights.transforms()

print("ResNet18 feature extractor loaded!")
print("Device:", device)


# ============================================
# 5. HELPER FUNCTIONS
# ============================================

def allowed_file(filename):

    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def extract_image_features(image):

    image = image.convert("RGB")

    image_tensor = preprocess(image).unsqueeze(0)
    image_tensor = image_tensor.to(device)

    with torch.no_grad():
        features = model(image_tensor)

    return features.cpu().numpy()


# ============================================
# 6. HOME PAGE
# ============================================

@app.route("/")
def home():

    return send_from_directory(
        BASE_DIR,
        "index.html"
    )


# ============================================
# 7. SERVE CSS AND JAVASCRIPT
# ============================================

@app.route("/<path:filename>")
def serve_frontend(filename):

    if filename in {"style.css", "script.js"}:

        return send_from_directory(
            BASE_DIR,
            filename
        )

    return jsonify({
        "error": "File not found"
    }), 404


# ============================================
# 8. SERVE DATASET IMAGES
# ============================================

@app.route("/images/<path:filename>")
def serve_image(filename):

    return send_from_directory(
        IMAGE_FOLDER,
        filename
    )


# ============================================
# 9. HEALTH CHECK
# ============================================

@app.route("/api/health", methods=["GET"])
def health():

    return jsonify({
        "status": "success",
        "message": "MUSEORA backend is running!"
    })


# ============================================
# 10. IMAGE UPLOAD VALIDATION
# ============================================

@app.route("/api/predict", methods=["POST"])
def predict():

    if "image" not in request.files:

        return jsonify({
            "error": "No image uploaded."
        }), 400

    file = request.files["image"]

    if not file.filename:

        return jsonify({
            "error": "No file selected."
        }), 400

    if not allowed_file(file.filename):

        return jsonify({
            "error": "Unsupported image format."
        }), 400

    try:

        image = Image.open(file.stream)
        image.verify()

    except Exception:

        return jsonify({
            "error": "Invalid image file."
        }), 400

    return jsonify({
        "status": "success",
        "message": "Image received and validated successfully.",
        "filename": secure_filename(file.filename)
    })


# ============================================
# 11. AI VISUAL SIMILARITY SEARCH
# ============================================

@app.route("/api/search", methods=["POST"])
def search_similar_images():

    if "image" not in request.files:

        return jsonify({
            "error": "No image uploaded."
        }), 400

    file = request.files["image"]

    if not file.filename:

        return jsonify({
            "error": "No file selected."
        }), 400

    if not allowed_file(file.filename):

        return jsonify({
            "error": "Unsupported image format."
        }), 400

    try:

        image = Image.open(file.stream).convert("RGB")

        query_features = extract_image_features(image)

        similarity_scores = cosine_similarity(
            query_features,
            IMAGE_FEATURES
        )[0]

        top_indices = np.argsort(
            similarity_scores
        )[::-1][:5]

        results = []

        for index in top_indices:

            results.append({
                "image": f"image_{int(index)}.png",
                "label": int(IMAGE_LABELS[index]),
                "similarity": round(
                    float(similarity_scores[index]),
                    4
                )
            })

        return jsonify({
            "status": "success",
            "message": "Visual similarity search completed!",
            "results": results
        })

    except Exception:

        app.logger.exception(
            "MUSEORA visual search failed."
        )

        return jsonify({
            "error": "Unable to analyse this image. Check the Flask terminal."
        }), 500


# ============================================
# 12. IMAGE FUSION API
# ============================================

@app.route("/api/fusion", methods=["POST"])
def fuse_images():

    try:

        files = request.files.getlist("images")

        if not files:

            return jsonify({
                "success": False,
                "error": "Please upload at least one image."
            }), 400

        if len(files) > 5:

            return jsonify({
                "success": False,
                "error": "Maximum 5 images allowed."
            }), 400

        cutouts = []
        objects = []

        for file in files:

            if not file or not file.filename:
                continue

            if not allowed_file(file.filename):

                return jsonify({
                    "success": False,
                    "error": "Unsupported image format."
                }), 400

            extension = os.path.splitext(
                secure_filename(file.filename)
            )[1].lower()

            filename = f"{uuid.uuid4().hex}{extension}"

            image_path = os.path.join(
                UPLOAD_FOLDER,
                filename
            )

            file.save(image_path)

            # Remove image background
            cutout_path = remove_background(image_path)

            if not cutout_path:
                continue

            cutouts.append(cutout_path)

            # Get individual transparent object information
            with Image.open(cutout_path) as image:

                image = image.convert("RGBA")

                objects.append({
                    "id": uuid.uuid4().hex,
                    "image_url": (
                        f"/fusion-results/"
                        f"{os.path.basename(cutout_path)}"
                    ),
                    "width": image.width,
                    "height": image.height
                })

        if not cutouts:

            return jsonify({
                "success": False,
                "error": "Could not process the uploaded images."
            }), 500

        # Generate unique composition filename
        output_name = f"{uuid.uuid4().hex}_fusion.png"

        output_path = create_composition(
            cutouts,
            output_name
        )

        # Verify generated image exists
        if not os.path.isfile(output_path):

            raise FileNotFoundError(
                f"Composition was not saved: {output_path}"
            )

        print("Generated composition:", output_path)
        print("File exists:", os.path.isfile(output_path))

        return jsonify({
            "success": True,
            "message": "Image fusion completed successfully!",
            "image_url": f"/fusion-results/{output_name}",
            "objects": objects,
            "canvas": {
                "width": 1200,
                "height": 900
            }
        })

    except Exception:

        app.logger.exception(
            "MUSEORA image fusion failed"
        )

        return jsonify({
            "success": False,
            "error": "Image fusion failed. Check the Flask terminal."
        }), 500


# ============================================
# 13. SERVE GENERATED FUSION IMAGES
# ============================================

@app.route("/fusion-results/<path:filename>")
def fusion_results(filename):

    print("Requested image:", filename)
    print("Looking inside:", FUSION_FOLDER)

    file_path = os.path.join(
        FUSION_FOLDER,
        filename
    )

    print("Full image path:", file_path)
    print("Image exists:", os.path.isfile(file_path))

    if not os.path.isfile(file_path):

        return jsonify({
            "success": False,
            "error": "Generated composition image not found.",
            "filename": filename,
            "folder": FUSION_FOLDER
        }), 404

    return send_from_directory(
        FUSION_FOLDER,
        filename
    )


# ============================================
# 14. RUN APPLICATION
# ============================================

if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
