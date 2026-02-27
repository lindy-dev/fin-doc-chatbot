# CrewAI Agents Configuration

## Agent Architecture Overview

Using **hierarchical CrewAI pattern** with 5 specialized agents:
1. **Manager Agent** - Orchestrates workflow
2. **Fundamental Analysis Agent** - Financial statement analysis
3. **Technical Analysis Agent** - Chart patterns and indicators
4. **Risk Assessment Agent** - Risk identification
5. **Synthesizer Agent** - Combines all analyses

---

## Agent Definitions

### 1. Manager Agent

```python
# backend/app/crew_agents/manager_agent.py

from crewai import Agent
from typing import List, Dict, Any

manager_agent = Agent(
    role='Senior Financial Analysis Manager',
    goal='Orchestrate comprehensive financial document analysis by coordinating specialized analysts',
    backstory='''You are a seasoned financial analysis manager with 20+ years of experience 
    at top investment firms. You excel at breaking down complex analysis tasks, delegating 
    to specialists, and ensuring high-quality, actionable outputs. You understand the 
    strengths and limitations of each analyst type and how to sequence their work for 
    optimal results.''',
    
    verbose=True,
    allow_delegation=True,
    max_iterations=3,
    
    tools=[
        'document_parser',
        'company_lookup',
        'ticker_resolver',
        'metadata_extractor'
    ],
    
    llm_config={
        'model': 'gpt-4-turbo-preview',  # Or local Ollama model
        'temperature': 0.3,
        'max_tokens': 2000
    }
)
```

**Manager Task:**

```python
from crewai import Task

manager_task = Task(
    description='''
    Review the uploaded financial document and coordinate a comprehensive analysis:
    
    DOCUMENT INFO:
    - Filename: {filename}
    - Document Type: {doc_type}
    - Company: {company_name}
    - Ticker: {ticker_symbol}
    - Fiscal Period: {fiscal_period}
    
    YOUR RESPONSIBILITIES:
    1. Parse and understand the document structure
    2. Identify the company and its ticker symbol if not provided
    3. Delegate to Fundamental Analysis Agent for financial health assessment
    4. Delegate to Technical Analysis Agent for market position analysis
    5. Delegate to Risk Analysis Agent for risk identification
    6. Collect outputs from all agents
    7. Delegate to Synthesizer Agent for final investment recommendation
    
    CONSTRAINTS:
    - Ensure each agent has complete context
    - Verify outputs are actionable and quantitative
    - Flag any conflicting findings between agents
    ''',
    
    expected_output='''
    A comprehensive investment analysis report with:
    - Executive summary (2-3 paragraphs)
    - Fundamental score (A-F scale)
    - Technical score (A-F scale)  
    - Risk score (1-10, 10 = highest risk)
    - Buy/Hold/Sell recommendation with confidence level
    - Key metrics dashboard
    - Alert flags (if any)
    ''',
    
    agent=manager_agent,
    output_json=True
)
```

---

### 2. Fundamental Analysis Agent

```python
# backend/app/crew_agents/fundamental_agent.py

from crewai import Agent

fundamental_agent = Agent(
    role='Fundamental Analyst',
    goal='Deep dive into financial statements to assess company health, profitability, and growth prospects',
    backstory='''You are a CFA charterholder with expertise in financial statement analysis. 
    You excel at parsing 10-K, 10-Q reports, extracting key financial metrics, and assessing 
    business quality. You use ratios, trends, and industry comparisons to form investment opinions.''',
    
    verbose=True,
    allow_delegation=False,
    
    tools=[
        'financial_statement_parser',
        'ratio_calculator',
        'growth_analyzer',
        'industry_comparator',
        'yahoo_finance_fundamentals'
    ],
    
    llm_config={
        'model': 'gpt-4-turbo-preview',
        'temperature': 0.2,
        'max_tokens': 3000
    }
)
```

**Fundamental Task:**

