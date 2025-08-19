from django.urls import path
from .views import fusion_excel_view,telecharger_fichier

urlpatterns = [
    path('', fusion_excel_view, name='fusion_excel'),
    path('download/', telecharger_fichier, name='telecharger_fichier'),
]
