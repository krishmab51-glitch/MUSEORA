import os
import uuid
import math
import numpy as np

from PIL import Image, ImageOps, ImageFilter, ImageDraw
from rembg import remove, new_session


# ==========================================
# 1. FOLDER CONFIGURATION
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
FUSION_FOLDER = os.path.join(BASE_DIR, "results", "fusion")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FUSION_FOLDER, exist_ok=True)

MAX_IMAGES = 5

# Lightweight AI model for background removal
_rembg_session = None


def get_rembg_session():
    global _rembg_session

    if _rembg_session is None:
        _rembg_session = new_session("u2netp")

    return _rembg_session


# ==========================================
# 2. BACKGROUND REMOVAL
# ==========================================

def remove_background(image_path):
    """
    Removes the background using the lightweight U2NETP model.
    """

    try:
        with Image.open(image_path) as image:

            # Correct image orientation
            image = ImageOps.exif_transpose(image)

            # Convert to RGB
            image = image.convert("RGB")

            # Reduce image dimensions to save RAM
            image.thumbnail(
                (800, 800),
                Image.Resampling.LANCZOS
            )

            # Convert to RGBA
            image = image.convert("RGBA")

            # Load lightweight model when required
            session = get_rembg_session()

            # Remove background
            output_image = remove(
                image,
                session=session
            )

            # Save transparent cutout
            filename = f"{uuid.uuid4().hex}_cutout.png"

            output_path = os.path.join(
                FUSION_FOLDER,
                filename
            )

            output_image.save(
                output_path,
                format="PNG"
            )

            output_image.close()
            image.close()

            print("Background removed successfully!")

            return output_path

    except Exception as e:

        print(f"Background removal failed: {e}")

        return None


# ==========================================
# 3. IMAGE COMPOSITION
# ==========================================

def create_composition(
    image_paths,
    output_name="museora_fusion.png"
):
    """
    Combines transparent images into one composition
    with a warm gradient background and blurred shadows.
    """

    if not image_paths:
        raise ValueError("No images provided.")

    if len(image_paths) > MAX_IMAGES:
        raise ValueError("Maximum 5 images allowed.")

    width = 1200
    height = 900

    # ======================================
    # CREATE MEMORY-EFFICIENT GRADIENT
    # ======================================

    y, x = np.mgrid[0:height, 0:width]

    ratio = (x + y) / (width + height)

    r = (252 - ratio * 8).astype(np.uint8)
    g = (249 - ratio * 7).astype(np.uint8)
    b = (243 - ratio * 5).astype(np.uint8)

    gradient = np.stack(
        [r, g, b, np.full_like(r, 255)],
        axis=-1
    )

    background = Image.fromarray(gradient, "RGBA")

    canvas = background

    # ======================================
    # AMBIENT LIGHTING
    # ======================================

    glow = Image.new(
        "RGBA",
        (width, height),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(glow)

    draw.ellipse(
        (250, 200, 950, 850),
        fill=(255, 220, 160, 35)
    )

    glow = glow.filter(
        ImageFilter.GaussianBlur(radius=80)
    )

    canvas = Image.alpha_composite(
        canvas,
        glow
    )

    glow.close()

    # ======================================
    # AUTOMATIC COMPOSITION LAYOUT
    # ======================================

    image_count = len(image_paths)

    # Calculate number of columns and rows
    columns = math.ceil(
        math.sqrt(image_count * width / height)
    )

    rows = math.ceil(image_count / columns)

    # Calculate available space for each object
    cell_width = width // columns
    cell_height = height // rows

    print("Automatic layout activated!")
    print("Images:", image_count)
    print("Columns:", columns)
    print("Rows:", rows)

    # ======================================
    # PROCESS EACH UPLOADED IMAGE
    # ======================================

    for index, image_path in enumerate(image_paths):

        with Image.open(image_path) as source_image:

            # Convert image to RGBA
            image = source_image.convert("RGBA")

            # Remove transparent margins
            bbox = image.getchannel("A").getbbox()

            if bbox:
                image = image.crop(bbox)

            # Calculate current grid position
            row = index // columns
            column = index % columns

            # Calculate maximum object dimensions
            max_width = cell_width - 80
            max_height = cell_height - 80

            # Resize while maintaining original proportions
            image.thumbnail(
                (max_width, max_height),
                Image.Resampling.LANCZOS
            )

            # Centre object inside its layout cell
            x = (
                column * cell_width
                + (cell_width - image.width) // 2
            )

            y = (
                row * cell_height
                + (cell_height - image.height) // 2
            )

            # ==================================
            # CREATE SOFT SHADOW
            # ==================================

            alpha = image.getchannel("A")

            shadow_size = (
                image.width + 40,
                image.height + 40
            )

            shadow_alpha = Image.new(
                "L",
                shadow_size,
                0
            )

            shadow_alpha.paste(
                alpha,
                (28, 32)
            )

            shadow_alpha = shadow_alpha.filter(
                ImageFilter.GaussianBlur(radius=8)
            )

            shadow = Image.new(
                "RGBA",
                shadow_size,
                (55, 45, 40, 0)
            )

            shadow.putalpha(
                shadow_alpha.point(
                    lambda value: int(value * 0.25)
                )
            )

            # Place shadow
            canvas.alpha_composite(
                shadow,
                (x - 20, y - 20)
            )

            # Place original image
            canvas.alpha_composite(
                image,
                (x, y)
            )

            # Close temporary images
            alpha.close()
            shadow_alpha.close()
            shadow.close()
            image.close()

    # ======================================
    # SAVE THE FINAL COMPOSITION
    # ======================================

    output_path = os.path.join(
        FUSION_FOLDER,
        output_name
    )

    canvas.save(
        output_path,
        format="PNG"
    )

    print("Composition saved successfully:", output_path)

    canvas.close()

    return output_path
