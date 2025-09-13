from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, Http404, JsonResponse
from django.db.models import Q
from .models import Document, SearchLog, UserAPIKey
from .forms import DocumentForm
import os
import weaviate
from langchain_community.llms import Ollama
from django.conf import settings
import json
from datetime import datetime
import zipfile
import tempfile
import logging
from .weaviate_module.client import get_collection, get_weaviate_client
from .weaviate_module.utils import send_to_weaviate,get_related_text

logger = logging.getLogger(__name__)


@login_required
def dashboard_view(request):
    if request.user.is_staff:
        # Admin dashboard logic
        search = request.GET.get('search', '')
        status_filter = request.GET.get('status', '')
        date_filter = request.GET.get('date', '')
        
        documents = Document.objects.all().order_by('-uploaded_at')
        
        if search:
            documents = documents.filter(
                Q(file__icontains=search) | 
                Q(uploaded_by__username__icontains=search)
            )
        
        if status_filter:
            documents = documents.filter(status=status_filter)
            
        if date_filter:
            documents = documents.filter(uploaded_at__date=date_filter)
        
        total_uploaded = Document.objects.count()
        total_processed = Document.objects.filter(status='processed').count()
        total_processing = Document.objects.filter(status='processing').count()
        processing_rate = round((total_processed / total_uploaded * 100) if total_uploaded > 0 else 0)
        
        context = {
            'total_uploaded': total_uploaded,
            'total_processed': total_processed,
            'total_processing': total_processing,
            'processing_rate': processing_rate,
            'documents': documents,
            'upload_form': DocumentForm()
        }
        return render(request, 'dashboard/admin_dashboard.html', context)
    else:
        # User dashboard with search functionality
        recent_searches = SearchLog.objects.filter(user=request.user)[:5]
        user_api_keys = UserAPIKey.objects.filter(user=request.user)
        
        # Get all processed documents for filtering
        documents = Document.objects.filter(status='processed').order_by('-uploaded_at')
        
        context = {
            'recent_searches': recent_searches,
            'user_api_keys': user_api_keys,
            'documents': documents
        }
        return render(request, 'dashboard/user_dashboard.html', context)

@login_required
def search_documents(request):
    if request.method == 'POST':
        query = request.POST.get('query', '').strip()
        if not query:
            return JsonResponse({'error': 'Query is required'})
        
        # Check if we have this search in logs first
        existing_log = SearchLog.objects.filter(user=request.user, query=query).first()
        if existing_log:
            return JsonResponse({'results': existing_log.results, 'from_cache': True})
        
        # Search in Weaviate
        results = get_related_text(query)
        
        if results is None:
            return JsonResponse({'results': [], 'message': 'Search service temporarily unavailable'})
        
        # Save search log
        SearchLog.objects.create(
            user=request.user,
            query=query,
            results=results
        )
        
        return JsonResponse({'results': results, 'from_cache': False})
    
    return JsonResponse({'error': 'Invalid request method'})

@login_required
def search_logs_view(request):
    logs = SearchLog.objects.filter(user=request.user)
    return render(request, 'dashboard/search_logs.html', {'logs': logs})

