from abc import ABC, abstractmethod


class CVTextExtractor(ABC):
    """
    Puerto para extracción de texto de CVs en formato PDF.
    
    Define la interfaz que debe implementar cualquier extractor de texto
    de PDFs, manteniendo el dominio independiente de la tecnología específica
    (pypdf, pdfplumber, etc).
    """

    @abstractmethod
    def extract_text(self, file_path: str) -> str:
        """
        Extrae texto de un archivo PDF.
        
        Args:
            file_path: Ruta local al archivo PDF
        
        Returns:
            Texto extraído del PDF como string
        
        Raises:
            ValueError: Si el archivo no existe o no es un PDF válido
            IOError: Si hay error al leer el archivo
        """
        pass
