from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404
from django.db.models import Q
from .models import Document
from .forms import DocumentForm
import os
import openai
from django.conf import settings
import json
from datetime import datetime
from .weaviate_module.utils import send_to_weaviate
# Set OpenAI API key from environment
openai.api_key = os.getenv('OPENAI_API_KEY')

@login_required
def dashboard_view(request):
    # Get filter parameters
    search = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    # Base queryset
    documents = Document.objects.all().order_by('-uploaded_at')
    
    # Apply filters
    if search:
        documents = documents.filter(
            Q(file__icontains=search) | 
            Q(uploaded_by__username__icontains=search)
        )
    
    if status_filter:
        documents = documents.filter(status=status_filter)
        
    if date_filter:
        documents = documents.filter(uploaded_at__date=date_filter)
    
    # Calculate statistics
    total_uploaded = Document.objects.count()
    total_processed = Document.objects.filter(status='processed').count()
    total_processing = Document.objects.filter(status='processing').count()
    processing_rate = round((total_processed / total_uploaded * 100) if total_uploaded > 0 else 0)
    
    context = {
        'total_uploaded': total_uploaded,
        'total_processed': total_processed,
        'total_processing': total_processing,
        'processing_rate': processing_rate,
        'documents': documents
    }
    
    if request.user.is_staff:
        upload_form = DocumentForm()
        context['upload_form'] = upload_form
        return render(request, 'dashboard/admin_dashboard.html', context)
    else:
        return render(request, 'dashboard/user_dashboard.html', context)

@login_required
def upload_file_view(request):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to upload files.')
        return redirect('dashboard')

    if request.method == 'POST':
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.uploaded_by = request.user
            document.save()
            messages.success(request, f'Successfully uploaded "{document.file.name}"')
            return redirect('dashboard')
        else:
            messages.error(request, 'Error uploading file. Please check the file format and size.')

    return redirect('dashboard')

