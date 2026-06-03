import logging
from io import BytesIO
from pathlib import Path

from pypdf import PdfReader
from app.domain.ports.cv_text_extractor import CVTextExtractor

logger = logging.getLogger("cv-processing")


class PDFCVTextExtractor(CVTextExtractor):
    """
    Extrae texto de archivos PDF usando pypdf.
    
    Implementa la interfaz CVTextExtractor del dominio.
    """

    def extract_text(self, file_bytes: bytes, filename: str | None = None) -> str:
        """
        Extrae texto de todas las páginas de un PDF.
        
        Args:
            file_path: Ruta local al archivo PDF
        
        Returns:
            Texto extraído concatenado de todas las páginas
        
        Raises:
            ValueError: Si el archivo no existe o no es un PDF válido
            IOError: Si hay error al leer el archivo
        """
        try:
            if not file_bytes:
                raise ValueError("PDF bytes are empty")

            if filename:
                path = Path(filename)
                if path.suffix.lower() != ".pdf":
                    raise ValueError(f"File is not a PDF: {filename}")
            
            # Abrir y leer PDF
            pdf_reader = PdfReader(BytesIO(file_bytes))
            
            # Extraer texto de todas las páginas
            text_parts = []
            for page_num, page in enumerate(pdf_reader.pages):
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                except Exception as e:
                    logger.warning(f"Error extracting page {page_num}: {e}")
            
            # Concatenar todo el texto
            full_text = "\n".join(text_parts)
            
            logger.info(
                "Extracted %s characters from %s pages",
                len(full_text),
                len(pdf_reader.pages),
            )
            
            return full_text
        
        except ValueError:
            # Re-lanzar ValueError como está (validaciones)
            raise
        except Exception as e:
            logger.error("Unexpected error extracting text from PDF: %s", e)
            raise IOError(f"Failed to extract text from PDF: {e}")
