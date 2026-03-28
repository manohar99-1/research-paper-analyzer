import pdfplumber
import requests
import tempfile
import os
from utils.logger import get_logger

logger = get_logger("pdf_parser")

MAX_CHARS = 12000  # Keep within context window limits

def extract_text_from_file(filepath: str) -> str:
    """Extract and clean text from a PDF file path."""
    logger.info(f"Extracting text from PDF: {filepath}")
    text_parts = []

    try:
        with pdfplumber.open(filepath) as pdf:
            logger.info(f"PDF has {len(pdf.pages)} pages")
            for i, page in enumerate(pdf.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(page_text.strip())

        full_text = "\n\n".join(text_parts)
        full_text = _clean_text(full_text)

        if len(full_text) > MAX_CHARS:
            logger.warning(f"Paper text truncated from {len(full_text)} to {MAX_CHARS} chars")
            full_text = full_text[:MAX_CHARS] + "\n\n[... truncated for context window ...]"

        logger.info(f"Extracted {len(full_text)} characters from PDF")
        return full_text

    except Exception as e:
        logger.error(f"Failed to parse PDF: {e}")
        raise ValueError(f"Could not extract text from PDF: {e}")


def extract_text_from_url(url: str) -> str:
    """Download a PDF from URL and extract text."""
    logger.info(f"Downloading PDF from URL: {url}")

    try:
        response = requests.get(url, timeout=30, stream=True)
        response.raise_for_status()

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            for chunk in response.iter_content(chunk_size=8192):
                tmp.write(chunk)
            tmp_path = tmp.name

        logger.info(f"Downloaded PDF to temp file: {tmp_path}")
        text = extract_text_from_file(tmp_path)
        os.unlink(tmp_path)
        return text

    except requests.RequestException as e:
        logger.error(f"Failed to download PDF: {e}")
        raise ValueError(f"Could not download PDF from URL: {e}")


def _clean_text(text: str) -> str:
    """Remove excessive whitespace and junk characters."""
    import re
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)  # remove non-ASCII
    return text.strip()
