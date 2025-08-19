# views.py
import pandas as pd
from django.shortcuts import render, redirect
from .forms import FusionForm
from django.http import HttpResponse
import io
import base64

def nettoyer_dataframe(df):
    df.columns = df.columns.str.strip()
    df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
    df.dropna(how='all', inplace=True)
    return df

def fusion_excel_view(request):
    fusion_result = None
    stats = {}
    colonne_commune = None
    selected_column = None
    error = None

    if request.method == 'POST':
        form = FusionForm(request.POST, request.FILES)
        if form.is_valid():
            fichier1 = form.cleaned_data['fichier1']
            fichier2 = form.cleaned_data['fichier2']
            selected_column = request.POST.get('colonne_commune')
            format_export = request.POST.get('format_export', 'xlsx')

            try:
                df1 = pd.read_excel(fichier1)
                df2 = pd.read_excel(fichier2)

                df1 = nettoyer_dataframe(df1)
                df2 = nettoyer_dataframe(df2)

                if not selected_column:
                    common_cols = df1.columns.intersection(df2.columns)
                    if len(common_cols) == 0:
                        error = "❌ Aucune colonne commune trouvée."
                        return render(request, 'fusion.html', {'form': form, 'error': error})
                    colonne_commune = common_cols[0]
                else:
                    colonne_commune = selected_column

                merged_df = pd.merge(df1, df2, on=colonne_commune, how='inner')
                fusion_result = merged_df.to_dict(orient='records')

                stats = {
                    'nb_lignes': len(merged_df),
                    'nb_colonnes': len(merged_df.columns),
                    'colonnes': list(merged_df.columns),
                    'doublons': merged_df.duplicated().sum(),
                }


                # Exporter dans un buffer
                output = io.BytesIO()
                if format_export == 'csv':
                    merged_df.to_csv(output, index=False)
                    content_type = 'text/csv'
                    filename = 'fusion.csv'
                elif format_export == 'json':
                    merged_df.to_json(output, orient='records')
                    content_type = 'application/json'
                    filename = 'fusion.json'
                else:
                    merged_df.to_excel(output, index=False)
                    content_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                    filename = 'fusion.xlsx'

                # Encode le contenu en base64 pour stocker en session
                output.seek(0)
                encoded_file = base64.b64encode(output.read()).decode()

                # Stocker en session
                request.session['fusion_file'] = encoded_file
                request.session['fusion_filename'] = filename
                request.session['fusion_content_type'] = content_type

                # Si on veut seulement afficher le résultat sans télécharger, on rend la page
                if 'download' not in request.POST:
                    return render(request, 'fusion.html', {
                        'form': form,
                        'fusion_result': fusion_result,
                        'stats': stats,
                        'colonne_commune': colonne_commune,
                        'error': error,
                    })

                # Sinon, rediriger vers la vue de téléchargement
                return redirect('telecharger_fichier')

            except Exception as e:
                error = f"Erreur lors de la fusion : {str(e)}"
    else:
        form = FusionForm()

    return render(request, 'fusion.html', {
        'form': form,
        'fusion_result': fusion_result,
        'stats': stats,
        'colonne_commune': colonne_commune,
        'error': error,
    })


from django.views.decorators.http import require_GET

@require_GET
def telecharger_fichier(request):
    encoded_file = request.session.get('fusion_file')
    filename = request.session.get('fusion_filename', 'fusion.xlsx')
    content_type = request.session.get('fusion_content_type', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

    if not encoded_file:
        return HttpResponse("Aucun fichier à télécharger.", status=404)

    file_bytes = base64.b64decode(encoded_file)
    response = HttpResponse(file_bytes, content_type=content_type)
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # Optionnel : supprimer le fichier de la session après téléchargement
    del request.session['fusion_file']
    del request.session['fusion_filename']
    del request.session['fusion_content_type']

    return response
