# API Documentation - FinDocAnalyzer

## Base URL

```
Development: http://localhost:8000
Production: https://api.findoc-analyzer.railway.app
```

---

## Authentication

All endpoints (except public ones) require JWT token in Authorization header:

```
Authorization: Bearer <access_token>
```

### Token Refresh

Access tokens expire in 30 minutes. Use refresh token to get new access token:

```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "<refresh_token>"
}
```

---

## API Endpoints

### 1. Authentication

#### Register User

```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "full_name": "John Doe",
      "role": "user"
    },
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer"
  }
}
```

#### Login

```http
POST /api/v1/auth/login
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=SecurePass123!
```

**Response:**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIs...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIs...",
    "token_type": "bearer",
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "role": "user"
    }
  }
}
```

#### Logout

```http
POST /api/v1/auth/logout
Authorization: Bearer <token>
```

#### Get Current User

```http
GET /api/v1/auth/me
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "email": "user@example.com",
    "full_name": "John Doe",
    "role": "user",
    "preferences": {},
    "created_at": "2026-02-14T10:00:00Z"
  }
}
```

---

### 2. Documents

#### Upload Document

```http
POST /api/v1/documents/upload
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <binary_file_data>
```

**Constraints:**
- Max file size: 10MB
- Allowed types: PDF, DOCX, TXT

**Response:**
```json
{
  "success": true,
  "data": {
    "document": {
      "id": "uuid",
      "original_name": "AAPL_2024_10K.pdf",
      "file_size": 5242880,
      "mime_type": "application/pdf",
      "status": "uploaded",
      "uploaded_at": "2026-02-14T10:00:00Z",
      "expires_at": "2026-03-16T10:00:00Z"
    },
    "message": "Document uploaded successfully"
  }
}
```

#### List User Documents

```http
GET /api/v1/documents?page=1&limit=20&status=analyzed
Authorization: Bearer <token>
```

**Query Parameters:**
- `page`: Page number (default: 1)
- `limit`: Items per page (default: 20, max: 100)
- `status`: Filter by status (uploaded, processing, analyzed, error)

**Response:**
```json
{
  "success": true,
  "data": {
    "documents": [
      {
        "id": "uuid",
        "original_name": "AAPL_2024_10K.pdf",
        "file_size": 5242880,
        "doc_type": "annual_report",
        "company_name": "Apple Inc.",
        "ticker_symbol": "AAPL",
        "status": "analyzed",
        "uploaded_at": "2026-02-14T10:00:00Z",
        "analysis_summary": {
          "recommendation": "buy",
          "risk_score": 4,
          "fundamental_score": "A-"
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "pages": 3
    }
  }
}
```

#### Get Document Details

```http
GET /api/v1/documents/{document_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "uuid",
    "original_name": "AAPL_2024_10K.pdf",
    "file_size": 5242880,
    "mime_type": "application/pdf",
    "doc_type": "annual_report",
    "company_name": "Apple Inc.",
    "ticker_symbol": "AAPL",
    "fiscal_year": 2024,
    "metadata": {
      "pages": 85,
      "sections_detected": ["business", "risk_factors", "financial_statements"]
    },
    "status": "analyzed",
    "uploaded_at": "2026-02-14T10:00:00Z",
    "expires_at": "2026-03-16T10:00:00Z"
  }
}
```

#### Delete Document

```http
DELETE /api/v1/documents/{document_id}
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "message": "Document deleted successfully"
}
```

---

### 3. Analysis

#### Start Analysis (Async)

```http
POST /api/v1/analysis
Authorization: Bearer <token>
Content-Type: application/json

