
import os
import uuid

from PIL import Image, ImageOps, ImageFilter, ImageDraw
from rembg import remove


# ==========================================
# 1. FOLDER CONFIGURATION
# ==========================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
FUSION_FOLDER = os.path.join(BASE_DIR, "results", "fusion")

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(FUSION_FOLDER, exist_ok=True)

MAX_IMAGES = 5


# ==========================================
# 2. BACKGROUND REMOVAL
# ==========================================

def remove_background(image_path):
    """
    Removes the background from an uploaded image
    and saves the transparent image.
    """

    try:
        with Image.open(image_path) as image:

            # Correct image orientation
            image = ImageOps.exif_transpose(image)

            # Convert to RGBA
            image = image.convert("RGBA")

            # Resize large images to reduce memory usage
            image.thumbnail(
                (1600, 1600),
                Image.Resampling.LANCZOS
            )

            # Remove background using rembg
            output_image = remove(image)

            # Generate unique filename
            filename = f"{uuid.uuid4().hex}_cutout.png"

            output_path = os.path.join(
                FUSION_FOLDER,
                filename
            )

            # Save transparent PNG
            output_image.save(
                output_path,
                format="PNG"
            )

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

    # ======================================
    # 4. CREATE GRADIENT BACKGROUND
    # ======================================

    width, height = 1200, 900

    background = Image.new(
        "RGBA",
        (width, height)
    )

    for y in range(height):

        for x in range(width):

            ratio = (x + y) / (width + height)

            r = int(252 - (ratio * 8))
            g = int(249 - (ratio * 7))
            b = int(243 - (ratio * 5))

            background.putpixel(
                (x, y),
                (r, g, b, 255)
            )

    canvas = background
        # ======================================
    # AMBIENT LIGHTING
    # ======================================

    # Create a separate lighting layer
    lighting = Image.new(
        "RGBA",
        (width, height),
        (0, 0, 0, 0)
    )

    # Draw a warm glow behind the composition
    glow = Image.new(
        "RGBA",
        (width, height),
        (0, 0, 0, 0)
    )

    draw = ImageDraw.Draw(glow)

    draw.ellipse(
        (250, 200, 950, 850),
        fill=(255, 220, 160, 45)
    )

    # Blur the glow for smooth ambient lighting
    glow = glow.filter(
        ImageFilter.GaussianBlur(radius=110)
    )

    lighting = Image.alpha_composite(
        lighting,
        glow
    )

    canvas = Image.alpha_composite(
        canvas,
        lighting
    )

    
    # ======================================
    # 7. PROCESS EACH UPLOADED IMAGE
    # ======================================
    # ======================================
    # AUTOMATIC COMPOSITION LAYOUT
    # ======================================

    import math

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

    for index, image_path in enumerate(image_paths):

        with Image.open(image_path) as image:

            # Convert image to RGBA
            image = image.convert("RGBA")

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
                ImageFilter.GaussianBlur(radius=12)
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

    # SAVE THE FINAL COMPOSITION

    output_path = os.path.join(
        FUSION_FOLDER,
        output_name
    )

    canvas.save(
        output_path,
        format="PNG"
    )

    print("Composition saved successfully:", output_path)

    return output_path