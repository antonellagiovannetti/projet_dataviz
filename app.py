"""Allergy Atlas compact — two-tab clinical cohort explorer. Run: python app.py"""
from pathlib import Path
import os
import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, dcc, html
from src.data_loader import load_data
from src.clustering import get_profiles
from src.charts import (common_count_histogram, top_allergens, clinical_differential,
                        pca_scatter, cluster_excess, cohort_difference, empty_figure)
from src.insights import clinical_example
from src.metrics import filter_cohort, summary_metrics

ROOT = Path(__file__).resolve().parent
DS = load_data()
# Compute the original fixed exploratory clusters once, with no clinical labels.
MODEL = get_profiles()
ALLERGENS = DS.common_allergens
FULL = MODEL.frame
APP_TITLE = "Allergy Atlas | Explorer une cohorte en allergologie"
app = Dash(__name__, title=APP_TITLE, assets_folder=str(ROOT / 'assets'))
server = app.server


def graph(graph_id):
    return dcc.Graph(id=graph_id, config={'displaylogo':False, 'modeBarButtonsToRemove':['toImage','autoScale2d']},
                     responsive=True, className='compact-graph')


def tile(label, value_id, sub=None):
    return html.Div([html.Small(label), html.Strong(id=value_id), html.Span(sub or '')], className='compact-kpi')


def panel(title, body, subtitle=None, extra=None):
    return html.Section([html.Div([html.H2(title), html.Small(subtitle or '')], className='compact-panel-title'),
                         body, extra or html.Span()], className='compact-panel')


def header_controls():
    return html.Div([
        html.Div([html.Label('Population'), dcc.Dropdown(id='compact-pop', value='all', clearable=False,
               options=[{'label':x,'value':v} for v,x in [('all','Tous les patients'),('children','Moins de 18 ans'),('adults','18 ans et plus')]])]),
        html.Div([html.Label('Technologie'), dcc.Dropdown(id='compact-chip', value='all', clearable=False,
               options=[{'label':'Toutes les puces','value':'all'}]+[{'label':c,'value':c} for c in ['ISAC V1','ISAC V2','ALEX']])]),
        html.Div([html.Label('Information clinique'), dcc.Dropdown(id='compact-outcome', value='skin', clearable=False,
               options=[{'label':x,'value':v} for v,x in [('skin','Symptômes cutanés'),('asthma','Traitement asthme'),('rhinitis','Traitement rhinite'),('dermatitis','Traitement dermatite')]])]),
        html.Div([html.Label('Groupe clinique'), dcc.Dropdown(id='compact-status', value='all', clearable=False,
               options=[{'label':'Tous (dont inconnus)','value':'all'},{'label':'Oui','value':'Oui'},{'label':'Non','value':'Non'}])]),
    ], className='compact-filters')


