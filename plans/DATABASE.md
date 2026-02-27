# Database Schema - FinDocAnalyzer

## Overview

PostgreSQL schema for financial document analysis platform with user management, document storage, analysis results, and caching metadata.

---

## Entity Relationship Diagram

```
┌──────────────────┐       ┌──────────────────┐       ┌──────────────────┐
│      users       │       │   documents      │       │  analysis_jobs   │
├──────────────────┤       ├──────────────────┤       ├──────────────────┤
│ id (PK)          │◄──────┤ id (PK)          │◄──────┤ id (PK)          │
│ email            │       │ user_id (FK)     │       │ document_id (FK) │
│ hashed_password  │       │ filename         │       │ status           │
│ full_name        │       │ original_name    │       │ started_at       │
│ role             │       │ file_path        │       │ completed_at     │
│ is_active        │       │ file_size        │       │ results (JSON)   │
│ created_at       │       │ mime_type        │       │ fundamental_score│
│ updated_at       │       │ uploaded_at      │       │ technical_score  │
└──────────────────┘       │ expires_at       │       │ risk_score       │
                           │ status           │       │ recommendation   │
                           │ metadata (JSON)  │       │ created_at       │
                           └──────────────────┘       └──────────────────┘
                                    │                          │
                                    └──────────────────────────┘
                                                           │
                                    ┌──────────────────────┘
                                    │
                           ┌────────▼─────────┐
                           │ analysis_details │
                           ├──────────────────┤
                           │ id (PK)          │
                           │ job_id (FK)      │
                           │ agent_type       │
                           │ findings (JSON)│
                           │ raw_output       │
                           │ created_at       │
                           └──────────────────┘

┌──────────────────┐       ┌──────────────────┐
│   api_keys       │       │  system_logs     │
├──────────────────┤       ├──────────────────┤
│ id (PK)          │       │ id (PK)          │
│ user_id (FK)     │       │ level            │
│ key_hash         │       │ message          │
│ name             │       │ context (JSON) │
│ last_used_at     │       │ created_at       │
│ expires_at       │       └──────────────────┘
│ is_active        │
│ created_at       │
└──────────────────┘
```

---

## Table Definitions

### 1. Users Table

```sql
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    
    -- Role management
    role VARCHAR(50) DEFAULT 'user' CHECK (role IN ('user', 'admin')),
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    
    -- Profile
    preferences JSONB DEFAULT '{}',
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login_at TIMESTAMP WITH TIME ZONE,
    
    -- Indexes
    CONSTRAINT valid_email CHECK (email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
);

-- Indexes
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_active ON users(is_active);
```

### 2. Documents Table

```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- File info
    filename VARCHAR(500) NOT NULL,  -- Stored filename (UUID)
    original_name VARCHAR(500) NOT NULL,  -- Original filename
    file_path VARCHAR(1000) NOT NULL,
    file_size BIGINT NOT NULL CHECK (file_size <= 10485760),  -- Max 10MB
    mime_type VARCHAR(100),
    
    -- Document type classification
    doc_type VARCHAR(50) CHECK (doc_type IN (
        'annual_report',      -- 10-K
        'quarterly_report',   -- 10-Q
        'earnings_transcript',
        'presentation',
        'sec_filing',
        'bank_statement',
        'other'
    )),
    
    -- Company info (extracted from document)
    company_name VARCHAR(255),
    ticker_symbol VARCHAR(20),
    fiscal_year INTEGER,
    
    -- Metadata (extracted by parser)
    metadata JSONB DEFAULT '{}',
    
    -- Status
    status VARCHAR(50) DEFAULT 'uploaded' CHECK (status IN (
        'uploaded',
        'processing',
        'analyzed',
        'error',
        'expired'
    )),
    
    -- Expiration (auto-delete after 30 days)
    uploaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT (CURRENT_TIMESTAMP + INTERVAL '30 days'),
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Cache info
    redis_cache_key VARCHAR(255),
    cache_hits INTEGER DEFAULT 0
);

-- Indexes
CREATE INDEX idx_documents_user_id ON documents(user_id);
CREATE INDEX idx_documents_status ON documents(status);
CREATE INDEX idx_documents_expires ON documents(expires_at);
CREATE INDEX idx_documents_ticker ON documents(ticker_symbol);

-- Partial index for active documents
CREATE INDEX idx_documents_active ON documents(user_id, status) 
WHERE status IN ('uploaded', 'processing', 'analyzed');

-- GIN index for JSONB queries
CREATE INDEX idx_documents_metadata ON documents USING GIN(metadata);
```

### 3. Analysis Jobs Table

