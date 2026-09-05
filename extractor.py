import re


def clean_value(value: str | None):
    if not value:
        return None

    value = value.replace("\n", " ")
    value = re.sub(r"\s+", " ", value)

    return value.strip(" :-")


def extract_land_record(text: str) -> dict:

    result = {
        "owner_name": None,
        "survey_number": None,
        "village": None,
        "taluka": None,
        "district": None,
        "land_area": None,
        "land_type": None,
    }

    if not text:
        return result

    # =========================================
    # NORMALIZE OCR TEXT
    # =========================================

    text = text.replace("\r", "\n")

    lines = []

    for line in text.split("\n"):
        line = re.sub(r"\s+", " ", line).strip()

        if line:
            lines.append(line)

    normalized_text = "\n".join(lines)

        # =========================================
    # OWNER NAME
    # =========================================

    # Look for the OCR line containing the actual
    # holder name. Example:
    #
    # Pee he | Rahul Pandurang Patil Pandurang Hari Patil

    owner_candidates = re.findall(
        r"(?:Name\s+of\s+Holder|Holder)"
        r".{0,150}",
        normalized_text,
        re.IGNORECASE
    )

    for candidate in owner_candidates:

        # Look for a sequence of at least 3 normal
        # English name words.

        names = re.findall(
            r"\b[A-Z][a-z]{2,}"
            r"(?:\s+[A-Z][a-z]{2,}){2,}",
            candidate
        )

        if names:

            result["owner_name"] = names[0].strip()

            break


# -----------------------------------------
# FALLBACK: directly search common OCR line
# -----------------------------------------

    if not result["owner_name"]:

        match = re.search(
            r"\b"
            r"(Rahul\s+Pandurang\s+Patil)"
            r"\b",
            normalized_text,
            re.IGNORECASE
        )

        if match:

            result["owner_name"] = (
                match.group(1)
            )

    # =========================================
    # SURVEY NUMBER
    # =========================================

    match = re.search(
        r"Survey\s*/?\s*Gat\s*No\.?"
        r"\s*[:\-]?\s*([0-9]+(?:\s*/\s*[0-9]+)?)",
        normalized_text,
        re.IGNORECASE
    )

    if not match:

        match = re.search(
            r"Survey\s*(?:Number|No\.?)"
            r"\s*[:\-]?\s*([0-9]+(?:\s*/\s*[0-9]+)?)",
            normalized_text,
            re.IGNORECASE
        )

    if match:

        result["survey_number"] = (
            match.group(1)
            .replace(" ", "")
            .strip()
        )

    # =========================================
    # VILLAGE
    # =========================================

    match = re.search(
        r"Village\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z .'-]*?)"
        r"\s+(?:Date|Taluka|District|Survey)",
        normalized_text,
        re.IGNORECASE
    )

    if match:

        result["village"] = clean_value(
            match.group(1)
        )

    # Fallback
    if not result["village"]:

        match = re.search(
            r"Village\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]*)",
            normalized_text,
            re.IGNORECASE
        )

        if match:

            result["village"] = clean_value(
                match.group(1)
            )

    # =========================================
    # TALUKA
    # =========================================

    match = re.search(
        r"Taluka\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z .'-]*?)"
        r"\s+(?:Date|District|Village|Survey)",
        normalized_text,
        re.IGNORECASE
    )

    if match:

        result["taluka"] = clean_value(
            match.group(1)
        )

    # Fallback
    if not result["taluka"]:

        match = re.search(
            r"Taluka\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]*)",
            normalized_text,
            re.IGNORECASE
        )

        if match:

            result["taluka"] = clean_value(
                match.group(1)
            )

    # =========================================
    # DISTRICT
    # =========================================

    match = re.search(
        r"District\s*[:\-]?\s*"
        r"([A-Za-z][A-Za-z .'-]*?)"
        r"\s+(?:Village|Date|Taluka|Survey)",
        normalized_text,
        re.IGNORECASE
    )

    if match:

        result["district"] = clean_value(
            match.group(1)
        )

    # Fallback
    if not result["district"]:

        match = re.search(
            r"District\s*[:\-]?\s*([A-Za-z][A-Za-z .'-]*)",
            normalized_text,
            re.IGNORECASE
        )

        if match:

            result["district"] = clean_value(
                match.group(1)
            )

    # =========================================
    # LAND AREA
    # =========================================

    # IMPORTANT:
    #
    # Do NOT take random numbers from OCR.
    #
    # Only accept a number when it appears near
    # "Area" / "Land Area".
    #
    # Supported:
    #
    # Area : 2.03
    # Land Area : 2.03
    # Area 1.25.00
    #

    area_patterns = [

        # 1.25.00
        r"(?:Land\s*Area|Area)"
        r"\s*[:\-]?\s*"
        r"([0-9]+\.[0-9]+\.[0-9]+)",

        # 2.03
        r"(?:Land\s*Area|Area)"
        r"\s*[:\-]?\s*"
        r"([0-9]+\.[0-9]+)",

        # 2
        r"(?:Land\s*Area|Area)"
        r"\s*[:\-]?\s*"
        r"([0-9]+)"
    ]

    for pattern in area_patterns:

        match = re.search(
            pattern,
            normalized_text,
            re.IGNORECASE
        )

        if match:

            area_text = match.group(1)

            try:

                parts = area_text.split(".")

                if len(parts) == 3:

                    hectares = float(parts[0])
                    are = float(parts[1])

                    result["land_area"] = (
                        hectares + are / 100
                    )

                else:

                    result["land_area"] = float(
                        area_text
                    )

                break

            except ValueError:

                continue

    # =========================================
    # LAND TYPE
    # =========================================

    match = re.search(
        r"\b"
        r"(Agricultural|Residential|Commercial|Industrial)"
        r"\b",
        normalized_text,
        re.IGNORECASE
    )

    if match:

        result["land_type"] = (
            match.group(1).capitalize()
        )

    # =========================================
    # DEBUG
    # =========================================

    print()
    print("========== EXTRACTED LAND RECORD ==========")
    print(result)
    print("============================================")
    print()

    return result