```python
fundamental_task = Task(
    description='''
    Analyze the financial fundamentals of {company_name} ({ticker_symbol}):
    
    INPUT DATA:
    - Document: {document_path}
    - Document Type: {doc_type}
    - Fiscal Period: {fiscal_period}
    - Extracted Financials: {financial_highlights}
    
    ANALYSIS REQUIREMENTS:
    
    1. REVENUE & GROWTH
    - Revenue trends (YoY, QoQ)
    - Revenue composition by segment
    - Growth rate vs industry average
    
    2. PROFITABILITY
    - Gross margin trend
    - Operating margin
    - Net margin
    - ROE, ROA, ROIC
    - Compare to industry benchmarks
    
    3. BALANCE SHEET STRENGTH
    - Current ratio
    - Debt-to-equity ratio
    - Interest coverage
    - Cash position
    - Working capital trends
    
    4. CASH FLOW QUALITY
    - Operating cash flow trend
    - Free cash flow
    - Cash conversion cycle
    - Capital expenditure needs
    
    5. VALUATION METRICS (if available)
    - P/E ratio
    - P/B ratio
    - EV/EBITDA
    - Compare to historical and industry
    
    OUTPUT FORMAT:
    {
        "overall_score": "A|B|C|D|F",
        "score_rationale": "explanation",
        "revenue_analysis": {
            "trend": "positive|negative|stable",
            "growth_rate": "X%",
            "assessment": "detailed commentary"
        },
        "profitability_analysis": {
            "gross_margin": "XX%",
            "operating_margin": "XX%",
            "net_margin": "XX%",
            "trend": "improving|declining|stable",
            "assessment": "commentary"
        },
        "balance_sheet_analysis": {
            "liquidity": "strong|adequate|weak",
            "leverage": "conservative|moderate|high",
            "assessment": "commentary"
        },
        "cash_flow_analysis": {
            "quality": "high|medium|low",
            "fcf_trend": "positive|negative",
            "assessment": "commentary"
        },
        "key_strengths": ["strength 1", "strength 2"],
        "key_concerns": ["concern 1", "concern 2"],
        "red_flags": ["flag 1"] or []
    }
    ''',
    
    expected_output='Structured JSON with fundamental scores and detailed analysis',
    agent=fundamental_agent,
    output_json=True
)
```

---

### 3. Technical Analysis Agent

```python
# backend/app/crew_agents/technical_agent.py

from crewai import Agent

technical_agent = Agent(
    role='Technical Analyst',
    goal='Analyze price action, trends, and technical indicators to assess market timing and momentum',
    backstory='''You are a CMT (Chartered Market Technician) with expertise in chart analysis, 
    technical indicators, and market psychology. You combine price action analysis with volume 
    patterns to identify entry/exit points and trend strength.''',
    
    verbose=True,
    allow_delegation=False,
    
    tools=[
        'price_data_fetcher',
        'chart_pattern_recognizer',
        'indicator_calculator',
        'volume_analyzer',
        'support_resistance_finder',
        'yahoo_finance_prices',
        'alpha_vantage_technical'
    ],
    
    llm_config={
        'model': 'gpt-4-turbo-preview',
        'temperature': 0.2,
        'max_tokens': 2500
    }
)
```

**Technical Task:**