```sql
CREATE TABLE analysis_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Job status
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN (
        'pending',
        'running',
        'completed',
        'failed',
        'cancelled'
    )),
    
    -- Progress tracking
    progress_percent INTEGER DEFAULT 0 CHECK (progress_percent BETWEEN 0 AND 100),
    current_agent VARCHAR(100),
    
    -- Agent execution log
    agent_logs JSONB DEFAULT '[]',
    
    -- Timestamps
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    failed_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    
    -- Results (comprehensive JSON structure)
    results JSONB,
    
    -- Scores (extracted for querying)
    fundamental_score VARCHAR(2) CHECK (fundamental_score IN ('A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F')),
    technical_score VARCHAR(2) CHECK (technical_score IN ('A+', 'A', 'A-', 'B+', 'B', 'B-', 'C+', 'C', 'C-', 'D', 'F')),
    risk_score INTEGER CHECK (risk_score BETWEEN 1 AND 10),
    
    -- Recommendation
    recommendation VARCHAR(20) CHECK (recommendation IN ('buy', 'hold', 'sell', 'watch')),
    confidence_score DECIMAL(3,2) CHECK (confidence_score BETWEEN 0 AND 1),
    
    -- Key metrics summary
    key_metrics JSONB,
    
    -- Alert flags
    alert_flags JSONB DEFAULT '[]',
    
    -- Report generation
    report_generated BOOLEAN DEFAULT false,
    report_url VARCHAR(1000),
    
    -- Costs (if using external APIs)
    estimated_cost DECIMAL(10, 4),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_analysis_jobs_document ON analysis_jobs(document_id);
CREATE INDEX idx_analysis_jobs_user ON analysis_jobs(user_id);
CREATE INDEX idx_analysis_jobs_status ON analysis_jobs(status);
CREATE INDEX idx_analysis_jobs_completed ON analysis_jobs(completed_at);
CREATE INDEX idx_analysis_jobs_recommendation ON analysis_jobs(recommendation);
```

### 4. Analysis Details Table

```sql
CREATE TABLE analysis_details (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    job_id UUID NOT NULL REFERENCES analysis_jobs(id) ON DELETE CASCADE,
    
    -- Agent that produced this analysis
    agent_type VARCHAR(50) NOT NULL CHECK (agent_type IN (
        'manager',
        'fundamental',
        'technical',
        'risk',
        'synthesizer'
    )),
    
    -- Agent output
    findings JSONB NOT NULL,
    raw_output TEXT,  -- Full agent output for debugging
    
    -- Structured data extracted from findings
    key_points JSONB,
    metrics JSONB,
    charts_data JSONB,
    
    -- Execution metadata
    execution_time_ms INTEGER,
    tokens_used INTEGER,
    model_used VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_analysis_details_job ON analysis_details(job_id);
CREATE INDEX idx_analysis_details_agent ON analysis_details(agent_type);
```

### 5. API Keys Table (for service accounts)

```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    key_hash VARCHAR(255) NOT NULL UNIQUE,  -- Hashed key for storage
    name VARCHAR(255),  -- User-friendly name
    
    last_used_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    is_active BOOLEAN DEFAULT true,
    rate_limit_per_hour INTEGER DEFAULT 100,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_user ON api_keys(user_id);
CREATE INDEX idx_api_keys_hash ON api_keys(key_hash);
```

### 6. System Logs Table

```sql
CREATE TABLE system_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    
    level VARCHAR(20) NOT NULL CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    
    message TEXT NOT NULL,
    
    -- Context
    context JSONB,
    user_id UUID REFERENCES users(id),
    document_id UUID REFERENCES documents(id),
    job_id UUID REFERENCES analysis_jobs(id),
    
    -- Source
    source VARCHAR(100),  -- Component name
    function_name VARCHAR(255),
    
    -- IP and request info
    ip_address INET,
    user_agent TEXT,
    request_id VARCHAR(100),
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Partitioning by time (optional, for scale)
-- CREATE TABLE system_logs_2024_02 PARTITION OF system_logs
--     FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

CREATE INDEX idx_system_logs_created ON system_logs(created_at);
CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_system_logs_user ON system_logs(user_id);
CREATE INDEX idx_system_logs_job ON system_logs(job_id);
```

---

## JSONB Structures

### Document Metadata Example

