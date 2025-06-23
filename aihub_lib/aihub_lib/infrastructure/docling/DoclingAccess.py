import requests

from aihub_lib.infrastructure.docling.DoclingConfig import DoclingConfig


class DoclingAccess:
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DoclingAccess, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        self.config = DoclingConfig()

    @classmethod
    def update_config_from_resource(cls, resource):
        if cls._instance is None:
            cls._instance = cls()

        # Update configuration values from the resource
        if resource.api_endpoint:
            cls._instance.config.DOCLING_API_ENDPOINT = resource.api_endpoint
        if resource.api_timeout:
            cls._instance.config.DOCLING_API_TIMEOUT = resource.api_timeout
        if resource.ocr_engine:
            cls._instance.config.DOCLING_OCR_ENGINE = resource.ocr_engine
        if resource.pdf_backend:
            cls._instance.config.DOCLING_PDF_BACKEND = resource.pdf_backend
        if resource.table_mode:
            cls._instance.config.DOCLING_TABLE_MODE = resource.table_mode

    def convert_document(self, file_content: str, filename: str):
        request_body = {
            "options": {
                "from_formats": self.config.DOCLING_FROM_FORMATS,
                "to_formats": self.config.DOCLING_TO_FORMATS,
                "image_export_mode": self.config.DOCLING_IMAGE_EXPORT_MODE,
                "do_ocr": self.config.DOCLING_DO_OCR,
                "force_ocr": self.config.DOCLING_FORCE_OCR,
                "ocr_engine": self.config.DOCLING_OCR_ENGINE,
                "pdf_backend": self.config.DOCLING_PDF_BACKEND,
                "table_mode": self.config.DOCLING_TABLE_MODE,
                "abort_on_error": False,
                "return_as_file": False,
                "do_table_structure": True,
                "include_images": True,
                "images_scale": self.config.DOCLING_IMAGES_SCALE,
                "do_code_enrichment": True,
                "do_formula_enrichment": True,
                "do_picture_classification": False,
                "do_picture_description": False,
                "md_page_break_placeholder": self.config.MD_PAGE_BREAK_PLACEHOLDER,
            },
            "file_sources": [{"base64_string": file_content, "filename": filename}],
        }

        response = requests.post(
            self.config.DOCLING_API_ENDPOINT,
            json=request_body,
            headers={"Content-Type": "application/json"},
            timeout=self.config.DOCLING_API_TIMEOUT,
        )

        if response.status_code != 200:
            raise ValueError(f"Docling API request failed with status code {response.status_code}: {response.text}")

        return response.json()
