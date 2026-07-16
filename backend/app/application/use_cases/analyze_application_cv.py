from app.domain.ports.job_application_repository import JobApplicationRepository
from app.domain.ports.job_offer_repository import JobOfferRepository
from app.domain.ports.cv_analyzer import CVAnalyzer
from app.domain.entities.job_application import JobApplication
from app.application.use_cases.process_application_cv import ProcessApplicationCV


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
        cv_processor: ProcessApplicationCV,
    ):
        self.job_application_repository = job_application_repository
        self.job_offer_repository = job_offer_repository
        self.cv_analyzer = cv_analyzer
        self.cv_processor = cv_processor

    def execute(self, application_id: str) -> JobApplication:
        """Analiza el CV de una candidatura.

        Args:
            application_id: ID de la candidatura

        Returns:
            JobApplication actualizada con resultados del análisis

        Raises:
            ValueError: Si la candidatura no existe o no tiene CV procesado
        """
        # Procesar CV y recuperar la candidatura actualizada
        job_application = self.cv_processor.execute(application_id)

        # Buscar la oferta de trabajo
        job_offer = self.job_offer_repository.find_by_id(job_application.job_offer_id)
        if not job_offer:
            raise ValueError(
                f"JobOffer not found with id: {job_application.job_offer_id}"
            )

        # Validar que tiene texto procesado
        if not job_application.cv_text:
            raise ValueError(
                f"JobApplication {application_id} does not have processed CV text"
            )

        # Marcar como analizando
        job_application.cv_analysis_status = "analyzing"

        try:
            # Analizar el CV
            prompt = (
                "Analiza el siguiente CV y devuelve unicamente JSON valido con la "
                "siguiente estructura: {"
                "\"candidate_name\":\"\","
                "\"professional_summary\":\"\","
                "\"education\":[],"
                "\"work_experience\":[],"
                "\"technical_skills\":[],"
                "\"soft_skills\":[],"
                "\"languages\":[],"
                "\"certifications\":[],"
                "\"warnings\":[]"
                "}. No inventes datos. Si falta informacion usa arrays vacios o "
                "strings vacios."
                f"\n\nDescripcion del puesto:\n{job_offer.description}"
            )

            analysis_result = self.cv_analyzer.analyze(
                cv_text=job_application.cv_text,
                job_description=job_offer.description,
                application_id=application_id,
                job_offer_id=job_application.job_offer_id,
                prompt=prompt,
            )

            # Actualizar candidatura con resultados
            job_application.cv_analysis_status = "completed"
            job_application.cv_analysis_score = None
            job_application.cv_analysis_summary = analysis_result.professional_summary
            job_application.cv_analysis_skills = analysis_result.technical_skills
            job_application.cv_analysis_experience = "\n".join(
                analysis_result.work_experience
            )
            job_application.cv_analysis_candidate_name = analysis_result.candidate_name
            job_application.cv_analysis_education = analysis_result.education
            job_application.cv_analysis_work_experience = analysis_result.work_experience
            job_application.cv_analysis_technical_skills = (
                analysis_result.technical_skills
            )
            job_application.cv_analysis_soft_skills = analysis_result.soft_skills
            job_application.cv_analysis_languages = analysis_result.languages
            job_application.cv_analysis_certifications = analysis_result.certifications
            job_application.cv_analysis_warnings = analysis_result.warnings
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
