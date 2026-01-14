"""PDF processing service for file uploads and text extraction."""

import os
import shutil
import base64
import logging
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile
import uuid

from mistralai import Mistral
from project.config import get_settings

logger = logging.getLogger(__name__)


class PDFService:
    """
    Service for handling PDF file uploads and text extraction.

    Responsibilities:
    - File upload validation (type, size)
    - Temporary file storage
    - Text extraction using Mistral OCR (placeholder)
    - File cleanup
    """

    # Configuration
    MAX_FILE_SIZE_MB = 10
    MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024
    ALLOWED_CONTENT_TYPES = ["application/pdf"]
    UPLOAD_DIR = Path("/tmp/arco_uploads")

    def __init__(self):
        """Initialize PDFService and create upload directory if needed."""
        self.UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

    def generate_file_id(self) -> str:
        """Generate a unique file ID."""
        return str(uuid.uuid4())

    async def validate_pdf(self, file: UploadFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded PDF file.

        Args:
            file: Uploaded file from FastAPI

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        # Check content type
        if file.content_type not in self.ALLOWED_CONTENT_TYPES:
            return False, f"Invalid file type. Only PDF files are allowed. Got: {file.content_type}"

        # Check file extension
        if not file.filename:
            return False, "Filename is missing"

        if not file.filename.lower().endswith(".pdf"):
            return False, "File must have .pdf extension"

        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to beginning

        if file_size > self.MAX_FILE_SIZE_BYTES:
            size_mb = file_size / (1024 * 1024)
            return False, f"File too large: {size_mb:.2f}MB. Maximum allowed: {self.MAX_FILE_SIZE_MB}MB"

        if file_size == 0:
            return False, "File is empty"

        return True, None

    async def upload_pdf(self, file: UploadFile) -> Tuple[str, str, Optional[str]]:
        """
        Upload and save PDF file to temporary storage.

        Args:
            file: Uploaded PDF file

        Returns:
            Tuple[str, str, Optional[str]]: (file_id, file_path, error_message)
        """
        # Validate file
        is_valid, error = await self.validate_pdf(file)
        if not is_valid:
            return "", "", error

        # Generate file ID and path
        file_id = self.generate_file_id()
        filename = f"{file_id}_{file.filename}"
        file_path = self.UPLOAD_DIR / filename

        # Save file
        try:
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            return file_id, str(file_path), None
        except Exception as e:
            return "", "", f"Failed to save file: {str(e)}"
        finally:
            file.file.close()

    def extract_text_mistral_ocr(self, file_path: str) -> Tuple[str, Optional[str]]:
        """
        Extract text from PDF using Mistral OCR.

        Falls back to PyPDF2 if:
        - Mistral API key is not configured
        - Mistral API call fails

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple[str, Optional[str]]: (extracted_text, error_message)
        """
        settings = get_settings()

        # Check if Mistral API key is configured
        if not settings.mistral_api_key:
            logger.warning("Mistral API key not configured, falling back to PyPDF2")
            return self._extract_text_pypdf2(file_path)

        # Try Mistral OCR
        try:
            extracted_text = self._extract_text_with_mistral(
                file_path,
                settings.mistral_api_key
            )

            if not extracted_text.strip():
                return "", "No text found in PDF after OCR processing."

            return extracted_text, None

        except Exception as e:
            logger.error(f"Mistral OCR failed: {str(e)}, falling back to PyPDF2")
            return self._extract_text_pypdf2(file_path)

    def _extract_text_with_mistral(self, file_path: str, api_key: str) -> str:
        """
        Extract text using Mistral OCR API.

        Args:
            file_path: Path to PDF file
            api_key: Mistral API key

        Returns:
            str: Combined markdown text from all pages

        Raises:
            Exception: If API call fails
        """
        # Initialize Mistral client
        client = Mistral(api_key=api_key)

        # Encode PDF to base64
        base64_pdf = self._encode_pdf_base64(file_path)

        # Call Mistral OCR API
        ocr_response = client.ocr.process(
            model="mistral-ocr-latest",
            document={
                "type": "document_url",
                "document_url": f"data:application/pdf;base64,{base64_pdf}",
            },
            include_image_base64=False
        )

        # Combine text from all pages
        return self._combine_pages_markdown(ocr_response)

    def _encode_pdf_base64(self, file_path: str) -> str:
        """
        Encode PDF file to base64 string.

        Args:
            file_path: Path to PDF file

        Returns:
            str: Base64 encoded PDF content
        """
        with open(file_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode("utf-8")

    def _combine_pages_markdown(self, ocr_response) -> str:
        """
        Combine markdown text from all pages of OCR response.

        Args:
            ocr_response: Response from Mistral OCR API

        Returns:
            str: Combined markdown text with page separators
        """
        if not ocr_response or not hasattr(ocr_response, 'pages'):
            return ""

        pages_text = []
        for page in ocr_response.pages:
            if hasattr(page, 'markdown') and page.markdown:
                pages_text.append(page.markdown)

        return "\n\n".join(pages_text)

    def _extract_text_pypdf2(self, file_path: str) -> Tuple[str, Optional[str]]:
        """
        Extract text from PDF using PyPDF2 (fallback method).

        Note: PyPDF2 extracts embedded text only, not OCR for images.

        Args:
            file_path: Path to PDF file

        Returns:
            Tuple[str, Optional[str]]: (extracted_text, error_message)
        """
        try:
            import PyPDF2
            with open(file_path, "rb") as pdf_file:
                pdf_reader = PyPDF2.PdfReader(pdf_file)
                text_parts = []

                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text_parts.append(page.extract_text())

                extracted_text = "\n".join(text_parts)

                if not extracted_text.strip():
                    return "", "No text found in PDF. File may contain only images (OCR not available without Mistral API key)."

                return extracted_text, None

        except ImportError:
            return "", "PyPDF2 not installed. Install with: pip install pypdf2"
        except Exception as e:
            return "", f"Text extraction failed: {str(e)}"

    async def process_pdf(
        self,
        file: UploadFile
    ) -> Tuple[str, str, str, Optional[str]]:
        """
        Complete PDF processing pipeline.

        Workflow:
        1. Upload and validate file
        2. Extract text using Mistral OCR
        3. Return file_id, extracted text, and file path

        Args:
            file: Uploaded PDF file

        Returns:
            Tuple[str, str, str, Optional[str]]:
                (file_id, extracted_text, file_path, error_message)
        """
        # Step 1: Upload file
        file_id, file_path, error = await self.upload_pdf(file)
        if error:
            return "", "", "", error

        # Step 2: Extract text
        extracted_text, error = self.extract_text_mistral_ocr(file_path)
        if error:
            # Clean up uploaded file on extraction failure
            self.cleanup_file(file_path)
            return "", "", "", error

        return file_id, extracted_text, file_path, None

    def cleanup_file(self, file_path: str) -> bool:
        """
        Delete uploaded file from temporary storage.

        Args:
            file_path: Path to file to delete

        Returns:
            bool: True if deleted successfully
        """
        try:
            path = Path(file_path)
            if path.exists():
                path.unlink()
                return True
            return False
        except Exception as e:
            print(f"Failed to cleanup file {file_path}: {e}")
            return False

    def cleanup_by_file_id(self, file_id: str) -> int:
        """
        Delete all files matching a file_id pattern.

        Args:
            file_id: File ID to cleanup

        Returns:
            int: Number of files deleted
        """
        try:
            pattern = f"{file_id}_*"
            deleted = 0
            for file_path in self.UPLOAD_DIR.glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    deleted += 1
            return deleted
        except Exception as e:
            print(f"Failed to cleanup files for {file_id}: {e}")
            return 0

    def cleanup_old_files(self, max_age_hours: int = 24) -> int:
        """
        Delete files older than specified age.

        Args:
            max_age_hours: Maximum age in hours

        Returns:
            int: Number of files deleted
        """
        import time
        try:
            current_time = time.time()
            max_age_seconds = max_age_hours * 3600
            deleted = 0

            for file_path in self.UPLOAD_DIR.glob("*"):
                if file_path.is_file():
                    file_age = current_time - file_path.stat().st_mtime
                    if file_age > max_age_seconds:
                        file_path.unlink()
                        deleted += 1

            return deleted
        except Exception as e:
            print(f"Failed to cleanup old files: {e}")
            return 0


# Singleton instance for easy import
pdf_service = PDFService()
