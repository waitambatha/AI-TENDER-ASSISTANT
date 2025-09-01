# Tender AI Assistant

An AI-powered document analysis system for processing tender documents and extracting key information.

## Features

### ✨ Enhanced UI/UX
- Modern, responsive design with gradient themes
- Attractive login and registration forms
- Interactive drag-and-drop file upload
- Real-time loading indicators
- Professional dashboard with statistics

### 🤖 AI Processing
- OpenAI GPT-3.5 integration for document analysis
- Automatic text extraction from PDFs
- Structured tender information extraction
- Intelligent opportunity assessment
- Prevents duplicate processing

### 📄 Document Management
- Secure file upload and storage
- Document viewing and download
- AI summary generation and storage
- Status tracking (uploaded, processing, processed, failed)
- Search and filter functionality

### 🔐 User Management
- Role-based access control
- Admin and user dashboards
- Secure authentication system
- Password strength validation

## Installation

1. **Clone and setup virtual environment:**
   ```bash
   cd /path/to/tender
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Setup environment variables:**
   Create a `.env` file with:
   ```
   DB_NAME=tender_project
   DB_USER=postgres
   DB_PASSWORD=your_password
   DB_HOST=localhost
   DB_PORT=5432
   OPENAI_API_KEY=your_openai_api_key
   ```

4. **Run migrations:**
   ```bash
   python manage.py migrate
   ```

5. **Create admin user:**
   ```bash
   python manage.py createsuperuser
   ```

6. **Start the server:**
   ```bash
   python manage.py runserver
   ```

## Usage

### Admin Access
- **Username:** admin
- **Password:** masterclass

### Features Available:
1. **Upload Documents:** Drag and drop PDF files for processing
2. **AI Processing:** Click "Process with AI" to analyze documents
3. **View Results:** Access structured tender information and summaries
4. **Search & Filter:** Find documents by status, date, or keywords

### AI Analysis Extracts:
- Tender number and title
- Procuring entity information
- Important dates and deadlines
- Requirements and eligibility criteria
- Submission details
- Business opportunity assessment

## Technical Stack

- **Backend:** Django 5.2.5
- **Database:** PostgreSQL
- **AI:** OpenAI GPT-3.5 Turbo
- **Frontend:** Bootstrap 5.3, Custom CSS
- **File Processing:** PyPDF2, pytesseract, pdf2image

## File Structure

```
tender/
├── dashboard/          # Main application
├── users/             # User management
├── templates/         # HTML templates
├── media/            # Uploaded files
├── documents/        # Document storage
└── summaries/        # AI-generated summaries
```

## API Endpoints

- `/dashboard/` - Main dashboard
- `/dashboard/upload/` - File upload
- `/dashboard/document/<id>/` - Document details
- `/dashboard/document/<id>/process/` - AI processing
- `/dashboard/document/<id>/view/` - View document
- `/dashboard/document/<id>/summary/` - Download summary

## Security Features

- CSRF protection
- Secure file handling
- Role-based access control
- Input validation and sanitization
- Secure file serving

## Future Enhancements

- Batch processing capabilities
- Advanced search with full-text indexing
- Email notifications for processing completion
- Export to various formats (Excel, Word)
- Integration with calendar systems
- Multi-language support

## Support

For issues or feature requests, contact the development team or create an issue in the project repository.