```json
{
  "extraction": {
    "company_name": "Apple Inc.",
    "ticker": "AAPL",
    "cik": "0000320193",
    "fiscal_year": 2024,
    "fiscal_period": "Q4",
    "filing_date": "2024-10-30",
    "document_type": "10-K"
  },
  "parser_info": {
    "engine": "pdfplumber",
    "version": "0.11.0",
    "pages": 85,
    "text_length": 125000
  },
  "financial_highlights": {
    "revenue": 383280000000,
    "net_income": 96995000000,
    "total_assets": 352755000000,
    "total_debt": 120000000000
  },
  "sections_detected": [
    "business",
    "risk_factors",
    "financial_statements",
    "management_discussion"
  ]
}
```

### Analysis Results Example

```json
{
  "executive_summary": "Apple Inc. demonstrates strong financial performance...",
  
  "fundamental_analysis": {
    "revenue_growth": {
      "value": "+8.1%",
      "trend": "positive",
      "assessment": "Strong growth maintaining market leadership"
    },
    "profitability": {
      "gross_margin": "45.6%",
      "operating_margin": "30.4%",
      "net_margin": "25.3%",
      "assessment": "Excellent profitability metrics"
    },
    "balance_sheet": {
      "current_ratio": "1.08",
      "debt_to_equity": "1.73",
      "assessment": "Adequate liquidity, manageable debt levels"
    },
    "cash_flow": {
      "operating_cash_flow": "118000000000",
      "free_cash_flow": "99000000000",
      "assessment": "Exceptional cash generation"
    }
  },
  
  "technical_analysis": {
    "trend": "bullish",
    "support_level": 170.00,
    "resistance_level": 195.00,
    "rsi": 62,
    "moving_averages": {
      "sma_50": 182.50,
      "sma_200": 175.30,
      "assessment": "Price above both MAs, bullish structure"
    },
    "volume_analysis": "Increasing volume on up days confirms trend"
  },
  
  "risk_analysis": {
    "market_risk": {
      "beta": 1.2,
      "volatility": "moderate-high",
      "assessment": "Higher volatility than market average"
    },
    "financial_risk": {
      "debt_rating": "AA+",
      "liquidity": "strong",
      "assessment": "Low financial distress risk"
    },
    "operational_risk": [
      "Supply chain concentration in China",
      "Regulatory scrutiny in EU and US",
      "Product cycle maturity for iPhone"
    ],
    "red_flags": []
  },
  
  "synthesis": {
    "investment_thesis": "Market leader with strong fundamentals...",
    "key_strengths": [
      "Dominant market position",
      "Exceptional profitability",
      "Strong cash generation"
    ],
    "key_concerns": [
      "High valuation multiples",
      "Regulatory pressures",
      "Product cycle maturity"
    ],
    "valuation": {
      "current_pe": 28.5,
      "sector_average_pe": 22.0,
      "assessment": "Premium valuation justified by quality"
    }
  },
  
  "recommendation": {
    "action": "hold",
    "target_price": 210.00,
    "time_horizon": "12 months",
    "confidence": 0.72,
    "rationale": "Strong company at fair valuation..."
  }
}
```

---

## Redis Cache Schema

### Cache Keys Pattern

```
# Document content cache
doc:content:{document_id}  → Binary PDF content
TTL: 1 hour

# Parsed text cache
doc:text:{document_id}  → Extracted text
TTL: 24 hours

# Analysis results cache
analysis:{job_id}  → Full analysis JSON
TTL: 7 days

# User session cache
session:{user_id}:{session_id}  → JWT payload
TTL: 30 minutes (refresh token: 7 days)

# Rate limiting
ratelimit:{user_id}:{endpoint}  → Request count
TTL: 1 hour

# External API cache
api:yahoo:{ticker}:{metric}  → Stock data
TTL: 5 minutes (real-time) / 1 hour (fundamentals)

api:alpha:{function}:{symbol}  → Technical indicators
TTL: 1 hour
```

### Redis Data Structures

```python
# Sorted set for document expiration tracking
# Key: "documents:expiring"
# Score: expiration timestamp
# Member: document_id

# Hash for user preferences
# Key: "user:prefs:{user_id}"
# Fields: theme, notifications, default_filters

# List for recent analysis jobs per user
# Key: "user:jobs:{user_id}"
# Items: [job_id_1, job_id_2, ...]
# Trim to last 50
```

---

## Triggers and Functions

### Auto-Update Timestamp Trigger

```sql
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_analysis_jobs_updated_at BEFORE UPDATE ON analysis_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Soft Delete Document Function

```sql
CREATE OR REPLACE FUNCTION soft_delete_document(doc_id UUID)
RETURNS VOID AS $$
BEGIN
    UPDATE documents 
    SET status = 'expired', deleted_at = CURRENT_TIMESTAMP
    WHERE id = doc_id;
    
    -- Cascade to analysis jobs
    UPDATE analysis_jobs 
    SET status = 'cancelled'
    WHERE document_id = doc_id AND status IN ('pending', 'running');