@login_required
def manage_api_keys(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'add':
            name = request.POST.get('name')
            api_key = request.POST.get('api_key')
            aws_secret_key = ""
            
            try:
                aws_secret_key = request.POST.get("aws_secret_key")
            except:
                pass

            
            if name and api_key:
                user_key = UserAPIKey(user=request.user, name=name)
                user_key.set_api_key(api_key)
                user_key.save()
                messages.success(request, f'API key "{name}" added successfully')
                
            if aws_secret_key:
                user_key = UserAPIKey(user=request.user, name="X-AWS-Secret-Key")
                user_key.set_api_key(aws_secret_key)
                user_key.save()
                messages.success(request, f'API key "{name}" added successfully')
        
        elif action == 'activate':
            key_id = request.POST.get('key_id')
            UserAPIKey.objects.filter(user=request.user).update(is_active=False)
            UserAPIKey.objects.filter(id=key_id, user=request.user).update(is_active=True)
            messages.success(request, 'API key activated')
        
        elif action == 'delete':
            key_id = request.POST.get('key_id')
            UserAPIKey.objects.filter(id=key_id, user=request.user).delete()
            messages.success(request, 'API key deleted')
    
    return redirect('dashboard')

def get_user_api_key(user):
    """Get active API key for user or default"""
    user_key = UserAPIKey.objects.filter(user=user, is_active=True).first()
    if user_key:
        return user_key.get_api_key()
    return os.getenv('OPENAI_API_KEY')

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
    
    if document.status == 'processed':
        messages.info(request, f'Document "{document.file.name}" is already processed.')
        return redirect('dashboard')
    
    if document.status == 'processing':
        messages.warning(request, f'Document "{document.file.name}" is currently being processed.')
        return redirect('dashboard')
    
    document.status = 'processing'
    document.save()

    try:
        text_content = extract_text_from_pdf(document.file.path)
        
        if not text_content.strip():
            raise Exception("No text could be extracted from the document")
        
        # Use Weaviate processing
        is_document_unique, summary_filename = send_to_weaviate(document.file.name, text_content)
        
        if is_document_unique and summary_filename:
            document.summarized_file.name = f'summaries/{summary_filename}'
            document.status = 'processed'
            document.save()
            
            messages.success(request, f'Successfully processed "{document.file.name}" with AI analysis.')
        elif not is_document_unique:
            document.status = 'failed'
            document.save()
            messages.error(request, f'Failed to process "{document.file.name}": A similar file has already been uploaded.')
        else:
            raise Exception("AI processing failed")
        
    except Exception as e:
        document.status = 'failed'
        document.save()
        messages.error(request, f'Failed to process "{document.file.name}": {str(e)}')

    return redirect('dashboard')

def extract_text_from_pdf(file_path):
    try:
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
        from pdf2image import convert_from_path
        import pytesseract
        
        images = convert_from_path(file_path)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image) + "\n"
        
        return text
    except Exception as e:
        raise Exception(f"Could not extract text: {str(e)}")

def process_with_llama_weaviate(text_content, filename, api_key=None):
    max_chars = 12000
    if len(text_content) > max_chars:
        text_content = text_content[:max_chars] + "..."
    
    try:
        # Initialize Weaviate client
        client = weaviate.Client("http://localhost:8080")
        
        # Initialize Llama model
        llm = Ollama(model="llama2")
        
        # Store document in Weaviate
        document_data = {
            "content": text_content,
            "filename": filename,
            "processed_at": datetime.now().isoformat()
        }
        
        client.data_object.create(
            data_object=document_data,
            class_name="Document"
        )
        
        # Process with Llama
        prompt = f"""
        Analyze this tender/government document and extract key information:

        1. TENDER INFORMATION:
           - Tender number/reference
           - Title/description
           - Procuring entity/organization
           - Category (ICT, Construction, Consultancy, etc.)

        2. IMPORTANT DATES:
           - Closing date and time
           - Site visit dates (if any)

        3. REQUIREMENTS:
           - Eligibility criteria
           - Mandatory documents required

        4. SUBMISSION DETAILS:
           - How to submit
           - Contact information

        Document: {filename}
        Content: {text_content}

        Provide structured JSON response.
        """
        
        response = llm(prompt)
        
        try:
            parsed_response = json.loads(response)
        except:
            parsed_response = {
                "analysis": response,
                "extracted_text_length": len(text_content),
                "processing_timestamp": datetime.now().isoformat()
            }
        
        parsed_response["metadata"] = {
            "filename": filename,
            "processed_at": datetime.now().isoformat(),
            "model_used": "llama2",
            "text_length": len(text_content)
        }
        
        return parsed_response
        
    except Exception as e:
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
    document = get_object_or_404(Document, pk=document_id)
    
    if not os.path.exists(document.file.path):
        raise Http404("Document file not found")
    
    with open(document.file.path, 'rb') as f:
        response = HttpResponse(f.read(), content_type='application/pdf')
        response['Content-Disposition'] = f'inline; filename="{document.file.name}"'
        return response

