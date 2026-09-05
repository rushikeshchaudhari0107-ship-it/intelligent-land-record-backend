import re


ALLOWED_LAND_TYPES = {
    "Agricultural",
    "Residential",
    "Commercial",
    "Industrial"
}


def validate_land_record(record: dict) -> dict:

    errors = []

    # -----------------------------------------
    # OWNER NAME
    # -----------------------------------------

    owner_name = record.get(
        "owner_name"
    )

    if not owner_name:

        errors.append(
            "Owner name is missing."
        )

    elif len(owner_name.strip()) < 3:

        errors.append(
            "Owner name is too short."
        )

    # -----------------------------------------
    # SURVEY NUMBER
    # -----------------------------------------

    survey_number = record.get(
        "survey_number"
    )

    if not survey_number:

        errors.append(
            "Survey number is missing."
        )

    elif not re.match(
        r"^[A-Za-z0-9]+(?:/[A-Za-z0-9]+)?$",
        str(survey_number).strip()
    ):

        errors.append(
            "Survey number format is invalid."
        )

    # -----------------------------------------
    # VILLAGE
    # -----------------------------------------

    if not record.get("village"):

        errors.append(
            "Village is missing."
        )

    # -----------------------------------------
    # TALUKA
    # -----------------------------------------

    if not record.get("taluka"):

        errors.append(
            "Taluka is missing."
        )

    # -----------------------------------------
    # DISTRICT
    # -----------------------------------------

    if not record.get("district"):

        errors.append(
            "District is missing."
        )

    # -----------------------------------------
    # LAND AREA
    # -----------------------------------------

    land_area = record.get(
        "land_area"
    )

    if land_area is None:

        errors.append(
            "Land area is missing."
        )

    else:

        try:

            area = float(
                land_area
            )

            if area <= 0:

                errors.append(
                    "Land area must be greater than 0."
                )

        except (
            ValueError,
            TypeError
        ):

            errors.append(
                "Land area must be a valid number."
            )

    # -----------------------------------------
    # LAND TYPE
    # -----------------------------------------

    land_type = record.get(
        "land_type"
    )

    if not land_type:

        errors.append(
            "Land type is missing."
        )

    elif land_type not in ALLOWED_LAND_TYPES:

        errors.append(
            "Land type is invalid."
        )

    # -----------------------------------------
    # FINAL RESULT
    # -----------------------------------------

    return {
        "valid": len(errors) == 0,
        "errors": errors
    }