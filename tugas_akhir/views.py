# tugas_akhir/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import FileResponse, HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.db.models import Q
from django.core.paginator import Paginator

from users.models import Mahasiswa
from .models import Dokumen, TugasAkhir
from .forms import DokumenEditForm

def document_list_view(request):
    """
    Fetches all documents and renders them in the core/documents.html template.
    """
    search_query = request.GET.get('q', '')

    # Start with the base queryset
    document_queryset = Dokumen.objects.select_related(
        'pemilik__user', 'pemilik__program_studi'
    ).order_by('-uploaded_at')

    # If a search query is provided, filter the queryset
    if search_query:
        document_queryset = document_queryset.filter(
            Q(nama_dokumen__icontains=search_query) |
            Q(pemilik__user__first_name__icontains=search_query) |
            Q(pemilik__user__last_name__icontains=search_query)
        )

    # Set up Pagination
    paginator = Paginator(document_queryset, 5)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'documents': page_obj,
        'bab_choices': Dokumen.BAB_CHOICES,
        'status_choices': Dokumen.STATUS_CHOICES,
        'tugas_akhirs': TugasAkhir.objects.all(),
        'mahasiswas': Mahasiswa.objects.select_related('user').all(),
    }

    return render(request, 'core/documents.html', context)

@login_required
def serve_document_file_view(request, pk):
    """
    Handles serving a file either for inline viewing or as a forced download.
    """
    document = get_object_or_404(Dokumen, pk=pk)

    # Check for a query parameter to decide the action
    action = request.GET.get('action')

    if action == 'download':
        # Force download by setting specific response headers
        response = HttpResponse(document.file, content_type='application/octet-stream')
        response['Content-Disposition'] = f'attachment; filename="{document.file.name}"'
        return response
    else:
        # Default to opening in a new tab (inline view)
        # FileResponse is optimized for this and sets the correct Content-Type
        return FileResponse(document.file.open('rb'))


# --- VIEW for deleting documents ---
@require_POST  # Ensures this view can only be accessed with a POST request
@login_required
def delete_document_view(request, pk):
    """
    Handles the deletion of a document and its associated file.
    """
    document = get_object_or_404(Dokumen, pk=pk)

    try:
        # First, delete the physical file from storage
        document.file.delete(save=False)
        # Then, delete the model record from the database
        document.delete()
        # Add a success message for the user
        messages.success(request, f"Dokumen '{document.nama_dokumen}' telah berhasil dihapus.")
    except Exception as e:
        messages.error(request, f"Terjadi kesalahan saat menghapus dokumen: {e}")

    # Redirect back to the document list page
    return redirect('tugas_akhir:document-list')

@login_required
def edit_document_view(request, pk):
    document = get_object_or_404(Dokumen, pk=pk)

    # You might want more robust permissions here, e.g., only staff/admins can edit
    # if not request.user.is_staff:
    #     return JsonResponse({'error': 'You do not have permission to edit.'}, status=403)

    if request.method == 'POST':
        form = DokumenEditForm(request.POST, request.FILES, instance=document)
        if form.is_valid():
            updated_doc = form.save()
            response_data = {
                'success': True,
                'document': {
                    'bab': updated_doc.get_bab_display(),
                    'nama_dokumen': updated_doc.nama_dokumen,
                    'status': updated_doc.get_status_display(),
                    'pemilik_name': updated_doc.pemilik.user.get_full_name(),
                    'pemilik_prodi': updated_doc.pemilik.program_studi.nama_prodi,
                    'file_url': updated_doc.file.url if updated_doc.file else '#',
                }
            }
            return JsonResponse(response_data)
        else:
            return JsonResponse({'success': False, 'errors': form.errors}, status=400)

    else:
        data = {
            'tugas_akhir': document.tugas_akhir_id,
            'bab': document.bab,
            'nama_dokumen': document.nama_dokumen,
            'status': document.status,
            'pemilik': document.pemilik_id,
            'current_file_url': document.file.url if document.file else None,
            'current_file_name': document.file.name.split('/')[-1] if document.file else 'No file uploaded',
        }
        return JsonResponse(data)
