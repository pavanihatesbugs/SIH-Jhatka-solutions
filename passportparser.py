"""
passport_ocr_traversal.py

Two independent passes over a flat OCR text list (e.g. PaddleOCR's
raw_texts):

  PASS A -- date classification by order of appearance:
    walk the list line by line, collect every string that looks like a
    date, and assign them in order: 1st = DOB, 2nd = date_of_issue,
    3rd = date_of_expiry (this matches the order dates are printed on
    an Indian passport bio-data page).

  PASS B -- MRZ identification + character traversal:
    walk the list to find the two MRZ lines, then walk each MRZ line
    with a moving cursor to pull out passport_number, country_code,
    surname, name, nationality, sex -- tolerating a couple of common
    real-world OCR quirks (a dropped leading 'P', and digit/letter
    confusions like '1' vs 'I').
"""

import re
from datetime import datetime


# ==========================================================================
# PASS A: dates, in order of appearance
# ==========================================================================

DATE_REGEX = re.compile(r"\b(\d{1,2})[/\-.](\d{1,2})[/\-.](\d{4})\b")


def extract_dates_in_order(raw_texts):
    """Walks raw_texts top to bottom, collects every date-shaped string,
    and assigns them positionally: 1st->DOB, 2nd->issue, 3rd->expiry."""
    found = []
    for line in raw_texts:
        match = DATE_REGEX.search(line)
        if match:
            d, m, y = match.groups()
            found.append(f"{int(d):02d}/{int(m):02d}/{y}")

    result = {"dob": None, "date_of_issue": None, "date_of_expiry": None}
    labels = ["dob", "date_of_issue", "date_of_expiry"]
    for label, value in zip(labels, found):
        result[label] = value

    result["_all_dates_found"] = found  # handy for debugging if order is off
    return result


# ==========================================================================
# PASS B: find MRZ lines, then traverse them
# ==========================================================================

def _normalize(line: str) -> str:
    return line.upper().replace(" ", "")


def _looks_like_mrz(line: str) -> bool:
    norm = _normalize(line)
    if len(norm) < 28 or "<" not in norm:
        return False
    valid = sum(1 for c in norm if c.isalnum() or c == "<")
    return (valid / len(norm)) > 0.85  # slightly relaxed for noisy OCR


def find_mrz_lines(raw_texts):
    """Returns the two MRZ lines exactly as OCR produced them (not yet
    padded/fixed-width) -- traversal below handles length variance."""
    candidates = [_normalize(t) for t in raw_texts if _looks_like_mrz(t)]
    if len(candidates) >= 2:
        return candidates[-2], candidates[-1]
    if len(candidates) == 1 and len(candidates[0]) >= 70:
        mid = len(candidates[0]) // 2
        return candidates[0][:mid], candidates[0][mid:]
    return None, None


def _fix_alpha_ocr_confusions(s: str) -> str:
    """Common OCR digit<->letter mixups inside fields that should be
    pure alphabetic (nationality, country code)."""
    return (s.replace("1", "I")
             .replace("0", "O")
             .replace("5", "S")
             .replace("8", "B"))


# Codes this pipeline expects to see (India-issued passports). Extend this
# set if you start processing other countries' passports.
KNOWN_VALID_CODES = {"IND"}


def _correct_country_like_code(code: str) -> str:
    """Fixes letter-to-letter OCR misreads (e.g. 'INO' for 'IND') that
    _fix_alpha_ocr_confusions can't catch, since that function only maps
    digits to letters, not letters to other letters.

    Compares `code` against each known-valid code of the same length; if
    exactly one character differs (Hamming distance 1), assumes OCR noise
    and returns the known-valid code instead. Leaves `code` untouched if
    it doesn't closely match anything known, so genuinely different
    country codes aren't clobbered.
    """
    code = code.upper()
    if code in KNOWN_VALID_CODES:
        return code
    for valid in KNOWN_VALID_CODES:
        if len(code) == len(valid):
            diff = sum(1 for a, b in zip(code, valid) if a != b)
            if diff <= 1:
                return valid
    return code


