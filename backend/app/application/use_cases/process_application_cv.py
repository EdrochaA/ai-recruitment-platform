import logging
from datetime import datetime

from app.domain.entities.job_application import JobApplication
from app.domain.ports.cv_text_extractor import CVTextExtractor
from app.domain.ports.job_application_repository import JobApplicationRepository

logger = logging.getLogger("use-cases")


class ProcessApplicationCV:
    """
    Extrae el texto del CV PDF de una candidatura.
    
    Responsabilidades:
    - Validar que la candidatura existe
    - Validar que tiene CV subido
    - Extraer texto del PDF (vía puerto CVTextExtractor)
    - Actualizar estado de procesamiento
    - Persistir cambios
    """

    def __init__(
        self,
        application_repository: JobApplicationRepository,
        cv_text_extractor: CVTextExtractor,
    ):
        self.application_repository = application_repository
        self.cv_text_extractor = cv_text_extractor

    def execute(self, application_id: str) -> JobApplication:
        """
        Procesa el CV de una candidatura.
        
        Args:
            application_id: ID de la candidatura a procesar
        
        Returns:
            JobApplication actualizada con texto extraído y estado procesado
        
        Raises:
            ValueError: Si no existe, no tiene CV, o falla la extracción
        """
        logger.info(f"Processing CV for application {application_id}")
        
        # 1. Buscar candidatura
        application = self.application_repository.find_by_id(application_id)
        if not application:
            raise ValueError(f"Application {application_id} not found")
        
        # 2. Validar que tiene CV subido
        if not application.cv_storage_key:
            raise ValueError(
                f"Application {application_id} has no CV uploaded. "
                "Upload a CV first via POST /applications/{id}/cv"
            )
        
        # 3. Intentar extraer texto
        try:
            cv_text = self.cv_text_extractor.extract_text(application.cv_storage_key)
            
            # 4. Actualizar aplicación con éxito
            application.cv_text = cv_text
            application.cv_processing_status = "processed"
            application.cv_processed_at = datetime.utcnow()
            application.cv_processing_error = None
            
            logger.info(f"Successfully processed CV for {application_id}")
        
        except (ValueError, IOError) as e:
            # 5. Actualizar aplicación con error
            logger.error(f"Failed to process CV for {application_id}: {e}")
            application.cv_processing_status = "failed"
            application.cv_processing_error = str(e)
            application.cv_processed_at = datetime.utcnow()
            
            # Guardar estado de error
            self.application_repository.update(application)
            
            raise ValueError(f"CV processing failed: {e}")
        
        # 6. Guardar cambios
        updated_application = self.application_repository.update(application)
        return updated_application
