

## Project Overview
A comprehensive financial document analysis system that processes corporate reports, financial statements, and investment documents using AI-powered analysis agents. This is a production-grade system that requires enterprise-level thinking and implementation.



### Prerequisites
- **Python 3.11.x** (Required for optimal performance and compatibility)
- Node.js 18+ (for frontend development)
- CrewAI 0.130.0



### Sample Document
The system analyzes financial documents like Tesla's Q2 2025 financial update.

**To add Tesla's financial document:**
1. Download the Tesla Q2 2025 update from: https://www.tesla.com/sites/default/files/downloads/TSLA-Q2-2025-Update.pdf
2. Save it as `data/TSLA-Q2-2025-Update.pdf` in the project directory
3. Or upload any financial PDF through the API endpoint

**Note:** Current `data/TSLA-Q2-2025-Update.pdf` may be a placeholder - ensure you test with actual financial documents.


## Mission Complexity



#### **Security & Authentication**
- Implement JWT-based authentication system
- Add role-based access control (Admin, Viewer)
- API rate limiting and request validation
- Input sanitization and file upload security
- Secure environment variable management

#### **Database Integration** 
- Design and implement database schema for:
  - User management and authentication
  - Document storage and metadata
  - Analysis results and history
  - Audit logs and system monitoring
- Database connection pooling and optimization
- You can use any database you want (preferably MongoDB), but you should have a good reason for choosing it.

#### **Frontend Integration (MANDATORY)**
- Build a complete web application frontend using modern framework (React, Vue.js, or Angular)
- **Preferred (not mandatory):** TailwindCSS for styling and shadcn/ui components for enhanced UI
- Real-time file upload with progress indicators
- Interactive dashboards for financial analysis results
- User authentication and session management on frontend
- Document management interface (upload, view, delete, search)
- Analysis history and results visualization
- Export functionality with download capabilities
- Error handling and user feedback 

#### **Performance & Scalability**
- Implement Redis caching for frequently accessed data
- Add background job processing with Redis or Celery or other job queue system
- Database query osystemsptimization and indexing
- Memory-efficient document processing
- Async/await patterns throughout the codebase

#### **Monitoring & Observability**
- Add LLM Observability Tools to the codebase to monitor the LLM calls and the tools calls.

### Edge Cases & Advanced Scenarios (CRITICAL FOR EVALUATION)

**Think like a senior engineer - what could break this system?**

#### **Document Processing Edge Cases**
- Corrupted or password-protected PDFs
- Documents larger than 100MB
- Non-English financial documents
- Scanned documents with poor OCR quality
- Documents with complex tables and charts

#### **API & System Edge Cases**
- Concurrent file uploads from multiple users
- Network timeouts during long analysis processes
- Memory exhaustion with large documents
- Database connection failures during analysis
- API rate limit exceeded scenarios
- Invalid file formats and malicious uploads
- Extremely long user queries or prompts

#### **Frontend & User Experience Edge Cases**
- File upload failures with proper error recovery
- Large file uploads exceeding browser memory limits
- Simultaneous document processing and UI responsiveness
- Cross-origin resource sharing (CORS) issues


## Expected Features (MINIMUM)

### Backend API Features
- Upload financial documents (multiple formats)
- AI-powered financial analysis with confidence scoring
- Investment recommendations with risk assessment
- Market insights and trend analysis
- User authentication and session management
- Document history and analysis tracking
- Comprehensive error handling and logging
- API documentation and testing interface
- **Python 3.11.x runtime**

### Frontend Application Features
- Modern, responsive web application (React/Vue/Angular)
- **Preferred:** TailwindCSS styling with shadcn/ui component library
- User registration and authentication interface
- Interactive analysis results dashboard
- Document management system (view, search, delete)
- Analysis history with filtering and sorting
- Export functionality for reports
- Real-time status updates and progress tracking