@login_required
def document_detail_view(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    
    # Check if file exists and get size safely
    file_exists = False
    file_size = 0
    
    try:
        if document.file and os.path.exists(document.file.path):
            file_exists = True
            file_size = os.path.getsize(document.file.path)
    except (ValueError, OSError):
        pass
    
    context = {
        'document': document,
        'file_size': file_size,
        'file_exists': file_exists
    }
    return render(request, 'dashboard/document_detail.html', context)

@login_required
def process_document_view(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    
    # Check if already processed
    if document.status == 'processed':
        messages.info(request, f'Document "{document.file.name}" is already processed.')
        return redirect('dashboard')
    
    # Check if currently processing
    if document.status == 'processing':
        messages.warning(request, f'Document "{document.file.name}" is currently being processed.')
        return redirect('dashboard')
    
    # Update status to processing
    document.status = 'processing'
    document.save()

    try:
        # Extract text from PDF
        text_content = extract_text_from_pdf(document.file.path)
        
        is_document_unique = send_to_weaviate(document.file.name,text_content)
        
        if is_document_unique:
            if not text_content.strip():
                raise Exception("No text could be extracted from the document")
            
            # Process with OpenAI
            ai_summary = process_with_openai(text_content, document.file.name)
            
            # Save the AI summary
            summary_filename = f"{os.path.splitext(document.file.name)[0]}_ai_summarized.json"
            summary_path = os.path.join(settings.MEDIA_ROOT, 'summaries', summary_filename)
            
            # Ensure summaries directory exists
            os.makedirs(os.path.dirname(summary_path), exist_ok=True)
            
            with open(summary_path, 'w', encoding='utf-8') as f:
                json.dump(ai_summary, f, indent=2, ensure_ascii=False)
            
            # Update document record
            document.summarized_file.name = f'summaries/{summary_filename}'
            document.status = 'processed'
            document.save()
            
            messages.success(request, f'Successfully processed "{document.file.name}" with AI analysis.')
        
        else:
            document.status = 'failed'
            document.save()
            messages.error(request, f'Failed to process "{document.file.name}": A similar file has already been uploaded.')
        
    except Exception as e:
        document.status = 'failed'
        document.save()
        messages.error(request, f'Failed to process "{document.file.name}": {str(e)}')

    return redirect('dashboard')

def extract_text_from_pdf(file_path):
    """Extract text from PDF using multiple methods"""
    try:
        # Try PyPDF2 first (faster)
        import PyPDF2
        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            text = ""
            for page in pdf_reader.pages:
                text += page.extract_text() + "\n"
        
        if text.strip():
            return text
    except:
        pass
    
    try:
        # Fallback to OCR with pytesseract
        from pdf2image import convert_from_path
        import pytesseract
        
        images = convert_from_path(file_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image) + "\n"
        
        return text
    except Exception as e:
        raise Exception(f"Could not extract text: {str(e)}")

def process_with_openai(text_content, filename):
    """Process document content with OpenAI for tender analysis"""
    
    # Truncate text if too long (OpenAI has token limits)
    max_chars = 12000  # Roughly 3000 tokens
    if len(text_content) > max_chars:
        text_content = text_content[:max_chars] + "..."
    
    prompt = f"""
    Analyze this tender/government document and extract key information. Focus on identifying:

    1. TENDER INFORMATION:
       - Tender number/reference
       - Title/description
       - Procuring entity/organization
       - Category (ICT, Construction, Consultancy, etc.)
       - Location/region
       - Estimated budget (if mentioned)

    2. IMPORTANT DATES:
       - Closing date and time
       - Site visit dates (if any)
       - Pre-bid meeting dates

    3. REQUIREMENTS:
       - Eligibility criteria
       - Mandatory documents required
       - Technical specifications (brief summary)
       - Experience requirements

    4. SUBMISSION DETAILS:
       - How to submit (online/physical)
       - Where to submit
       - Contact information

    5. BUSINESS OPPORTUNITY ASSESSMENT:
       - Rate the opportunity (1-10) based on clarity and completeness
       - Key risks or challenges
       - Recommended next steps

    Document: {filename}
    
    Content:
    {text_content}
    
    Please provide a structured JSON response with all the extracted information.
    """
    
    try:
        client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are an expert tender analyst. Extract and structure tender information accurately."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.3
        )
        
        ai_response = response.choices[0].message.content
        
        # Try to parse as JSON, if it fails, wrap in a structure
        try:
            parsed_response = json.loads(ai_response)
        except:
            parsed_response = {
                "analysis": ai_response,
                "extracted_text_length": len(text_content),
                "processing_timestamp": datetime.now().isoformat()
            }
        
        # Add metadata
        parsed_response["metadata"] = {
            "filename": filename,
            "processed_at": datetime.now().isoformat(),
            "model_used": "gpt-3.5-turbo",
            "text_length": len(text_content)
        }
        
        return parsed_response
        
    except Exception as e:
        # Fallback response if OpenAI fails
        return {
            "error": f"AI processing failed: {str(e)}",
            "extracted_text": text_content[:1000] + "..." if len(text_content) > 1000 else text_content,
            "metadata": {
                "filename": filename,
                "processed_at": datetime.now().isoformat(),
                "status": "failed"
            }
        }

@login_required
def view_document_file(request, document_id):
    """Serve document files securely"""
    document = get_object_or_404(Document, pk=document_id)
    
    if not os.path.exists(document.file.path):
        raise Http404("Document file not found")
    
    with open(document.file.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{document.file.name}"'
        return response

@login_required
def view_summary_file(request, document_id):
    """Serve summary files securely"""
    document = get_object_or_404(Document, pk=document_id)
    
    if not document.summarized_file or not os.path.exists(document.summarized_file.path):
        raise Http404("Summary file not found")
    
    with open(document.summarized_file.path, 'r', encoding='utf-8') as f:
        content = f.read()
        response = HttpResponse(content, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(document.summarized_file.name)}"'
        return response
