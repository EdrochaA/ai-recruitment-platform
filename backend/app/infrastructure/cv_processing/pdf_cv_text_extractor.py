import logging
from pathlib import Path

from pypdf import PdfReader
from app.domain.ports.cv_text_extractor import CVTextExtractor

logger = logging.getLogger("cv-processing")


class PDFCVTextExtractor(CVTextExtractor):
    """
    Extrae texto de archivos PDF usando pypdf.
    
    Implementa la interfaz CVTextExtractor del dominio.
    """

    def extract_text(self, file_path: str) -> str:
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
            path = Path(file_path)
            
            # Validar que el archivo existe
            if not path.exists():
                raise ValueError(f"File not found: {file_path}")
            
            # Validar extensión
            if path.suffix.lower() != ".pdf":
                raise ValueError(f"File is not a PDF: {file_path}")
            
            # Abrir y leer PDF
            pdf_reader = PdfReader(file_path)
            
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
            
            logger.info(f"Extracted {len(full_text)} characters from {len(pdf_reader.pages)} pages")
            
            return full_text
        
        except ValueError:
            # Re-lanzar ValueError como está (validaciones)
            raise
        except Exception as e:
            logger.error(f"Unexpected error extracting text from {file_path}: {e}")
            raise IOError(f"Failed to extract text from PDF: {e}")
