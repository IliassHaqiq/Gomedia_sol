import os
import re
import unicodedata
from typing import List

import openpyxl
import pdfplumber


MAX_TEXT_LENGTH = 6000


def clean_text(text: str) -> str:
    if not text:
        return ""

    # normalisation unicode
    text = unicodedata.normalize("NFKC", text)

    # remplace espaces insécables et caractères bizarres fréquents
    replacements = {
        "\u00a0": " ",
        "\u200b": "",
        "\ufeff": "",
        "\t": " ",
        "\r": "\n",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)

    # supprime les espaces multiples
    text = re.sub(r"[ ]{2,}", " ", text)

    # supprime les lignes vides excessives
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


def normalize_key(key: str) -> str:
    key = clean_text(key).strip(":;- ")
    if not key:
        return "Champ"
    return key


def normalize_value(value: str) -> str:
    value = clean_text(value)

    # normalisation légère des unités
    unit_map = {
        " vdc": " VDC",
        " vac": " VAC",
        " v ": " V ",
        " a ": " A ",
        " ma": " mA",
        " kw": " kW",
        " w ": " W ",
        " hz": " Hz",
    }

    lowered = f" {value.lower()} "
    for old, new in unit_map.items():
        lowered = lowered.replace(old, f" {new} ")
    value = lowered.strip()

    # remet un espace simple partout
    value = re.sub(r"\s{2,}", " ", value)
    return value


def truncate_text(text: str, max_length: int = MAX_TEXT_LENGTH) -> str:
    text = clean_text(text)
    if len(text) <= max_length:
        return text
    return text[:max_length]


def extract_text_from_pdf(file_path: str) -> str:
    chunks: List[str] = []

    with pdfplumber.open(file_path) as pdf:
        for page_index, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            page_text = clean_text(page_text)
            if page_text:
                chunks.append(f"[PAGE {page_index}]\n{page_text}")

    return truncate_text("\n\n".join(chunks))


def extract_text_from_excel(file_path: str) -> str:
    wb = openpyxl.load_workbook(file_path, data_only=True)
    output_chunks: List[str] = []

    for sheet in wb.worksheets:
        sheet_lines: List[str] = [f"[SHEET: {sheet.title}]"]

        for row in sheet.iter_rows(values_only=True):
            values = [str(cell).strip() for cell in row if cell is not None and str(cell).strip()]
            if not values:
                continue

            # Cas 1 : ligne type clé / valeur
            if len(values) == 2:
                key = normalize_key(values[0])
                value = normalize_value(values[1])
                sheet_lines.append(f"{key}: {value}")
            else:
                # Cas 2 : ligne plus complexe → concaténation lisible
                cleaned_values = [normalize_value(v) for v in values]
                sheet_lines.append(" | ".join(cleaned_values))

        output_chunks.append("\n".join(sheet_lines))

    return truncate_text("\n\n".join(output_chunks))


def extract_text_from_file(file_path: str) -> str:
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        return extract_text_from_pdf(file_path)

    if ext == ".xlsx":
        return extract_text_from_excel(file_path)

    raise ValueError(f"Format non supporté pour l'extraction: {ext}")