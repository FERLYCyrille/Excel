from django import forms

class FusionForm(forms.Form):
    fichier1 = forms.FileField(label="Premier fichier Excel/CSV")
    fichier2 = forms.FileField(label="Deuxième fichier Excel/CSV")
    colonne_commune = forms.CharField(label="Colonne pour la fusion (ex: email)", max_length=100)
    format_export = forms.ChoiceField(
        choices=[('xlsx', 'Excel (.xlsx)'), ('csv', 'CSV (.csv)'), ('json', 'JSON')],
        label="Format d'export"
    )
