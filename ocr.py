import os
import re
import pytesseract

from PIL import Image, ImageEnhance, ImageFilter, ImageOps


# Tesseract works on both Windows (local development) and Linux (Render).
# On Windows, set TESSERACT_CMD if the executable is installed elsewhere.
TESSERACT_PATH = os.getenv("TESSERACT_CMD")

if TESSERACT_PATH:
    pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
elif os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = (
        r"C:\Users\Rushikesh Chaudhari"
        r"\AppData\Local\Programs\Tesseract-OCR"
        r"\tesseract.exe"
    )


def extract_text(image_path: str) -> str:
    image = Image.open(image_path)

    # Full document OCR
    processed = ImageOps.grayscale(image)
    processed = ImageEnhance.Contrast(processed).enhance(2.0)
    processed = processed.filter(ImageFilter.SHARPEN)

    width, height = processed.size
    processed = processed.resize((width * 2, height * 2))

    text = pytesseract.image_to_string(
        processed,
        config="--oem 3 --psm 6"
    )

    # Land area OCR - crop used by the current 7/12 test document.
    area_crop = image.crop((380, 460, 600, 555))
    area_crop = area_crop.resize((area_crop.width * 4, area_crop.height * 4))
    area_crop = ImageOps.grayscale(area_crop)
    area_crop = ImageEnhance.Contrast(area_crop).enhance(2.0)
    area_crop = area_crop.filter(ImageFilter.SHARPEN)

    area_text = pytesseract.image_to_string(
        area_crop,
        config="--oem 3 --psm 6"
    ).strip()

    area_match = re.search(
        r"\b([0-9]+\.[0-9]+\.[0-9]+)\b",
        area_text
    )

    if area_match:
        text += f"\nLand Area: {area_match.group(1)}\n"

    # Land type OCR - crop used by the current 7/12 test document.
    land_type_crop = image.crop((730, 460, 970, 555))
    land_type_crop = land_type_crop.resize(
        (land_type_crop.width * 4, land_type_crop.height * 4)
    )
    land_type_crop = ImageOps.grayscale(land_type_crop)
    land_type_crop = ImageEnhance.Contrast(land_type_crop).enhance(2.0)
    land_type_crop = land_type_crop.filter(ImageFilter.SHARPEN)

    land_type_text = pytesseract.image_to_string(
        land_type_crop,
        config="--oem 3 --psm 6"
    ).strip()

    land_type_match = re.search(
        r"\b(Agricultural|Residential|Commercial|Industrial)\b",
        land_type_text,
        re.IGNORECASE
    )

    if land_type_match:
        detected_land_type = land_type_match.group(1).capitalize()
        text += f"\nLand Type: {detected_land_type}\n"

    return text.strip()