END;
$$ LANGUAGE plpgsql;
```

### Cleanup Expired Documents (Run daily via cron)

```sql
CREATE OR REPLACE FUNCTION cleanup_expired_documents()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO deleted_count
    FROM documents
    WHERE expires_at < CURRENT_TIMESTAMP AND deleted_at IS NULL;
    
    UPDATE documents 
    SET status = 'expired', deleted_at = CURRENT_TIMESTAMP
    WHERE expires_at < CURRENT_TIMESTAMP AND deleted_at IS NULL;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;
```

---

## Alembic Migration Script

```python
# alembic/versions/001_initial_schema.py

"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-02-14

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255)),
        sa.Column('role', sa.String(50), server_default='user'),
        sa.Column('is_active', sa.Boolean(), server_default='true'),
        sa.Column('is_verified', sa.Boolean(), server_default='false'),
        sa.Column('preferences', postgresql.JSONB(), server_default='{}'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login_at', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
        sa.CheckConstraint("email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{2,}$'", name='valid_email')
    )
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('filename', sa.String(500), nullable=False),
        sa.Column('original_name', sa.String(500), nullable=False),
        sa.Column('file_path', sa.String(1000), nullable=False),
        sa.Column('file_size', sa.BigInteger(), nullable=False),
        sa.Column('mime_type', sa.String(100)),
        sa.Column('doc_type', sa.String(50)),
        sa.Column('company_name', sa.String(255)),
        sa.Column('ticker_symbol', sa.String(20)),
        sa.Column('fiscal_year', sa.Integer()),
        sa.Column('metadata', postgresql.JSONB(), server_default='{}'),
        sa.Column('status', sa.String(50), server_default='uploaded'),
        sa.Column('uploaded_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP + INTERVAL '30 days'")),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('redis_cache_key', sa.String(255)),
        sa.Column('cache_hits', sa.Integer(), server_default='0'),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('file_size <= 10485760', name='max_file_size')
    )
    
    # Create indexes
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_documents_user_id', 'documents', ['user_id'])
    op.create_index('idx_documents_status', 'documents', ['status'])
    op.create_index('idx_documents_expires', 'documents', ['expires_at'])
    op.create_index('idx_documents_ticker', 'documents', ['ticker_symbol'])
    op.create_index('idx_documents_metadata', 'documents', ['metadata'], postgresql_using='gin')
    
    # Create analysis_jobs table
    op.create_table(
        'analysis_jobs',
        sa.Column('id', postgresql.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('document_id', postgresql.UUID(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=False),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('progress_percent', sa.Integer(), server_default='0'),
        sa.Column('current_agent', sa.String(100)),
        sa.Column('agent_logs', postgresql.JSONB(), server_default='[]'),
        sa.Column('started_at', sa.DateTime(timezone=True)),
        sa.Column('completed_at', sa.DateTime(timezone=True)),
        sa.Column('failed_at', sa.DateTime(timezone=True)),
        sa.Column('error_message', sa.Text()),
        sa.Column('results', postgresql.JSONB()),
        sa.Column('fundamental_score', sa.String(2)),
        sa.Column('technical_score', sa.String(2)),
        sa.Column('risk_score', sa.Integer()),
        sa.Column('recommendation', sa.String(20)),
        sa.Column('confidence_score', sa.Numeric(3, 2)),
        sa.Column('key_metrics', postgresql.JSONB()),
        sa.Column('alert_flags', postgresql.JSONB(), server_default='[]'),
        sa.Column('report_generated', sa.Boolean(), server_default='false'),
        sa.Column('report_url', sa.String(1000)),
        sa.Column('estimated_cost', sa.Numeric(10, 4)),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['document_id'], ['documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE')
    )
    
    op.create_index('idx_analysis_jobs_document', 'analysis_jobs', ['document_id'])
    op.create_index('idx_analysis_jobs_user', 'analysis_jobs', ['user_id'])
    op.create_index('idx_analysis_jobs_status', 'analysis_jobs', ['status'])


def downgrade():
    op.drop_table('analysis_jobs')
    op.drop_table('documents')
    op.drop_table('users')
```

---

## Next Steps

1. **Run migrations:**
   ```bash
   alembic upgrade head
   ```

2. **Verify schema:**
   ```bash
   psql -d findoc -c "\dt"
   ```

3. **Connect from FastAPI:**
   ```python
   from sqlalchemy.ext.asyncio import create_async_engine
   
   engine = create_async_engine(
       "postgresql+asyncpg://user:pass@localhost/findoc"
   )
   ```

**Schema ready for implementation!** 🚀