```python
technical_task = Task(
    description='''
    Perform technical analysis for {ticker_symbol}:
    
    PRICE DATA:
    - Current Price: {current_price}
    - Timeframe: Daily, Weekly, Monthly charts
    - Lookback Period: 1 year minimum
    
    TECHNICAL ANALYSIS REQUIREMENTS:
    
    1. TREND ANALYSIS
    - Primary trend (bullish/bearish/sideways)
    - Trend strength (ADX)
    - Price position vs moving averages
    
    2. SUPPORT & RESISTANCE
    - Key support levels
    - Key resistance levels
    - Recent breakouts or breakdowns
    
    3. MOMENTUM INDICATORS
    - RSI (14-period)
    - MACD signal
    - Stochastic oscillator
    - Momentum interpretation
    
    4. VOLUME ANALYSIS
    - Volume trends
    - Volume on up/down days
    - Confirmation/divergence with price
    
    5. CHART PATTERNS
    - Identify any classic patterns
    - Pattern completion status
    - Measured moves if applicable
    
    6. MOVING AVERAGES
    - 20-day EMA
    - 50-day SMA
    - 200-day SMA
    - Golden/Death cross status
    
    OUTPUT FORMAT:
    {
        "overall_score": "A|B|C|D|F",
        "trend": "bullish|bearish|neutral",
        "trend_strength": "strong|moderate|weak",
        "current_price": XX.XX,
        "key_levels": {
            "support": [170.00, 165.00],
            "resistance": [185.00, 195.00]
        },
        "indicators": {
            "rsi": XX,
            "rsi_interpretation": "overbought|oversold|neutral",
            "macd": "bullish|bearish|neutral",
            "stochastic": "overbought|oversold|neutral"
        },
        "moving_averages": {
            "price_vs_20ema": "above|below",
            "price_vs_50sma": "above|below",
            "price_vs_200sma": "above|below",
            "ma_alignment": "bullish|bearish|mixed"
        },
        "volume": {
            "trend": "increasing|decreasing|stable",
            "confirmation": "confirming|diverging"
        },
        "patterns": ["pattern 1", "pattern 2"] or [],
        "entry_suggestions": {
            "ideal_entry": XX.XX,
            "stop_loss": XX.XX,
            "target": XX.XX
        },
        "assessment": "detailed commentary on technical health"
    }
    ''',
    
    expected_output='Structured JSON with technical scores and indicator values',
    agent=technical_agent,
    output_json=True
)
```

---

### 4. Risk Assessment Agent

```python
# backend/app/crew_agents/risk_agent.py

from crewai import Agent

risk_agent = Agent(
    role='Risk Analyst',
    goal='Identify and quantify investment risks across market, credit, operational, and regulatory dimensions',
    backstory='''You are a risk management professional with FRM (Financial Risk Manager) certification. 
    You specialize in identifying hidden risks, stress testing, and scenario analysis. You maintain 
    a skeptical perspective and excel at finding what could go wrong.''',
    
    verbose=True,
    allow_delegation=False,
    
    tools=[
        'risk_scoring_model',
        'volatility_calculator',
        'beta_fetcher',
        'news_sentiment_analyzer',
        'sec_filing_checker',
        'yahoo_finance_risk_metrics'
    ],
    
    llm_config={
        'model': 'gpt-4-turbo-preview',
        'temperature': 0.3,
        'max_tokens': 2500
    }
)
```

**Risk Task:**

```python
risk_task = Task(
    description='''
    Conduct comprehensive risk assessment for {company_name} ({ticker_symbol}):
    
    RISK ANALYSIS FRAMEWORK:
    
    1. MARKET RISK
    - Beta coefficient (systematic risk)
    - Historical volatility (standard deviation)
    - Maximum drawdown in last 2 years
    - Correlation with broader market
    - Sector concentration risk
    
    2. CREDIT/FINANCIAL RISK
    - Credit rating (S&P, Moody's, Fitch if available)
    - Debt maturity profile
    - Interest rate sensitivity
    - Refinancing risk
    - Liquidity position
    
    3. OPERATIONAL RISK
    - Supply chain dependencies
    - Key person dependencies
    - Geopolitical exposure
    - Technology disruption risk
    
    4. REGULATORY/LEGAL RISK
    - Pending litigation
    - Regulatory investigations
    - Industry-specific regulations
    - Tax/audit risks
    
    5. BUSINESS MODEL RISK
    - Customer concentration
    - Product cycle maturity
    - Competition intensity
    - Pricing power
    
    6. ESG RISKS (if material)
    - Environmental liabilities
    - Social controversies
    - Governance concerns
    
    DOCUMENT RED FLAGS CHECKLIST:
    - Going concern warnings
    - Material weakness in controls
    - Related party transactions
    - Auditor changes
    - Restatements
    - Whistleblower mentions
    
    OUTPUT FORMAT:
    {
        "overall_risk_score": 1-10,
        "risk_level": "low|moderate|high|very_high",
        "risk_categories": {
            "market_risk": {
                "score": 1-10,
                "beta": X.XX,
                "volatility": "XX%",
                "assessment": "commentary"
            },
            "financial_risk": {
                "score": 1-10,
                "credit_rating": "AA|A|BBB|etc",
                "debt_concern": "low|moderate|high",
                "liquidity_risk": "low|moderate|high"
            },
            "operational_risk": {
                "score": 1-10,
                "key_risks": ["risk 1", "risk 2"],
                "assessment": "commentary"
            },
            "regulatory_risk": {
                "score": 1-10,
                "active_investigations": boolean,
                "key_issues": ["issue 1"] or []
            }
        },
        "red_flags": [
            {"flag": "description", "severity": "high|medium|low"}
        ] or [],
        "warning_signs": [
            {"sign": "description", "monitor": true}
        ] or [],
        "mitigating_factors": [
            "factor 1", "factor 2"
        ],
        "recommendation": "proceed_with_caution|monitor_closely|avoid|standard_due_diligence"
    }
    ''',
    
    expected_output='Structured JSON with risk scores and detailed breakdown',
    agent=risk_agent,
    output_json=True
)
```