@login_required
def view_summary_file(request, document_id):
    document = get_object_or_404(Document, pk=document_id)
    
    if not document.summarized_file or not os.path.exists(document.summarized_file.path):
        raise Http404("Summary file not found")
    
    with open(document.summarized_file.path, 'r', encoding='utf-8') as f:
        content = f.read()
        response = HttpResponse(content, content_type='application/json')
        response['Content-Disposition'] = f'attachment; filename="{os.path.basename(document.summarized_file.name)}"'
        return response

@login_required
def document_management_view(request):
    """Document management page with search, filter, and bulk download"""
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    documents = Document.objects.filter(uploaded_by=request.user).order_by('-uploaded_at')
    
    if search:
        documents = documents.filter(file__icontains=search)
    
    if date_from:
        documents = documents.filter(uploaded_at__date__gte=date_from)
    
    if date_to:
        documents = documents.filter(uploaded_at__date__lte=date_to)
    
    # Add file size to each document
    for doc in documents:
        try:
            if doc.file and os.path.exists(doc.file.path):
                doc.file_size = os.path.getsize(doc.file.path)
            else:
                doc.file_size = 0
        except:
            doc.file_size = 0
    
    context = {
        'documents': documents,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'dashboard/document_management.html', context)

@login_required
def bulk_download_documents(request):
    """Handle bulk download of selected documents"""
    if request.method == 'POST':
        document_ids = request.POST.getlist('document_ids')
        
        if not document_ids:
            messages.error(request, 'No documents selected for download.')
            return redirect('document_management')
        
        documents = Document.objects.filter(id__in=document_ids, uploaded_by=request.user)
        
        if len(documents) == 1:
            # Single file download
            document = documents.first()
            if document.file and os.path.exists(document.file.path):
                with open(document.file.path, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/octet-stream')
                    response['Content-Disposition'] = f'attachment; filename="{os.path.basename(document.file.name)}"'
                    return response
            else:
                messages.error(request, 'File not found.')
                return redirect('document_management')
        
        else:
            # Multiple files - create zip
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_zip:
                with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    for document in documents:
                        if document.file and os.path.exists(document.file.path):
                            zip_file.write(document.file.path, os.path.basename(document.file.name))
                
                temp_zip.seek(0)
                with open(temp_zip.name, 'rb') as f:
                    response = HttpResponse(f.read(), content_type='application/zip')
                    response['Content-Disposition'] = f'attachment; filename="documents_{datetime.now().strftime("%Y%m%d_%H%M%S")}.zip"'
                
                os.unlink(temp_zip.name)
                return response
    
    return redirect('document_management')

@login_required
def delete_document_view(request, document_id):
    if not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete documents.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        document = get_object_or_404(Document, pk=document_id)
        filename = document.file.name
        
        # Delete physical files
        try:
            if document.file and os.path.exists(document.file.path):
                os.remove(document.file.path)
            if document.summarized_file and os.path.exists(document.summarized_file.path):
                os.remove(document.summarized_file.path)
        except Exception as e:
            messages.warning(request, f'File deletion warning: {str(e)}')
        
        # Delete database record
        document.delete()
        messages.success(request, f'Successfully deleted "{filename}"')
    
    return redirect('dashboard')
def get_document_summary(document_name):
    """Get document summary from Weaviate"""
    return weaviate_summary(document_name)

def weaviate_summary(document_name):
    """Get summary from Weaviate"""
    client = get_collection()
    
    if client is None:
        raise Exception("Weaviate connection failed")
        
    try:
        where_filter = {
            "path": ["file_name"],
            "operator": "Equal",
            "valueText": document_name
        }
        
        result = client.query.get("TenderDocument", ["summary"]).with_where(where_filter).with_limit(1).do()
        
        documents = result.get("data", {}).get("Get", {}).get("TenderDocument", [])
        if documents:
            return documents[0].get("summary")
        return None
    except Exception as e:
        logger.error(f"Error getting Weaviate summary: {e}")
        raise Exception(f"Failed to get summary: {e}")

@login_required
def get_summary_view(request, document_id):
    """API endpoint to get document summary"""
    document = get_object_or_404(Document, pk=document_id)
    
    try:
        summary = get_document_summary(document.file.name)
        if summary:
            return JsonResponse({"summary": summary})
        else:
            return JsonResponse({"summary": None, "message": "No summary available"})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
@login_required
def admin_weaviate_view(request):
    """Admin page to manage Weaviate data"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    documents = get_collection()
    weaviate_data = []
    
    if documents:
        try:
            result = documents.query.get("TenderDocument", ["file_name", "time_created", "content_hash", "summary"]).with_limit(100).do()
            weaviate_data = result.get("data", {}).get("Get", {}).get("TenderDocument", [])
        except Exception as e:
            messages.error(request, f'Error fetching Weaviate data: {e}')
    
    context = {
        'weaviate_data': weaviate_data,
        'total_count': len(weaviate_data)
    }
    return render(request, 'dashboard/admin_weaviate.html', context)

@login_required
def delete_weaviate_entry(request, content_hash):
    """Delete entry from Weaviate by content hash"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    if request.method == 'POST':
        documents = get_collection()
        if documents:
            try:
                where_filter = {
                    "path": ["content_hash"],
                    "operator": "Equal",
                    "valueText": content_hash
                }
                
                # Get the document ID first
                result = documents.query.get("TenderDocument", ["_additional {id}"]).with_where(where_filter).with_limit(1).do()
                entries = result.get("data", {}).get("Get", {}).get("TenderDocument", [])
                
                if entries:
                    doc_id = entries[0]["_additional"]["id"]
                    documents.data_object.delete(doc_id, "TenderDocument")
                    messages.success(request, 'Entry deleted successfully from Weaviate')
                else:
                    messages.error(request, 'Entry not found in Weaviate')
            except Exception as e:
                messages.error(request, f'Error deleting from Weaviate: {e}')
    
    return redirect('admin_weaviate')

@login_required
def view_weaviate_summary(request, content_hash):
    """View detailed summary from Weaviate"""
    if not request.user.is_staff:
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('dashboard')
    
    documents = get_collection()
    summary_data = None
    
    if documents:
        try:
            where_filter = {
                "path": ["content_hash"],
                "operator": "Equal",
                "valueText": content_hash
            }
            
            result = documents.query.get("TenderDocument", ["file_name", "time_created", "summary", "text_content"]).with_where(where_filter).with_limit(1).do()
            entries = result.get("data", {}).get("Get", {}).get("TenderDocument", [])
            
            if entries:
                summary_data = entries[0]
        except Exception as e:
            messages.error(request, f'Error fetching summary: {e}')
    
    context = {
        'summary_data': summary_data,
        'content_hash': content_hash
    }
    return render(request, 'dashboard/view_weaviate_summary.html', context)
@login_required
def view_document_content(request, document_id):
    """View the text content of a document"""
    document = get_object_or_404(Document, pk=document_id)
    
    try:
        text_content = extract_text_from_pdf(document.file.path)
        if not text_content.strip():
            text_content = "No text content could be extracted from this document."
    except Exception as e:
        text_content = f"Error extracting text: {str(e)}"
    
    context = {
        'document': document,
        'text_content': text_content,
        'filename': os.path.basename(document.file.name)
    }
    return render(request, 'dashboard/view_document_content.html', context)
