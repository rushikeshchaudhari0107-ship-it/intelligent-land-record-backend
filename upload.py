import os
import uuid

from fastapi import APIRouter, UploadFile, File, HTTPException
from backend.ocr import extract_text
from backend.extractor import extract_land_record
from backend.validator import validate_land_record
from backend.db_connection import get_db_connection

router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"]
)


UPLOAD_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)),
    "documents",
    "uploads"
)


os.makedirs(UPLOAD_DIR, exist_ok=True)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".jpg",
    ".jpeg",
    ".png"
}


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, JPG, JPEG and PNG files are allowed"
        )

    unique_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    try:

        contents = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        return {
            "status": "success",
            "message": "Document uploaded successfully",
            "original_filename": file.filename,
            "saved_filename": unique_filename,
            "file_size": len(contents)
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@router.post("/ocr")
async def extract_document_text(
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in {
        ".jpg",
        ".jpeg",
        ".png"
    }:
        raise HTTPException(
            status_code=400,
            detail="OCR currently supports JPG, JPEG and PNG"
        )

    unique_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    try:
        contents = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        text = extract_text(file_path)

        return {
            "status": "success",
            "filename": file.filename,
            "extracted_text": text
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@router.post("/extract")
async def extract_land_record_from_document(
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in {
        ".jpg",
        ".jpeg",
        ".png"
    }:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG and PNG files are supported"
        )

    unique_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    try:
        # Save uploaded file
        contents = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        # OCR
        extracted_text = extract_text(
            file_path
        )

        # Extract structured fields
        land_record = extract_land_record(
            extracted_text
        )

        return {
            "status": "success",
            "filename": file.filename,
            "raw_text": extracted_text,
            "land_record": land_record
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@router.post("/validate")
async def validate_document(
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in {
        ".jpg",
        ".jpeg",
        ".png"
    }:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG and PNG files are supported"
        )

    unique_filename = (
        f"{uuid.uuid4()}{extension}"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    try:
        # Save file
        contents = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        # OCR
        extracted_text = extract_text(
            file_path
        )

        # Extract fields
        land_record = extract_land_record(
            extracted_text
        )

        # Validate fields
        validation = validate_land_record(
            land_record
        )

        return {
            "status": "success",
            "filename": file.filename,
            "land_record": land_record,
            "validation": validation
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )
@router.post("/save")
async def save_land_record(
    file: UploadFile = File(...)
):
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file selected"
        )

    extension = os.path.splitext(
        file.filename
    )[1].lower()

    if extension not in {".jpg", ".jpeg", ".png"}:
        raise HTTPException(
            status_code=400,
            detail="Only JPG, JPEG and PNG files are supported"
        )

    unique_filename = f"{uuid.uuid4()}{extension}"

    file_path = os.path.join(
        UPLOAD_DIR,
        unique_filename
    )

    connection = None
    cursor = None

    try:
        # -----------------------------
        # Save uploaded image
        # -----------------------------

        contents = await file.read()

        with open(file_path, "wb") as buffer:
            buffer.write(contents)

        # -----------------------------
        # OCR
        # -----------------------------

        extracted_text = extract_text(
            file_path
        )

        # -----------------------------
        # Extract fields
        # -----------------------------

        land_record = extract_land_record(
            extracted_text
        )

        # -----------------------------
        # Validate
        # -----------------------------

        validation = validate_land_record(
            land_record
        )

        if not validation["valid"]:
            return {
                "status": "validation_failed",
                "errors": validation["errors"],
                "land_record": land_record
            }

        # -----------------------------
        # Connect PostgreSQL
        # -----------------------------

        connection = get_db_connection()
        cursor = connection.cursor()

        # -----------------------------
        # Check duplicate survey number
        # -----------------------------

        cursor.execute(
            """
            SELECT id
            FROM land_records
            WHERE survey_number = %s;
            """,
            (land_record["survey_number"],)
        )

        existing_record = cursor.fetchone()

        if existing_record:
            return {
                "status": "duplicate",
                "message": "Survey number already exists",
                "survey_number": land_record["survey_number"],
                "existing_id": existing_record[0]
            }

        # -----------------------------
        # Insert record
        # -----------------------------

        cursor.execute(
            """
            INSERT INTO land_records
            (
                owner_name,
                survey_number,
                village,
                taluka,
                district,
                land_area,
                land_type
            )
            VALUES
            (
                %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING id;
            """,
            (
                land_record["owner_name"],
                land_record["survey_number"],
                land_record["village"],
                land_record["taluka"],
                land_record["district"],
                land_record["land_area"],
                land_record["land_type"]
            )
        )

        new_id = cursor.fetchone()[0]

        connection.commit()

        return {
            "status": "success",
            "message": "Land record saved successfully",
            "id": new_id,
            "land_record": land_record
        }

    except Exception as e:

        if connection:
            connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        if cursor:
            cursor.close()

        if connection:
            connection.close()