app.layout = html.Div([
    html.Header([html.Div([html.Div('AA', className='compact-monogram'),
                 html.Div([html.H1('Allergy Atlas'), html.P('Explorer une cohorte pour la recherche clinique en allergologie')])], className='compact-brand'),
                 html.Div([html.Span('ACC · 4 271 patients · 91 allergènes comparables'),
                 html.Span('Exploration, pas diagnostic', className='compact-disclaimer')], className='compact-header-right')], className='compact-header'),
    html.Div([html.Strong('Question de recherche'), html.Span('Comment les profils de sensibilisation IgE se structurent-ils dans ACC, et quels liens présentent-ils avec les manifestations cliniques disponibles ?')], className='compact-question'),
    html.Div([header_controls(), html.Div(id='compact-selection', className='compact-selection')], className='compact-controls'),
    dcc.Tabs(id='compact-tab', value='synthesis', className='compact-tabs', children=[
        dcc.Tab(label='01 · Identifier les profils IgE', value='synthesis', className='compact-tab', selected_className='compact-tab-selected'),
        dcc.Tab(label='02 · Explorer les liens cliniques', value='profiles', className='compact-tab', selected_className='compact-tab-selected')]),
    html.Main([
       html.Div(id='compact-intro', className='compact-intro'),
       html.Div([tile('Patients dans la sélection', 'compact-patients'),tile('Détections médianes / 91','compact-median'),
                 tile('Profils analysables','compact-complete'),tile('Données cliniques Oui / Non','compact-known')], className='compact-kpis'),
       html.Div(id='compact-synthesis', children=[
           panel('1 · Combien de détections par patient ?', graph('compact-count'), 'Distribution sur les 91 allergènes communs'),
           panel('2 · Quels allergènes sont les plus détectés ?', graph('compact-top'), 'Fréquence descriptive des IgE > 0'),
           panel('3 · Quels profils se ressemblent ?', graph('compact-pca'), 'Projection PCA des profils IgE comparables'),
           panel('4 · Qu’est-ce qui distingue les groupes ?', graph('compact-excess'), 'Différences biologiques exploratoires'),
       ], className='compact-grid'),
       html.Div(id='compact-profiles', children=[
           panel('1 · Quels liens avec les symptômes ?', graph('compact-clinical'), 'Écart de détection entre Oui et Non'),
           panel('2 · Les groupes diffèrent-ils cliniquement ?', graph('compact-cluster-clinical'), 'Parmi les statuts cliniques connus'),
           panel('3 · Les différences changent-elles avec l’âge ?', graph('compact-cohort'), 'Comparaison descriptive enfants / adultes'),
           panel('4 · Réponse et limites', html.Div(id='compact-takeaway', className='compact-takeaway'), 'Interprétation et prudence'),
       ], className='compact-grid', style={'display':'none'}),
    ], className='compact-main'),
    html.Footer([html.Span('Source : Allergen Chip Challenge · SFA / Health Data Hub'),
                 html.Details([html.Summary('Méthode et limites'), html.P('Une détection correspond ici à une mesure IgE strictement supérieure à zéro ; cela ne suffit pas à poser un diagnostic. Les trois puces n’ont pas les mêmes couvertures : les comparaisons transversales utilisent 91 allergènes communs. Les codes cliniques inconnus ne sont jamais assimilés à Non. Les groupes KMeans sont exploratoires et la sévérité clinique ne peut pas être prédite avec le CSV disponible.')], className='compact-method'),
                 html.Span('Vue optimisée pour ordinateur ≥ 1366 × 768')], className='compact-footer'),
], className='compact-app')


def resize(fig):
    fig.update_layout(height=None, autosize=True, margin=dict(l=55,r=16,t=30,b=42),
                      font=dict(size=10), legend=dict(font=dict(size=9)))
    return fig


@app.callback(Output('compact-synthesis','style'),Output('compact-profiles','style'),
              Output('compact-intro','children'), Input('compact-tab','value'))
def show_tab(tab):
    if tab == 'profiles':
        return {'display':'none'}, {}, [html.Strong('Étape 2 / 2 · Quelles associations cliniques ?'),
            html.Span(' Comparons les taux de détection et la composition clinique des profils : associations descriptives, pas causalité ni sévérité.')] 
    return {}, {'display':'none'}, [html.Strong('Étape 1 / 2 · Quels profils biologiques ?'),
        html.Span(' Décrire la diversité, les allergènes dominants et les regroupements, avant d’explorer les manifestations cliniques.')] 


@app.callback(Output('compact-patients','children'),Output('compact-median','children'),
              Output('compact-complete','children'),Output('compact-known','children'),
              Output('compact-selection','children'), Output('compact-count','figure'),
              Output('compact-top','figure'),Output('compact-clinical','figure'),
              Output('compact-takeaway','children'),Output('compact-pca','figure'),
              Output('compact-excess','figure'),Output('compact-cohort','figure'),
              Output('compact-cluster-clinical','figure'),
              Input('compact-pop','value'),Input('compact-chip','value'),
              Input('compact-outcome','value'),Input('compact-status','value'))
