"""CrewAI crew assembly and execution."""

import asyncio
from typing import Callable, Optional

from crewai import Crew, Process

from app.config import get_settings
from app.crew.tasks import (
    create_advisory_task,
    create_data_analysis_task,
    create_final_synthesis_task,
    create_risk_assessment_task,
)

settings = get_settings()


class FinancialAnalysisCrew:
    """Crew for financial document analysis."""

    def __init__(self) -> None:
        self.crew: Optional[Crew] = None

    def _create_crew(self, query: str, context: str = "") -> Crew:
        """Create the crew with tasks for the query."""
        # Create tasks
        data_task = create_data_analysis_task(query, context)
        advisory_task = create_advisory_task(query)
        risk_task = create_risk_assessment_task(query)
        synthesis_task = create_final_synthesis_task(query)

        # Create crew with sequential process
        return Crew(
            agents=[
                data_task.agent,
                advisory_task.agent,
                risk_task.agent,
            ],
            tasks=[
                data_task,
                advisory_task,
                risk_task,
                synthesis_task,
            ],
            process=Process.sequential,
            verbose=settings.crewai_verbose,
        )

    async def analyze(
        self,
        query: str,
        context: str = "",
        progress_callback: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Run financial analysis with the crew.

        Args:
            query: The financial query to analyze
            context: Additional context for the query
            progress_callback: Optional callback for progress updates

        Returns:
            The final analysis result
        """
        if progress_callback:
            progress_callback("Initializing analysis crew...")

        # Create crew
        crew = self._create_crew(query, context)

        if progress_callback:
            progress_callback("Starting data analysis...")

        # Run crew (this is synchronous, so we run in thread pool)
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, crew.kickoff)

        if progress_callback:
            progress_callback("Analysis complete")

        return str(result)


# Global crew instance
_financial_crew: Optional[FinancialAnalysisCrew] = None


def get_financial_crew() -> FinancialAnalysisCrew:
    """Get or create the financial analysis crew."""
    global _financial_crew
    if _financial_crew is None:
        _financial_crew = FinancialAnalysisCrew()
    return _financial_crew