---

### 5. Synthesizer Agent

```python
# backend/app/crew_agents/synthesizer_agent.py

from crewai import Agent

synthesizer_agent = Agent(
    role='Investment Strategist',
    goal='Synthesize multi-dimensional analysis into actionable investment recommendation',
    backstory='''You are a senior portfolio manager with experience across asset classes and 
    investment strategies. You excel at weighing conflicting signals, assessing risk/reward 
    tradeoffs, and making clear buy/hold/sell recommendations. You communicate complex 
    analysis in accessible terms while maintaining analytical rigor.''',
    
    verbose=True,
    allow_delegation=False,
    
    tools=[
        'portfolio_simulator',
        'scenario_analyzer',
        'valuation_model_calculator'
    ],
    
    llm_config={
        'model': 'gpt-4-turbo-preview',
        'temperature': 0.25,
        'max_tokens': 3500
    }
)
```

**Synthesizer Task:**

```python
synthesizer_task = Task(
    description='''
    Synthesize all analysis inputs into final investment recommendation:
    
    INPUT DATA:
    
    FUNDAMENTAL ANALYSIS:
    {fundamental_analysis}
    
    TECHNICAL ANALYSIS:
    {technical_analysis}
    
    RISK ANALYSIS:
    {risk_analysis}
    
    SYNTHESIS REQUIREMENTS:
    
    1. INTEGRATE FINDINGS
    - Identify areas of agreement/disagreement between analysts
    - Resolve conflicts or note them as uncertainties
    - Weight fundamental vs technical based on investment horizon
    
    2. INVESTMENT THESIS
    - Core bull case (why buy)
    - Core bear case (why avoid)
    - Key assumptions
    - What would change the thesis
    
    3. VALUATION ASSESSMENT
    - Is current price attractive?
    - What is fair value range?
    - Margin of safety assessment
    
    4. RISK/REWARD EVALUATION
    - Upside potential (%)
    - Downside risk (%)
    - Probability-weighted expected return
    - Position sizing suggestion (if applicable)
    
    5. FINAL RECOMMENDATION
    - Action: BUY | HOLD | SELL | WATCH
    - Confidence level: 0-100%
    - Time horizon: short_term | medium_term | long_term
    - Target price (if applicable)
    - Stop loss suggestion (if applicable)
    
    6. KEY METRICS SUMMARY
    - Fundamental Score: X/10
    - Technical Score: X/10
    - Risk Score: X/10
    - Overall Composite Score
    
    7. EXECUTIVE SUMMARY
    - 2-3 paragraph summary for busy investors
    - Highlight most important points
    - Call to action
    
    8. ALERT FLAGS (if any)
    - Immediate attention items
    - Ongoing monitoring points
    
    OUTPUT FORMAT:
    {
        "executive_summary": "2-3 paragraphs",
        "investment_thesis": {
            "bull_case": "description",
            "bear_case": "description",
            "key_assumptions": ["assumption 1", "assumption 2"],
            "thesis_change_triggers": ["trigger 1", "trigger 2"]
        },
        "recommendation": {
            "action": "buy|hold|sell|watch",
            "confidence": XX,
            "time_horizon": "short|medium|long",
            "target_price": XX.XX,
            "stop_loss": XX.XX,
            "position_size_suggestion": "full|half|quarter|speculative"
        },
        "scoring": {
            "fundamental_score": "A|B|C|D|F",
            "fundamental_numeric": X,
            "technical_score": "A|B|C|D|F",
            "technical_numeric": X,
            "risk_score": 1-10,
            "composite_score": X.XX
        },
        "risk_reward": {
            "upside_potential": "XX%",
            "downside_risk": "XX%",
            "expected_return": "XX%",
            "risk_reward_ratio": "X:1"
        },
        "key_metrics": {
            "current_price": XX.XX,
            "fair_value_range": {"low": XX.XX, "high": XX.XX},
            "margin_of_safety": "XX%"
        },
        "alert_flags": [
            {"flag": "description", "severity": "high|medium|low"}
        ] or [],
        "monitoring_points": [
            "point 1", "point 2"
        ]
    }
    ''',
    
    expected_output='Comprehensive synthesis with clear recommendation and rationale',
    agent=synthesizer_agent,
    output_json=True
)
```