def update(pop, chip, outcome, status):
    conditions = {}
    if chip != 'all': conditions['chip'] = [chip]
    if status != 'all': conditions[outcome] = [status]
    frame = filter_cohort(FULL, conditions)
    if pop == 'children': frame = frame.loc[frame.age.lt(18)]
    if pop == 'adults': frame = frame.loc[frame.age.ge(18)]
    n = len(frame)
    known = int(frame[outcome].isin(['Oui','Non']).sum())
    complete = int(frame.common_complete.sum())
    median = frame.common_count.dropna().median()
    median_label = f'{median:.0f}' if np.isfinite(median) else '—'
    figs = [resize(common_count_histogram(frame)),
            resize(top_allergens(frame,ALLERGENS,top_n=8)),
            resize(clinical_differential(frame,outcome,ALLERGENS,top_n=7))]
    sample = clinical_example(frame,ALLERGENS,outcome)
    if sample['available']:
        clinical_text = f"Ara h 2 : {sample['yes_rate']:.1f} % (Oui, n={sample['yes_n']}) contre {sample['no_rate']:.1f} % (Non, n={sample['no_n']}). Écart : {sample['difference']:+.1f} points."
    else:
        clinical_text = 'Comparaison Ara h 2 non calculable pour cette sélection.'
    takeaway = [html.H3('Ce que répondent les données'),
                html.P(clinical_text),
                html.P(f'Information clinique exploitable : {known:,} / {n:,} patients.'.replace(',',' ')),
                html.P('Les groupes IgE et les écarts cliniques sont des pistes de recherche, pas des diagnostics.'),
                html.P('Les données ne permettent ni d’inférer une cause ni de prédire la sévérité.'),
                html.Details([html.Summary('Méthode : quelles comparaisons ?'), html.P('IgE > 0 est un seuil descriptif. Les comparaisons transversales utilisent les 91 allergènes communs ; les inconnus cliniques sont exclus des taux Oui / Non.')])]
    # The fixed model was fitted on the full cohort; filters only select visible patients.
    projection = frame.loc[frame.common_complete]
    pca = resize(pca_scatter(projection, MODEL.explained_variance))
    valid_groups = sorted([str(v) for v in frame.cluster.dropna().unique() if str(v).isdigit()])
    selected_group = valid_groups[-1] if valid_groups else None
    excess = resize(cluster_excess(frame,ALLERGENS, selected_cluster=selected_group,top_n=8)) if selected_group else resize(empty_figure())
    child = frame.loc[frame.age.lt(18)]; adult = frame.loc[frame.age.ge(18)]
    cohorts = resize(cohort_difference(child,adult,ALLERGENS,top_n=8)) if len(child) and len(adult) else resize(empty_figure('Comparaison impossible : enfants et adultes requis.'))
    rates = []
    for group in sorted(str(g) for g in frame.cluster.dropna().unique() if str(g).isdigit()):
        members = frame.loc[frame.cluster.astype(str).eq(group)]
        known_group = members.loc[members[outcome].isin(['Oui', 'Non'])]
        if len(known_group):
            yes = int(known_group[outcome].eq('Oui').sum())
            rates.append((f'Profil {group}', 100*yes/len(known_group), len(known_group), yes))
    if rates:
        cluster_clinical = go.Figure(go.Bar(x=[r[0] for r in rates], y=[r[1] for r in rates],
            text=[f'{r[1]:.1f} %' for r in rates], textposition='outside', marker_color='#198a85',
            customdata=[[r[2],r[3]] for r in rates],
            hovertemplate='%{x}<br>Oui : %{customdata[1]} / %{customdata[0]} renseignés<br>%{y:.1f} %<extra></extra>'))
        cluster_clinical.update_layout(yaxis=dict(title='% de Oui parmi les connus',range=[0, 110]),
            xaxis=dict(title='Groupes exploratoires'))
    else:
        cluster_clinical = empty_figure('Pas de comparaison clinique calculable dans cette sélection.')
    cluster_clinical = resize(cluster_clinical)
    return (f'{n:,}'.replace(',',' '),median_label,f'{complete:,}'.replace(',',' '),
            f'{known:,} / {n:,}'.replace(',',' '),f'{n:,} patients sélectionnés · {n/len(FULL)*100:.1f} % du fichier'.replace(',',' ',1),
            *figs,takeaway,pca,excess,cohorts,cluster_clinical)


if __name__ == '__main__':
    app.run(host='127.0.0.1',port=int(os.environ.get('PORT','8050')),debug=False)
