from django.urls import path
from .views import (
    dashboard_view, upload_file_view, document_detail_view, 
    process_document_view, view_document_file, view_summary_file,
    search_documents, search_logs_view, manage_api_keys, delete_document_view,
    document_management_view, bulk_download_documents
)

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('upload/', upload_file_view, name='upload_file'),
    path('documents/', document_management_view, name='document_management'),
    path('documents/bulk-download/', bulk_download_documents, name='bulk_download_documents'),
    path('document/<int:document_id>/', document_detail_view, name='document_detail'),
    path('document/<int:document_id>/process/', process_document_view, name='process_document'),
    path('document/<int:document_id>/view/', view_document_file, name='view_document'),
    path('document/<int:document_id>/summary/', view_summary_file, name='view_summary'),
    path('document/<int:document_id>/delete/', delete_document_view, name='delete_document'),
    path('search/', search_documents, name='search_documents'),
    path('search-logs/', search_logs_view, name='search_logs'),
    path('api-keys/', manage_api_keys, name='manage_api_keys'),
]