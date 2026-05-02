import logging
from datetime import datetime
from app.domain.ports.cv_analyzer import CVAnalyzer
from app.domain.entities.cv_analysis import CVAnalysisResult

logger = logging.getLogger("cv-analysis")


class SimpleCVAnalyzer(CVAnalyzer):
    """Analizador simple de CVs basado en heurísticas.
    
    Implementación inicial sin dependencias externas.
    Detecta skills conocidas y calcula un score de compatibilidad
    con la descripción del puesto.
    
    Preparado para ser reemplazado por AgentCoreCVAnalyzer sin modificar
    el caso de uso ni el resto de la aplicación.
    """

    # Skills conocidas para detectar en CVs
    KNOWN_SKILLS = {
        "python",
        "fastapi",
        "sql",
        "postgresql",
        "docker",
        "aws",
        "java",
        "javascript",
        "react",
        "machine learning",
        "nlp",
        "git",
        "django",
        "rest api",
        "microservices",
        "kubernetes",
        "redis",
        "mongodb",
        "elasticsearch",
        "graphql",
        "nodejs",
        "typescript",
        "angular",
        "vue",
        "linux",
        "windows",
        "devops",
        "ci/cd",
        "agile",
        "scrum",
    }

    def analyze(self, cv_text: str, job_description: str) -> CVAnalysisResult:
        """Analiza un CV contra una descripción de puesto.
        
        Args:
            cv_text: Texto extraído del CV del candidato
            job_description: Descripción del puesto de trabajo
            
        Returns:
            CVAnalysisResult con skills detectadas, score y resumen
        """
        try:
            # Convertir a minúsculas para búsqueda insensible a mayúsculas
            cv_lower = cv_text.lower()
            job_lower = job_description.lower()

            # Detectar skills en el CV
            detected_skills = self._detect_skills(cv_lower)

            # Detectar skills requeridos en la descripción
            required_skills = self._detect_skills(job_lower)

            # Calcular score de compatibilidad
            score = self._calculate_score(detected_skills, required_skills)

            # Generar resumen
            experience_summary = self._extract_experience_summary(cv_text)
            summary = self._generate_summary(detected_skills, required_skills, score)

            logger.info(
                f"CV analyzed: {len(detected_skills)} skills detected, "
                f"score: {score}/100, "
                f"required skills match: {len(detected_skills & required_skills)}/{len(required_skills)}"
            )

            return CVAnalysisResult(
                skills=sorted(list(detected_skills)),
                experience_summary=experience_summary,
                score=score,
                summary=summary,
                analyzed_at=datetime.now(),
            )

        except Exception as e:
            logger.error(f"Error analyzing CV: {e}")
            raise ValueError(f"Failed to analyze CV: {e}")

    def _detect_skills(self, text: str) -> set[str]:
        """Detecta skills conocidas en un texto."""
        detected = set()
        text_lower = text.lower()

        for skill in self.KNOWN_SKILLS:
            # Buscar la skill como palabra completa o parte de palabras compuestas
            if skill in text_lower:
                detected.add(skill)

        return detected

    def _calculate_score(self, detected_skills: set[str], required_skills: set[str]) -> int:
        """Calcula un score de 0-100 basado en compatibilidad de skills.
        
        - 100: Candidato tiene todas las skills requeridas
        - 75: Candidato tiene 75% de skills requeridas
        - 50: Candidato tiene 50% de skills requeridas
        - 25: Candidato tiene 25% de skills requeridas
        - 0: Candidato no tiene ninguna skill requerida
        """
        if not required_skills:
            # Si no hay skills requeridas, score mínimo dependiendo de skills detectadas
            return min(50, len(detected_skills) * 5)

        matched_skills = detected_skills & required_skills
        match_percentage = len(matched_skills) / len(required_skills)

        # Escalar a 0-100
        base_score = int(match_percentage * 100)

        # Bonus por skills adicionales detectadas
        extra_skills = detected_skills - required_skills
        bonus = min(10, len(extra_skills) * 2)

        final_score = min(100, base_score + bonus)

        return final_score

    def _extract_experience_summary(self, cv_text: str) -> str:
        """Intenta extraer un resumen de experiencia del CV."""
        # Buscar patrones comunes de experiencia
        lines = cv_text.split("\n")

        # Buscar líneas que contengan palabras clave de experiencia
        experience_keywords = ["experience", "work", "employment", "position", "career"]
        experience_lines = []

        for i, line in enumerate(lines):
            line_lower = line.lower()
            if any(keyword in line_lower for keyword in experience_keywords):
                # Tomar esta línea y las siguientes (hasta 3)
                for j in range(i, min(i + 3, len(lines))):
                    if lines[j].strip():
                        experience_lines.append(lines[j].strip())

            if len(experience_lines) >= 100:  # Limitar a 100 caracteres
                break

        if experience_lines:
            return " ".join(experience_lines)[:200]
        else:
            # Si no encuentra sección de experiencia, tomar primeras líneas no vacías
            non_empty_lines = [line.strip() for line in lines if line.strip()]
            return " ".join(non_empty_lines[:3])[:200]

    def _generate_summary(
        self, detected_skills: set[str], required_skills: set[str], score: int
    ) -> str:
        """Genera un resumen del análisis."""
        matched_skills = detected_skills & required_skills
        missing_skills = required_skills - detected_skills

        parts = []

        # Score assessment
        if score >= 80:
            parts.append("Candidato muy compatible con el puesto.")
        elif score >= 60:
            parts.append("Candidato compatible con algunas áreas de mejora.")
        elif score >= 40:
            parts.append("Candidato parcialmente compatible.")
        else:
            parts.append("Candidato con bajo nivel de compatibilidad.")

        # Skills match
        if matched_skills:
            parts.append(f"Tiene {len(matched_skills)} de {len(required_skills)} skills requeridas.")
        else:
            parts.append(f"No contiene las skills requeridas para el puesto.")

        # Missing skills
        if missing_skills:
            missing_list = ", ".join(sorted(list(missing_skills))[:5])
            if len(missing_skills) > 5:
                missing_list += f", y {len(missing_skills) - 5} más"
            parts.append(f"Falta: {missing_list}.")

        # Extra skills
        extra_skills = detected_skills - required_skills
        if extra_skills and len(extra_skills) <= 5:
            extra_list = ", ".join(sorted(list(extra_skills))[:5])
            parts.append(f"Skills adicionales: {extra_list}.")

        return " ".join(parts)
