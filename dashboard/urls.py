from django.urls import path
from .views import (
    dashboard_view, upload_file_view, document_detail_view, 
    process_document_view, view_document_file, view_summary_file,
    search_documents, search_logs_view, manage_api_keys, delete_document_view,
    document_management_view, bulk_download_documents, get_summary_view,
    admin_weaviate_view, delete_weaviate_entry, view_weaviate_summary,
    view_document_content
)

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('upload/', upload_file_view, name='upload_file'),
    path('documents/', document_management_view, name='document_management'),
    path('documents/bulk-download/', bulk_download_documents, name='bulk_download_documents'),
    path('document/<int:document_id>/', document_detail_view, name='document_detail'),
    path('document/<int:document_id>/process/', process_document_view, name='process_document'),
    path('document/<int:document_id>/view/', view_document_file, name='view_document'),
    path('document/<int:document_id>/content/', view_document_content, name='view_document_content'),
    path('document/<int:document_id>/summary/', get_summary_view, name='view_summary'),
    path('document/<int:document_id>/delete/', delete_document_view, name='delete_document'),
    path('search/', search_documents, name='search_documents'),
    path('search-logs/', search_logs_view, name='search_logs'),
    path('api-keys/', manage_api_keys, name='manage_api_keys'),
    path('admin/weaviate/', admin_weaviate_view, name='admin_weaviate'),
    path('admin/weaviate/delete/<str:content_hash>/', delete_weaviate_entry, name='delete_weaviate_entry'),
    path('admin/weaviate/view/<str:content_hash>/', view_weaviate_summary, name='view_weaviate_summary'),
]