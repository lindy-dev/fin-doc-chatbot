"""CrewAI agent definitions for financial analysis."""

from typing import Callable, Optional

from crewai import Agent

from app.config import get_settings

settings = get_settings()
DEFAULT_LLM = settings.openai_model



def create_data_analyst_agent(
    step_callback: Optional[Callable[[object], None]] = None,
) -> Agent:
    """Create the Data Analyst agent."""
    return Agent(
        role="Financial Data Analyst",
        goal="Extract, analyze, and interpret numerical financial data from queries and provide accurate calculations and trend analysis",
        backstory="""You are an expert financial data analyst with deep expertise in interpreting 
        financial statements, market data, and economic indicators. You excel at extracting 
        meaningful insights from numerical data, performing calculations, and identifying 
        trends in financial metrics. You provide precise, data-driven analysis.""",
        llm=DEFAULT_LLM,
        function_calling_llm=None,
        verbose=settings.crewai_verbose,
        allow_delegation=False,
        max_iter=20,
        max_rpm=None,
        max_execution_time=None,
        max_retry_limit=2,
        allow_code_execution=False,
        code_execution_mode="safe",
        respect_context_window=True,
        use_system_prompt=True,
        multimodal=False,
        inject_date=False,
        date_format="%Y-%m-%d",
        reasoning=False,
        max_reasoning_attempts=None,
        knowledge_sources=None,
        embedder=None,
        system_template=None,
        prompt_template=None,
        response_template=None,
        step_callback=step_callback,
    )


def create_financial_advisor_agent(
    step_callback: Optional[Callable[[object], None]] = None,
) -> Agent:
    """Create the Financial Advisor agent."""
    return Agent(
        role="Senior Financial Advisor",
        goal="Provide actionable investment recommendations and strategic financial advice based on analysis",
        backstory="""You are a seasoned financial advisor with 20+ years of experience in 
        investment strategy, portfolio management, and wealth planning. You specialize in 
        translating complex financial analysis into clear, actionable recommendations. You 
        consider risk tolerance, market conditions, and long-term financial goals in your advice.""",
        llm=DEFAULT_LLM,
        function_calling_llm=None,
        verbose=settings.crewai_verbose,
        allow_delegation=False,
        max_iter=20,
        max_rpm=None,
        max_execution_time=None,
        max_retry_limit=2,
        allow_code_execution=False,
        code_execution_mode="safe",
        respect_context_window=True,
        use_system_prompt=True,
        multimodal=False,
        inject_date=False,
        date_format="%Y-%m-%d",
        reasoning=False,
        max_reasoning_attempts=None,
        knowledge_sources=None,
        embedder=None,
        system_template=None,
        prompt_template=None,
        response_template=None,
        step_callback=step_callback,
    )


def create_risk_assessor_agent(
    step_callback: Optional[Callable[[object], None]] = None,
) -> Agent:
    """Create the Risk Assessor agent."""
    return Agent(
        role="Risk Assessment Specialist",
        goal="Identify, quantify, and communicate financial risks associated with investments and market conditions",
        backstory="""You are a risk management expert specializing in financial risk assessment. 
        You excel at identifying potential risks in investment strategies, quantifying their 
        impact, and providing risk mitigation recommendations. You analyze market volatility, 
        credit risk, liquidity risk, and operational risks with precision.""",
        llm=DEFAULT_LLM,
        function_calling_llm=None,
        verbose=settings.crewai_verbose,
        allow_delegation=False,
        max_iter=20,
        max_rpm=None,
        max_execution_time=None,
        max_retry_limit=2,
        allow_code_execution=False,
        code_execution_mode="safe",
        respect_context_window=True,
        use_system_prompt=True,
        multimodal=False,
        inject_date=False,
        date_format="%Y-%m-%d",
        reasoning=False,
        max_reasoning_attempts=None,
        knowledge_sources=None,
        embedder=None,
        system_template=None,
        prompt_template=None,
        response_template=None,
        step_callback=step_callback,
    )