{
  "document_id": "uuid",
  "analysis_type": "comprehensive"  // Options: comprehensive, fundamental, technical, risk
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job": {
      "id": "job_uuid",
      "document_id": "uuid",
      "status": "pending",
      "progress_percent": 0,
      "created_at": "2026-02-14T10:05:00Z"
    },
    "message": "Analysis started. Use the job_id to track progress."
  }
}
```

#### Get Analysis Status

```http
GET /api/v1/analysis/{job_id}/status
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "job": {
      "id": "job_uuid",
      "status": "running",
      "progress_percent": 45,
      "current_agent": "fundamental",
      "started_at": "2026-02-14T10:05:00Z",
      "agent_logs": [
        {
          "agent": "manager",
          "status": "completed",
          "timestamp": "2026-02-14T10:05:30Z"
        },
        {
          "agent": "fundamental",
          "status": "running",
          "timestamp": "2026-02-14T10:06:00Z"
        }
      ]
    }
  }
}
```

#### Get Analysis Results

```http
GET /api/v1/analysis/{job_id}/results
Authorization: Bearer <token>
```

**Response (Completed):**
```json
{
  "success": true,
  "data": {
    "job": {
      "id": "job_uuid",
      "document_id": "uuid",
      "status": "completed",
      "completed_at": "2026-02-14T10:08:30Z"
    },
    "results": {
      "executive_summary": "Apple Inc. demonstrates strong financial performance...",
      "recommendation": {
        "action": "buy",
        "confidence": 0.82,
        "time_horizon": "medium",
        "target_price": 210.00,
        "stop_loss": 175.00
      },
      "scoring": {
        "fundamental_score": "A-",
        "fundamental_numeric": 8.5,
        "technical_score": "B+",
        "technical_numeric": 7.2,
        "risk_score": 4,
        "composite_score": 7.8
      },
      "fundamental_analysis": {
        "revenue_growth": {
          "value": "+8.1%",
          "trend": "positive",
          "assessment": "Strong growth maintaining market leadership"
        },
        "profitability": {
          "gross_margin": "45.6%",
          "net_margin": "25.3%",
          "assessment": "Excellent profitability metrics"
        }
      },
      "technical_analysis": {
        "trend": "bullish",
        "support_levels": [170.00, 165.00],
        "resistance_levels": [185.00, 195.00],
        "rsi": 62,
        "moving_averages": {
          "price_vs_20ema": "above",
          "ma_alignment": "bullish"
        }
      },
      "risk_analysis": {
        "overall_risk_score": 4,
        "risk_level": "moderate",
        "red_flags": [],
        "key_risks": [
          "Regulatory scrutiny in EU",
          "Supply chain concentration"
        ]
      },
      "key_metrics": {
        "current_price": 185.50,
        "fair_value_range": {"low": 195.00, "high": 220.00},
        "margin_of_safety": "5%"
      },
      "alert_flags": []
    }
  }
}
```

#### Stream Analysis Progress (WebSocket)

```javascript
// Connect to WebSocket
const ws = new WebSocket('wss://api.findoc-analyzer.railway.app/ws/analysis/{job_id}');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  switch(data.type) {
    case 'agent_start':
      console.log(`${data.agent} started`);
      updateProgress(data.progress);
      break;
    case 'agent_complete':
      console.log(`${data.agent} completed`);
      break;
    case 'tool_use':
      console.log(`Using tool: ${data.tool}`);
      break;
    case 'complete':
      console.log('Analysis complete!');
      break;
  }
};
```

---

### 4. Reports

#### Download PDF Report

```http
GET /api/v1/analysis/{job_id}/report.pdf
Authorization: Bearer <token>
```

**Response:** Binary PDF data with `Content-Type: application/pdf`

#### Get Report URL

```http
GET /api/v1/analysis/{job_id}/report-url
Authorization: Bearer <token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "url": "https://storage.findoc-analyzer.com/reports/uuid.pdf",
    "expires_in": 3600
  }
}
```

---

### 5. Admin Endpoints (Admin role only)

#### List All Users

```http
GET /api/v1/admin/users?page=1&limit=50
Authorization: Bearer <admin_token>
```

#### Update User Role

```http
PATCH /api/v1/admin/users/{user_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "role": "admin",
  "is_active": true
}
```

#### System Metrics

```http
GET /api/v1/admin/metrics
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "users": {
      "total": 150,
      "active_today": 45,
      "new_this_week": 12
    },
    "documents": {
      "total": 520,
      "analyzed": 480,
      "processing": 5,
      "failed": 12
    },
    "analysis": {
      "total_jobs": 580,
      "avg_completion_time": "3m 45s",
      "success_rate": 0.96
    },
    "storage": {
      "total_used_gb": 4.2,
      "documents_size_gb": 3.8
    },
    "api_usage": {
      "calls_today": 1250,
      "cost_today_usd": 45.50
    }
  }
}
```

#### Trigger Document Cleanup

```http
POST /api/v1/admin/cleanup
Authorization: Bearer <admin_token>
```

**Response:**
```json
{
  "success": true,
  "data": {
    "deleted_documents": 23,
    "freed_storage_mb": 156.5
  }
}
```

---

## Error Handling

### Standard Error Response

```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": {},
    "timestamp": "2026-02-14T10:00:00Z"
  }
}
```

### Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `UNAUTHORIZED` | 401 | Invalid or missing token |
| `FORBIDDEN` | 403 | Insufficient permissions |
| `NOT_FOUND` | 404 | Resource not found |
| `VALIDATION_ERROR` | 422 | Invalid input data |
| `FILE_TOO_LARGE` | 413 | File exceeds 10MB limit |
| `UNSUPPORTED_TYPE` | 415 | File type not allowed |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `ANALYSIS_FAILED` | 502 | AI analysis failed |

---

## Rate Limiting

- **Authenticated requests:** 100 requests per hour
- **Uploads:** 10 per hour
- **Analysis jobs:** 5 per hour (cost control)

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1644850800
```

