"""CrewAI task definitions for financial analysis."""

from typing import Callable, Optional

from crewai import Task

from app.crew.agents import (
    create_data_analyst_agent,
    create_financial_advisor_agent,
    create_risk_assessor_agent,
)


def create_data_analysis_task(
    query: str,
    context: str = "",
    step_callback: Optional[Callable[[object], None]] = None,
) -> Task:
    """Create task for data analysis."""
    agent = create_data_analyst_agent(step_callback=step_callback)
    context_str = f"\nAdditional Context: {context}" if context else ""

    return Task(
        description=f"""Analyze the following financial query and extract all relevant numerical data,
        metrics, and financial indicators mentioned or implied:

        Query: {query}{context_str}

        Your analysis should include:
        1. Key financial metrics and KPIs identified
        2. Numerical calculations and trends
        3. Data quality assessment
        4. Any missing data points that would be helpful

        Provide a structured analysis with specific numbers and calculations where applicable.""",
        expected_output="""A structured data analysis report containing:
        - Identified financial metrics and their values
        - Calculations performed
        - Trends observed
        - Data gaps or limitations noted""",
        agent=agent,
    )


def create_advisory_task(
    query: str,
    step_callback: Optional[Callable[[object], None]] = None,
) -> Task:
    """Create task for financial advisory."""
    agent = create_financial_advisor_agent(step_callback=step_callback)

    return Task(
        description=f"""Based on the original query and the prior data analysis context,
        provide comprehensive financial advice and investment recommendations:

        Original Query: {query}

        Your recommendations should include:
        1. Strategic financial advice tailored to the query
        2. Specific investment recommendations if applicable
        3. Portfolio considerations
        4. Actionable next steps
        5. Long-term financial planning insights

        Consider risk tolerance, market conditions, and diversification in your advice.""",
        expected_output="""Comprehensive financial advisory report containing:
        - Strategic recommendations
        - Investment suggestions with rationale
        - Portfolio guidance
        - Actionable next steps
        - Long-term considerations""",
        agent=agent,
    )


def create_risk_assessment_task(
    query: str,
    step_callback: Optional[Callable[[object], None]] = None,
) -> Task:
    """Create task for risk assessment."""
    agent = create_risk_assessor_agent(step_callback=step_callback)

    return Task(
        description=f"""Assess the financial risks associated with the original query,
        using the prior data analysis and advisory context:

        Original Query: {query}

        Your risk assessment should include:
        1. Market risks and volatility considerations
        2. Credit and liquidity risks
        3. Operational and regulatory risks
        4. Risk quantification (low/medium/high) with justification
        5. Risk mitigation strategies
        6. Warning signs to monitor

        Provide a balanced view of potential risks without being overly conservative.""",
        expected_output="""Comprehensive risk assessment report containing:
        - Identified risks by category
        - Risk severity ratings with justification
        - Mitigation strategies
        - Monitoring recommendations
        - Overall risk summary""",
        agent=agent,
    )


def create_final_synthesis_task(
    query: str,
    step_callback: Optional[Callable[[object], None]] = None,
) -> Task:
    """Create task for final synthesis."""
    agent = create_financial_advisor_agent(step_callback=step_callback)

    return Task(
        description=f"""Synthesize the prior analyses into a comprehensive, coherent response
        to the original query. The response should be well-structured and actionable:

        Original Query: {query}

        Create a final response that:
        1. Directly addresses the original query
        2. Integrates insights from all three analyses
        3. Provides clear, actionable recommendations
        4. Includes appropriate risk warnings
        5. Is written in a professional yet accessible tone
        6. Has a logical flow from analysis to recommendation to risk consideration

        The response should be comprehensive but concise, suitable for a knowledgeable
        but non-expert audience.""",
        expected_output="""A comprehensive, well-structured response that synthesizes all
        analyses into actionable financial advice with appropriate risk considerations.
        The response should be professional, clear, and directly address the original query.""",
        agent=agent,
    )
