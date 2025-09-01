from django.urls import path
from .views import (
    dashboard_view, upload_file_view, document_detail_view, 
    process_document_view, view_document_file, view_summary_file
)

urlpatterns = [
    path('', dashboard_view, name='dashboard'),
    path('upload/', upload_file_view, name='upload_file'),
    path('document/<int:document_id>/', document_detail_view, name='document_detail'),
    path('document/<int:document_id>/process/', process_document_view, name='process_document'),
    path('document/<int:document_id>/view/', view_document_file, name='view_document'),
    path('document/<int:document_id>/summary/', view_summary_file, name='view_summary'),
]