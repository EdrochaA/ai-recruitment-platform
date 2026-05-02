from app.domain.ports.job_application_repository import JobApplicationRepository
from app.domain.ports.job_offer_repository import JobOfferRepository
from app.domain.ports.cv_analyzer import CVAnalyzer
from app.domain.entities.job_application import JobApplication


class AnalyzeApplicationCV:
    """Caso de uso para analizar el CV de una candidatura.
    
    Orquesta la extracción de texto del CV y su análisis inteligente,
    actualizando el estado de la candidatura con los resultados.
    """

    def __init__(
        self,
        job_application_repository: JobApplicationRepository,
        job_offer_repository: JobOfferRepository,
        cv_analyzer: CVAnalyzer,
    ):
        self.job_application_repository = job_application_repository
        self.job_offer_repository = job_offer_repository
        self.cv_analyzer = cv_analyzer

    def execute(self, application_id: str) -> JobApplication:
        """Analiza el CV de una candidatura.
        
        Args:
            application_id: ID de la candidatura
            
        Returns:
            JobApplication actualizada con resultados del análisis
            
        Raises:
            ValueError: Si la candidatura no existe o no tiene CV procesado
        """
        # Buscar la candidatura
        job_application = self.job_application_repository.find_by_id(application_id)
        if not job_application:
            raise ValueError(f"JobApplication not found with id: {application_id}")

        # Validar que tiene CV procesado
        if not job_application.cv_text:
            raise ValueError(
                f"JobApplication {application_id} does not have processed CV text"
            )

        # Buscar la oferta de trabajo
        job_offer = self.job_offer_repository.find_by_id(job_application.job_offer_id)
        if not job_offer:
            raise ValueError(
                f"JobOffer not found with id: {job_application.job_offer_id}"
            )

        # Marcar como analizando
        job_application.cv_analysis_status = "analyzing"

        try:
            # Analizar el CV
            analysis_result = self.cv_analyzer.analyze(
                cv_text=job_application.cv_text,
                job_description=job_offer.description,
            )

            # Actualizar candidatura con resultados
            job_application.cv_analysis_status = "completed"
            job_application.cv_analysis_score = analysis_result.score
            job_application.cv_analysis_summary = analysis_result.summary
            job_application.cv_analysis_skills = analysis_result.skills
            job_application.cv_analysis_experience = analysis_result.experience_summary
            job_application.cv_analyzed_at = analysis_result.analyzed_at
            job_application.cv_analysis_error = None

        except Exception as e:
            # Marcar como fallido
            job_application.cv_analysis_status = "failed"
            job_application.cv_analysis_error = str(e)
            raise

        finally:
            # Guardar cambios
            self.job_application_repository.update(job_application)

        return job_application