def traverse_mrz_line1(line1: str) -> dict:
    """Walks line1 with a cursor. Standard layout: doc_type(1) +
    subtype(1) + country(3) + names(rest).

    Cursor position is decided from the FIRST character(s) actually
    present, not from total line length -- length alone is unreliable
    because trailing filler '<' characters are frequently truncated by
    OCR (harmless, since they're just padding) independently of whether
    the leading 'P' was dropped. Mixing those two up (as an earlier
    version of this function did) causes the country-code window to
    shift incorrectly when only the *trailing* padding is short.
        line1[0] == 'P'  -> doc_type present, cursor = 2 (skip P + subtype)
        line1[0] == '<'  -> doc_type missing, subtype present, cursor = 1
        otherwise        -> both missing, cursor = 0 (best effort)
    """
    if line1[0] == "P":
        cursor = 2
    elif line1[0] == "<":
        cursor = 1
    else:
        cursor = 0

    country_code = line1[cursor:cursor + 3]
    cursor += 3
    names_field = line1[cursor:]

    idx = names_field.find("<<")
    if idx == -1:
        surname, given = names_field.replace("<", " ").strip() or None, None
    else:
        surname = names_field[:idx].replace("<", " ").strip() or None
        given = names_field[idx + 2:].replace("<", " ").strip()

    return {
        "country_code": _correct_country_like_code(
            _fix_alpha_ocr_confusions(country_code).replace("<", "")
        ),
        "surname": surname,
        "name": given,
    }


def traverse_mrz_line2(line2: str) -> dict:
    """Walks line2 with a cursor, per the standard TD3 layout. Cursor
    positions are fixed here since line2 tends to survive OCR at full
    width even when line1 doesn't."""
    cursor = 0
    passport_number = line2[cursor:cursor + 9]; cursor += 9
    cursor += 1  # skip passport number check digit
    nationality = line2[cursor:cursor + 3]; cursor += 3
    dob_raw = line2[cursor:cursor + 6]; cursor += 6
    cursor += 1  # skip DOB check digit
    sex_code = line2[cursor:cursor + 1]; cursor += 1
    expiry_raw = line2[cursor:cursor + 6]; cursor += 6

    def fmt(yymmdd):
        try:
            return datetime.strptime(yymmdd, "%y%m%d").strftime("%d/%m/%Y")
        except ValueError:
            return None

    return {
        "passport_number": passport_number.replace("<", ""),
        "nationality": _correct_country_like_code(
            _fix_alpha_ocr_confusions(nationality).replace("<", "")
        ),
        "dob": fmt(dob_raw),
        "sex": {"M": "Male", "F": "Female"}.get(sex_code, "Unspecified"),
        "date_of_expiry": fmt(expiry_raw),
    }


def extract_mrz_data(raw_texts):
    line1, line2 = find_mrz_lines(raw_texts)
    if not line1 or not line2:
        return {}
    data = {}
    data.update(traverse_mrz_line1(line1))
    data.update(traverse_mrz_line2(line2))
    return data


# ==========================================================================
# Combined -- this is the one function to import into main.py
# ==========================================================================

def extract_passport_info(raw_texts):
    """
    The single entry point to call from main.py.

    raw_texts: flat list of OCR strings for the whole passport page
               (same list you already build in run_pipeline()).

    Returns a plain dict with these keys, ready to iterate/print:
        passport_number, country_code, surname, name, nationality,
        sex, dob, date_of_issue, date_of_expiry
    Any field that couldn't be found is set to None.
    """
    date_data = extract_dates_in_order(raw_texts)
    mrz_data = extract_mrz_data(raw_texts)

    return {
        "passport_number": mrz_data.get("passport_number"),
        "country_code": mrz_data.get("country_code"),
        "surname": mrz_data.get("surname"),
        "name": mrz_data.get("name"),
        "nationality": mrz_data.get("nationality"),
        "sex": mrz_data.get("sex"),
        "dob": mrz_data.get("dob") or date_data.get("dob"),
        "date_of_issue": date_data.get("date_of_issue"),
        "date_of_expiry": mrz_data.get("date_of_expiry") or date_data.get("date_of_expiry"),
    }


if __name__ == "__main__":
    import json

    raw_texts = ['m/p', 'eeg etw/Country Code', 'P', 'IND', 'ee/Smta', 'R7123405',
                 'MAQDOOMA FATHIMA', 'aglat/ Nationally', '(icy / Son',
                 'MAINT/INDIAN', 'F', '23/06/1981', '/PaceofBirth',
                 'CHENNAI, TAMIL NADU', '厂', ' ', 'Mhuyloonafalua', 'BENGALURU',
                 '15/12/2017', '14/12/2027',
                 '<IND<<MAQDOOMA<FATHIMA<<<<<<<<<<<<<<<<<<<<<',
                 'R7123405<31ND8106230F2712147<<<<<<<<<<<<<<<2']

    result = extract_passport_info(raw_texts)
    print(json.dumps(result, indent=2))

    for key, value in result.items():
        print(f"{key}: {value}")