---

## Crew Orchestration

```python
# backend/app/crew_agents/crew_orchestrator.py

from crewai import Crew, Process
from .manager_agent import manager_agent, manager_task
from .fundamental_agent import fundamental_agent, fundamental_task
from .technical_agent import technical_agent, technical_task
from .risk_agent import risk_agent, risk_task
from .synthesizer_agent import synthesizer_agent, synthesizer_task

class FinancialAnalysisCrew:
    def __init__(self, document_info: dict):
        self.document_info = document_info
        
        # Create crew with hierarchical process
        self.crew = Crew(
            agents=[
                manager_agent,
                fundamental_agent,
                technical_agent,
                risk_agent,
                synthesizer_agent
            ],
            tasks=[
                manager_task,
                fundamental_task,
                technical_task,
                risk_task,
                synthesizer_task
            ],
            process=Process.hierarchical,
            manager=manager_agent,
            verbose=True,
            memory=True,  # Enable memory for context retention
            cache=True,   # Enable caching for tool results
            max_rpm=100,  # Rate limit for API calls
        )
    
    def run_analysis(self) -> dict:
        """Execute the full analysis workflow."""
        
        # Prepare context
        context = {
            'filename': self.document_info['filename'],
            'doc_type': self.document_info['doc_type'],
            'company_name': self.document_info['company_name'],
            'ticker_symbol': self.document_info['ticker_symbol'],
            'fiscal_period': self.document_info['fiscal_period'],
            'document_path': self.document_info['file_path'],
            'financial_highlights': self.document_info.get('financial_highlights', {}),
            'current_price': self.document_info.get('current_price'),
        }
        
        # Run crew
        result = self.crew.kickoff(inputs=context)
        
        return {
            'raw_output': result,
            'structured_results': self._parse_results(result)
        }
    
    def _parse_results(self, raw_output: str) -> dict:
        """Parse crew output into structured format."""
        # Implementation depends on CrewAI version
        # Typically involves JSON parsing from agent outputs
        pass

# Usage
async def analyze_document(document_id: str, db_session):
    # Fetch document info
    doc = await get_document(document_id, db_session)
    
    # Create and run crew
    crew = FinancialAnalysisCrew(doc)
    results = crew.run_analysis()
    
    # Store results
    await store_analysis_results(document_id, results, db_session)
    
    return results
```

---

## Agent Tools