---

## Pagination

List endpoints return paginated results:

```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "pages": 8,
    "has_next": true,
    "has_prev": false
  }
}
```

---

## OpenAPI Schema

Access interactive docs at:
- Swagger UI: `/docs`
- ReDoc: `/redoc`
- OpenAPI JSON: `/openapi.json`

---

## SDK Example (Python)

```python
import requests

class FinDocClient:
    def __init__(self, base_url, token=None):
        self.base_url = base_url
        self.token = token
    
    def _headers(self):
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return headers
    
    def login(self, email, password):
        response = requests.post(
            f"{self.base_url}/api/v1/auth/login",
            data={"username": email, "password": password}
        )
        data = response.json()
        self.token = data["data"]["access_token"]
        return data
    
    def upload_document(self, file_path):
        with open(file_path, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": f"Bearer {self.token}"}
            response = requests.post(
                f"{self.base_url}/api/v1/documents/upload",
                headers=headers,
                files=files
            )
        return response.json()
    
    def start_analysis(self, document_id):
        response = requests.post(
            f"{self.base_url}/api/v1/analysis",
            headers=self._headers(),
            json={"document_id": document_id}
        )
        return response.json()
    
    def get_results(self, job_id):
        response = requests.get(
            f"{self.base_url}/api/v1/analysis/{job_id}/results",
            headers=self._headers()
        )
        return response.json()

# Usage
client = FinDocClient("https://api.findoc-analyzer.railway.app")
client.login("user@example.com", "password")

# Upload and analyze
upload = client.upload_document("AAPL_10K.pdf")
doc_id = upload["data"]["document"]["id"]

job = client.start_analysis(doc_id)
job_id = job["data"]["job"]["id"]

# Poll for results
import time
while True:
    result = client.get_results(job_id)
    if result["data"]["job"]["status"] == "completed":
        print(result["data"]["results"]["recommendation"])
        break
    time.sleep(5)
```

---

## Next Steps

See `/docs/FRONTEND.md` for React component integration!