```python
# backend/app/crew_agents/tools.py

from crewai_tools import BaseTool
from typing import Type, Any
import yfinance as yf
import requests

class YahooFinanceTool(BaseTool):
    name: str = "yahoo_finance"
    description: str = "Fetch stock data from Yahoo Finance"
    
    def _run(self, ticker: str, metric: str) -> str:
        stock = yf.Ticker(ticker)
        
        if metric == "info":
            return str(stock.info)
        elif metric == "history":
            hist = stock.history(period="1y")
            return hist.to_string()
        elif metric == "financials":
            return str(stock.financials)
        elif metric == "balance_sheet":
            return str(stock.balance_sheet)
        elif metric == "cash_flow":
            return str(stock.cashflow)
        
        return f"Unknown metric: {metric}"

class AlphaVantageTool(BaseTool):
    name: str = "alpha_vantage"
    description: str = "Fetch technical indicators from Alpha Vantage"
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        super().__init__()
    
    def _run(self, symbol: str, function: str) -> str:
        url = f"https://www.alphavantage.co/query"
        params = {
            "function": function,
            "symbol": symbol,
            "apikey": self.api_key
        }
        
        response = requests.get(url, params=params)
        return response.text

class DocumentParserTool(BaseTool):
    name: str = "document_parser"
    description: str = "Parse financial document and extract text and tables"
    
    def _run(self, file_path: str) -> str:
        # Use pdfplumber or similar
        import pdfplumber
        
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
        
        return text

# Tool registry
TOOLS = {
    'yahoo_finance': YahooFinanceTool,
    'alpha_vantage': AlphaVantageTool,
    'document_parser': DocumentParserTool,
}
```

---

## Execution Flow with Progress Tracking

```python
# backend/app/crew_agents/progress_tracker.py

import asyncio
from typing import Callable

class AnalysisProgressTracker:
    def __init__(self, websocket_callback: Callable):
        self.websocket_callback = websocket_callback
        self.current_step = 0
        self.total_steps = 5
    
    async def on_agent_start(self, agent_name: str):
        self.current_step += 1
        progress = (self.current_step / self.total_steps) * 100
        
        await self.websocket_callback({
            'type': 'agent_start',
            'agent': agent_name,
            'progress': progress,
            'step': self.current_step,
            'total_steps': self.total_steps
        })
    
    async def on_agent_complete(self, agent_name: str, output: dict):
        await self.websocket_callback({
            'type': 'agent_complete',
            'agent': agent_name,
            'output_summary': self._summarize_output(output)
        })
    
    async def on_tool_use(self, tool_name: str, input_params: dict):
        await self.websocket_callback({
            'type': 'tool_use',
            'tool': tool_name,
            'params': input_params
        })
    
    def _summarize_output(self, output: dict) -> str:
        # Create human-readable summary
        if 'score' in output:
            return f"Score: {output['score']}"
        return "Analysis complete"

# Integration with FastAPI WebSocket
async def analyze_with_progress(document_id: str, websocket):
    tracker = AnalysisProgressTracker(
        websocket_callback=websocket.send_json
    )
    
    # Wrap agents with progress tracking
    crew = FinancialAnalysisCrewWithTracking(
        document_info=doc,
        progress_tracker=tracker
    )
    
    results = await crew.run_analysis()
    return results
```

---

## Configuration Summary

| Agent | Model | Temperature | Tokens | Tools |
|-------|-------|-------------|--------|-------|
| Manager | gpt-4-turbo | 0.3 | 2000 | 4 |
| Fundamental | gpt-4-turbo | 0.2 | 3000 | 5 |
| Technical | gpt-4-turbo | 0.2 | 2500 | 6 |
| Risk | gpt-4-turbo | 0.3 | 2500 | 6 |
| Synthesizer | gpt-4-turbo | 0.25 | 3500 | 3 |

**Total expected cost per analysis:** ~$0.50-1.50 (depending on document length)

---

## Local LLM Alternative (Ollama)

```python
# For privacy and cost savings

ollama_config = {
    'model': 'ollama/llama2:70b',  # Or mixtral, codellama
    'base_url': 'http://localhost:11434',
    'temperature': 0.2,
    'max_tokens': 4000
}

# Use Ollama for all agents
for agent in [manager_agent, fundamental_agent, technical_agent, risk_agent, synthesizer_agent]:
    agent.llm_config = ollama_config
```

**Note:** Local models may require larger context windows and may have lower accuracy for financial analysis.

---

## Next Steps

1. **Set up API keys** for OpenAI or Ollama
2. **Implement custom tools** for document parsing
3. **Test agent interactions** with sample documents
4. **Tune prompts** based on output quality
5. **Add caching** for tool results
6. **Implement progress tracking** via WebSocket

**Ready to implement?** See `/docs/API.md` for FastAPI integration! 🚀
