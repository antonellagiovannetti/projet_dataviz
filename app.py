"""Allergy Atlas: two coordinated views of the fixed ACC cohort. Run: python app.py."""
from pathlib import Path
import json
import os

import numpy as np
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, ctx, dcc, html, no_update

from src.data_loader import load_data
from src.clustering import get_profiles
from src.charts import (
    common_count_histogram, top_allergens, clinical_differential,
    pca_scatter, cluster_excess, cohort_difference, empty_figure,
)
from src.insights import clinical_focus
from src.metrics import filter_cohort, cohort_difference as difference_statistics

ROOT = Path(__file__).resolve().parent
DS = load_data()
# The model is fitted once without clinical labels; interaction never refits it.
MODEL = get_profiles()
ALLERGENS = DS.common_allergens
FULL = MODEL.frame
OUTCOMES = {
    'skin': 'Symptômes cutanés', 'asthma': 'Traitement asthme',
    'rhinitis': 'Traitement rhinite', 'dermatitis': 'Traitement dermatite',
}
app = Dash(__name__, title='Allergy Atlas | Explorer une cohorte en allergologie',
           assets_folder=str(ROOT / 'assets'))
server = app.server


def number(value):
    return f'{value:,}'.replace(',', ' ')


def graph(graph_id):
    return dcc.Graph(
        id=graph_id, responsive=True, className='compact-graph',
        config={'displaylogo': False, 'displayModeBar': graph_id == 'compact-pca',
                'modeBarButtonsToRemove': ['toImage', 'autoScale2d', 'select2d', 'lasso2d']},
    )


def tile(label, value_id):
    return html.Div([html.Small(label), html.Strong(id=value_id)], className='compact-kpi')


def panel(title, body, subtitle='', subtitle_id=None):
    small = html.Small(subtitle, id=subtitle_id) if subtitle_id else html.Small(subtitle)
    return html.Section([
        html.Div([html.H2(title), small], className='compact-panel-title'), body,
    ], className='compact-panel')


def control(label, component, component_id):
    return html.Div([html.Label(label, htmlFor=component_id), component])


def header_controls():
    return html.Div([
        control('Population', dcc.Dropdown(
            id='compact-pop', value='all', clearable=False,
            options=[{'label': label, 'value': value} for value, label in [
                ('all', 'Tous les patients'), ('children', 'Moins de 18 ans'),
                ('adults', '18 ans et plus')]],
        ), 'compact-pop'),
        control('Technologie', dcc.Dropdown(
            id='compact-chip', value='all', clearable=False,
            options=[{'label': 'Toutes les puces', 'value': 'all'}]
                    + [{'label': chip, 'value': chip} for chip in ['ISAC V1', 'ISAC V2', 'ALEX']],
        ), 'compact-chip'),
        control('Information clinique', dcc.Dropdown(
            id='compact-outcome', value='skin', clearable=False,
            options=[{'label': label, 'value': value} for value, label in OUTCOMES.items()],
        ), 'compact-outcome'),
        control('Groupe clinique', dcc.Dropdown(
            id='compact-status', value='all', clearable=False,
            options=[{'label': 'Tous (dont inconnus)', 'value': 'all'},
                     {'label': 'Oui', 'value': 'Oui'}, {'label': 'Non', 'value': 'Non'}],
        ), 'compact-status'),
    ], className='compact-filters')


app.layout = html.Div([
    html.Header([
        html.Div([html.Div('AA', className='compact-monogram'), html.Div([
            html.H1('Allergy Atlas'),
            html.P('Explorer une cohorte pour la recherche clinique en allergologie'),
        ])], className='compact-brand'),
        html.Div([
            html.Span('Exploration, pas diagnostic', className='compact-disclaimer'),
        ], className='compact-header-right'),
    ], className='compact-header'),
    html.Div([
        html.Strong('Question de recherche'),
        html.Span('Comment les profils de sensibilisation IgE se structurent-ils dans ACC, '
                  'et quels liens présentent-ils avec les manifestations cliniques disponibles ?'),
    ], className='compact-question'),
    html.Div([
        html.Div([
            header_controls(),
        ], className='compact-filter-row'),
        html.Div([
            control('Allergène à suivre', dcc.Dropdown(
                id='compact-focus-allergen', value=None, clearable=True,
                placeholder='Choisir ou cliquer une barre',
                options=[{'label': name.replace('_', ' '), 'value': name} for name in sorted(ALLERGENS)],
            ), 'compact-focus-allergen'),
            control('Profil à explorer', dcc.Dropdown(
                id='compact-focus-profile', value=None, clearable=True,
                placeholder='Choisir ou cliquer un point PCA', options=[],
            ), 'compact-focus-profile'),
            html.Button('Réinitialiser les filtres', id='compact-reset', n_clicks=0,
                        className='compact-reset', title='Rétablir les filtres et les sélections'),
            html.Div(id='compact-selection', className='compact-selection',
                     role='status', **{'aria-live': 'polite'}),
        ], className='compact-focus-row'),
    ], className='compact-controls'),
    dcc.Tabs(id='compact-tab', value='synthesis', className='compact-tabs', children=[
        dcc.Tab(label='01 · Identifier les profils IgE', value='synthesis',
                className='compact-tab', selected_className='compact-tab-selected'),
        dcc.Tab(label='02 · Explorer les liens cliniques', value='profiles',
                className='compact-tab', selected_className='compact-tab-selected'),
    ]),
    html.Main([
        html.Div(id='compact-intro', className='compact-intro'),
        html.Div([
            tile('Patients dans les filtres', 'compact-patients'),
            tile(f'Détections médianes / {len(ALLERGENS)}', 'compact-median'),
            tile('Profils analysables', 'compact-complete'),
            tile('Données cliniques Oui / Non', 'compact-known'),
        ], className='compact-kpis'),
        html.Div(id='compact-synthesis', children=[
            panel('1 · Combien de détections par patient ?', graph('compact-count'),
                  'Panel commun · survol pour les effectifs'),
            panel('2 · Quels allergènes sont les plus détectés ?', graph('compact-top'),
                  'Cliquer une barre pour suivre cet allergène'),
            panel('3 · Quels profils se ressemblent ?', graph('compact-pca'),
                  'Un point = un patient · proximité ≈ profils similaires · cliquer un point'),
            panel('4 · Qu’est-ce qui distingue le profil ?', graph('compact-excess'),
                  subtitle_id='compact-excess-subtitle'),
        ], className='compact-grid'),
        html.Div(id='compact-profiles', children=[
            panel('1 · Quels liens avec l’information clinique ?', graph('compact-clinical'),
                  subtitle_id='compact-clinical-subtitle'),
            panel('2 · Les groupes diffèrent-ils cliniquement ?', graph('compact-cluster-clinical'),
                  'Tous les profils des filtres · cliquer un profil'),
            panel('3 · Les signatures IgE diffèrent-elles selon l’âge ?', graph('compact-cohort'),
                  subtitle_id='compact-cohort-subtitle'),
            panel('4 · Réponse et limites',
                  html.Div(id='compact-takeaway', className='compact-takeaway',
                           **{'aria-live': 'polite'}), 'Synthèse de la vue actuelle'),
        ], className='compact-grid', style={'display': 'none'}),
    ], className='compact-main'),
    html.Footer([
        html.Span('Source : Allergen Chip Challenge · SFA / Health Data Hub'),
    ], className='compact-footer'),
], className='compact-app')


def cohort(pop, chip, outcome, status):
    conditions = {}
    if chip != 'all':
        conditions['chip'] = [chip]
    if status != 'all':
        conditions[outcome] = [status]
    frame = filter_cohort(FULL, conditions)
    if pop == 'children':
        frame = frame.loc[frame.age.lt(18)]
    elif pop == 'adults':
        frame = frame.loc[frame.age.ge(18)]
    return frame


def groups(frame):
    return sorted({str(value) for value in frame.cluster.dropna() if str(value).isdigit()}, key=int)


@app.callback(
    Output('compact-pop', 'value'), Output('compact-chip', 'value'),
    Output('compact-outcome', 'value'), Output('compact-status', 'value'),
    Output('compact-focus-allergen', 'value'), Output('compact-focus-profile', 'value'),
    Output('compact-top', 'clickData'), Output('compact-clinical', 'clickData'),
    Output('compact-excess', 'clickData'), Output('compact-cohort', 'clickData'),
    Output('compact-pca', 'clickData'), Output('compact-cluster-clinical', 'clickData'),
    Input('compact-reset', 'n_clicks'),
    Input('compact-pop', 'value'), Input('compact-chip', 'value'),
    Input('compact-outcome', 'value'), Input('compact-status', 'value'),
    Input('compact-top', 'clickData'), Input('compact-clinical', 'clickData'),
    Input('compact-excess', 'clickData'), Input('compact-cohort', 'clickData'),
    Input('compact-pca', 'clickData'), Input('compact-cluster-clinical', 'clickData'),
    State('compact-focus-allergen', 'value'), State('compact-focus-profile', 'value'),
    prevent_initial_call=True,
)
def controls(reset, pop, chip, outcome, status, top, clinical, excess, age,
             pca, cluster_clinical, selected_allergen, selected_profile):
    unchanged = [no_update] * 12
    triggered = ctx.triggered_prop_ids
    if 'compact-reset.n_clicks' in triggered:
        return ('all', 'all', 'skin', 'all', None, None) + (None,) * 6
    if any(f'{name}.value' in triggered for name in
           ['compact-pop', 'compact-chip', 'compact-outcome', 'compact-status']):
        # A profile belongs to the previous cohort. Allergen focus remains a comparison aid.
        unchanged[5] = None
        unchanged[6:] = [None] * 6
        return tuple(unchanged)
    events = {'compact-top': top, 'compact-clinical': clinical, 'compact-excess': excess,
              'compact-cohort': age, 'compact-pca': pca,
              'compact-cluster-clinical': cluster_clinical}
    event_id = ctx.triggered_id
    event = events.get(event_id)
    points = event.get('points') if isinstance(event, dict) else None
    if not isinstance(points, (list, tuple)) or not points:
        return tuple(unchanged)
    point = points[0]
    custom = point.get('customdata') if isinstance(point, dict) else None
    if not isinstance(custom, (list, tuple)):
        return tuple(unchanged)
    if event_id in ['compact-pca', 'compact-cluster-clinical']:
        index = 5 if event_id == 'compact-pca' else 0
        candidate = str(custom[index]) if len(custom) > index else None
        if candidate in groups(cohort(pop, chip, outcome, status)):
            unchanged[5] = candidate
    elif custom and custom[0] in ALLERGENS:
        unchanged[4] = custom[0]
    if unchanged[4] is not no_update or unchanged[5] is not no_update:
        # Consume events so clicking the same mark after clearing focus fires again.
        unchanged[6:] = [None] * 6
    return tuple(unchanged)


@app.callback(Output('compact-synthesis', 'style'), Output('compact-profiles', 'style'),
              Output('compact-intro', 'children'), Input('compact-tab', 'value'))
def show_tab(tab):
    if tab == 'profiles':
        return {'display': 'none'}, {}, [
            html.Strong('Étape 2 / 2 · Quels liens entre profils IgE et manifestations cliniques ?'),
        ]
    return {}, {'display': 'none'}, [
        html.Strong('Étape 1 / 2 · Comment se structurent les profils IgE ?'),
    ]


def resize(fig, revision, note=None):
    # Compact panels put the footer context in subtitles, hovers and the method.
    # Keep empty-state annotations, and use one line above each actual plot.
    annotations = []
    for annotation in fig.layout.annotations or []:
        if annotation.yref == 'paper' and annotation.y == 0 and (annotation.yshift or 0) < 0:
            continue
        if annotation.yref == 'paper' and annotation.y is not None and annotation.y > 1:
            annotation.text = note or annotation.text.replace('<br>', ' ')
            annotation.font.size = 9
        annotations.append(annotation)
    fig.layout.annotations = annotations
    fig.update_layout(height=None, autosize=True, margin=dict(l=55, r=16, t=28, b=42),
                      font=dict(size=10), legend=dict(font=dict(size=9)), uirevision=revision)
    return fig


def clinical_profiles(frame, outcome, selected_profile):
    rates = []
    for group in groups(frame):
        members = frame.loc[frame.cluster.astype(str).eq(group)]
        known = members.loc[members[outcome].isin(['Oui', 'Non'])]
        if len(known):
            yes = int(known[outcome].eq('Oui').sum())
            rates.append((group, 100 * yes / len(known), len(known), yes, len(members) - len(known)))
    if not rates:
        return empty_figure('Aucun profil avec statut clinique Oui / Non renseigné.')
    selected = [r[0] == selected_profile for r in rates]
    fig = go.Figure(go.Bar(
        x=[f'Profil {r[0]}' + (' (sélection)' if focus else '') for r, focus in zip(rates, selected)],
        y=[r[1] for r in rates], text=[f'{r[1]:.1f} %' for r in rates],
        textposition='outside', cliponaxis=False,
        marker=dict(color=['#182c47' if focus else '#198a85' for focus in selected],
                    opacity=[1 if focus or not selected_profile else .35 for focus in selected],
                    line=dict(color='#182c47', width=[2 if focus else 0 for focus in selected])),
        customdata=[[r[0], r[2], r[3], r[4]] for r in rates],
        hovertemplate='Profil %{customdata[0]}<br>Oui : %{customdata[2]} / %{customdata[1]} connus'
                      '<br>Inconnus exclus : %{customdata[3]}<br>%{y:.1f} %'
                      '<br>Cliquer pour explorer ce profil<extra></extra>',
    ))
    fig.update_layout(template='plotly_white', paper_bgcolor='rgba(0,0,0,0)',
                      plot_bgcolor='rgba(0,0,0,0)', clickmode='event', dragmode=False,
                      yaxis=dict(title='% de Oui parmi les connus', range=[0, 110], fixedrange=True),
                      xaxis=dict(title='Profils des filtres · inconnus exclus', fixedrange=True))
    return fig


def takeaway(frame, detail, outcome, selected_allergen, selected_profile):
    evidence = clinical_focus(detail, ALLERGENS, outcome, selected_allergen)
    scope = f'Profil {selected_profile}' if selected_profile else 'Sélection filtrée'
    known = int(detail[outcome].isin(['Oui', 'Non']).sum())
    rows = [html.H3(f'{scope} · {number(len(detail))} patients')]
    if evidence['available']:
        lead = 'Allergène suivi' if selected_allergen else 'Plus grand écart absolu Oui − Non'
        rows.append(html.P(
            f"{lead} : {evidence['label']}. Détection IgE pour « {OUTCOMES[outcome]} » : "
            f"{evidence['yes_rate']:.1f} % dans le groupe Oui "
            f"({evidence['yes_detected']} / {evidence['yes_n']} mesures), "
            f"contre {evidence['no_rate']:.1f} % dans le groupe Non "
            f"({evidence['no_detected']} / {evidence['no_n']}). "
            f"Écart : {evidence['difference']:+.1f} points."
        ))
    else:
        rows.append(html.P(evidence['reason']))
    if selected_profile and len(detail):
        signature = difference_statistics(detail, frame, ALLERGENS).dropna(subset=['difference'])
        median = detail.common_count.dropna().median()
        text = f'Profil {selected_profile} : {100 * len(detail) / len(frame):.1f} % des patients des filtres'
        if np.isfinite(median):
            text += f' · médiane {median:.0f} détections'
        if len(signature):
            row = signature.iloc[0]
            text += (f" · {row.allergen.replace('_', ' ')} : {row.difference:+.1f} points "
                     'par rapport à la sélection filtrée')
        rows.append(html.P(text + '.'))
    rows.append(html.P(f'Information clinique connue : {number(known)} / {number(len(detail))} '
                       f'· inconnus exclus des taux : {number(len(detail) - known)}.'))
    if len(detail) and detail[outcome].nunique() == 1 and detail[outcome].iloc[0] in ['Oui', 'Non']:
        rows.append(html.P('Un seul statut clinique reste visible. Choisir « Tous » pour comparer Oui et Non.'))
    rows.append(html.P('Écarts descriptifs et groupes exploratoires : ni diagnostic, ni causalité, ni prédiction de sévérité.'))
    rows.append(html.Details([
        html.Summary('Méthode et limites de cette vue'),
        html.P('IgE > 0 est un seuil descriptif. Les dénominateurs excluent les mesures manquantes. '
               'Sans allergène choisi, le texte décrit le plus grand écart absolu calculable parmi les '
               'allergènes communs ; ce classement ne constitue pas un test statistique. '
               'La signature compare le profil au total filtré, qui inclut ce profil. '
               'Les traitements sont des informations déclarées, pas des diagnostics. '
               'Les groupes et les coordonnées PCA restent ceux du modèle initial.'),
    ]))
    return rows


@app.callback(
    Output('compact-patients', 'children'), Output('compact-median', 'children'),
    Output('compact-complete', 'children'), Output('compact-known', 'children'),
    Output('compact-selection', 'children'), Output('compact-count', 'figure'),
    Output('compact-top', 'figure'), Output('compact-clinical', 'figure'),
    Output('compact-takeaway', 'children'), Output('compact-pca', 'figure'),
    Output('compact-excess', 'figure'), Output('compact-cohort', 'figure'),
    Output('compact-cluster-clinical', 'figure'), Output('compact-focus-profile', 'options'),
    Output('compact-excess-subtitle', 'children'), Output('compact-clinical-subtitle', 'children'),
    Output('compact-cohort-subtitle', 'children'),
    Input('compact-pop', 'value'), Input('compact-chip', 'value'),
    Input('compact-outcome', 'value'), Input('compact-status', 'value'),
    Input('compact-focus-allergen', 'value'), Input('compact-focus-profile', 'value'),
    Input('compact-reset', 'n_clicks'),
)
def update(pop, chip, outcome, status, selected_allergen=None, selected_profile=None, reset=0):
    frame = cohort(pop, chip, outcome, status)
    valid_groups = groups(frame)
    selected_allergen = selected_allergen if selected_allergen in ALLERGENS else None
    selected_profile = str(selected_profile) if str(selected_profile) in valid_groups else None
    detail = frame.loc[frame.cluster.astype(str).eq(selected_profile)] if selected_profile else frame
    n = len(frame)
    known = int(frame[outcome].isin(['Oui', 'Non']).sum())
    complete = int(frame.common_complete.sum())
    median = frame.common_count.dropna().median()
    median_label = f'{median:.0f}' if np.isfinite(median) else '—'
    revision = json.dumps([pop, chip, outcome, status, reset or 0])
    hist = resize(common_count_histogram(frame), revision)
    hist.update_xaxes(fixedrange=True)
    hist.update_yaxes(fixedrange=True)
    top = resize(top_allergens(frame, ALLERGENS, top_n=8, selected_allergen=selected_allergen), revision,
                 'Top 8 (+ cible si hors classement) · IC 95 % Wilson · n au survol')
    clinical = resize(clinical_differential(
        detail, outcome, ALLERGENS, top_n=7, selected_allergen=selected_allergen), revision,
        f"Oui : n={int(detail[outcome].eq('Oui').sum())} · Non : n={int(detail[outcome].eq('Non').sum())} "
        f"· inconnus exclus : {int((~detail[outcome].isin(['Oui', 'Non'])).sum())} · IC 95 % exploratoires")
    for trace in clinical.data:
        if trace.hovertemplate:
            trace.hovertemplate = trace.hovertemplate.replace('Présence', 'Oui').replace('Absence', 'Non')
    pca = resize(pca_scatter(frame.loc[frame.common_complete], MODEL.explained_variance,
                             selected_cluster=selected_profile), revision)
    pca.update_layout(clickmode='event', dragmode='zoom',
                      legend=dict(itemclick=False, itemdoubleclick=False))
    # Give the overview a useful default, explicitly identified in the subtitle.
    default_group = (frame.loc[frame.cluster.astype(str).isin(valid_groups), 'cluster']
                     .astype(str).value_counts().index[0]) if valid_groups else None
    signature_group = selected_profile or default_group
    excess = (cluster_excess(frame, ALLERGENS, selected_cluster=signature_group,
                             top_n=8, selected_allergen=selected_allergen)
              if signature_group else empty_figure('Aucun profil analysable dans ces filtres.'))
    excess = resize(excess, revision, f'Profil {signature_group} − total filtré · dénominateurs IgE au survol')
    child, adult = detail.loc[detail.age.lt(18)], detail.loc[detail.age.ge(18)]
    age = (cohort_difference(child, adult, ALLERGENS, top_n=8, selected_allergen=selected_allergen)
           if len(child) and len(adult) else empty_figure('Comparaison impossible : enfants et adultes requis.'))
    if len(child) and len(adult):
        age.update_xaxes(title='Écart adultes − enfants (points)')
        for trace in age.data:
            if trace.hovertemplate:
                trace.hovertemplate = trace.hovertemplate.replace('Cohorte A', 'Enfants').replace('Cohorte B', 'Adultes')
    age = resize(age, revision, f'Enfants : n={len(child)} · Adultes : n={len(adult)} · comparaison descriptive')
    profile_clinical = resize(clinical_profiles(frame, outcome, selected_profile), revision)
    scope = f'Profil {selected_profile}' if selected_profile else 'Tous les patients des filtres'
    selection = []
    if selected_allergen:
        selection.append(html.Strong(f"Allergène suivi : {selected_allergen.replace('_', ' ')}"))
    if selected_profile:
        selection.append(html.Strong(f'Profil {selected_profile} · {number(len(detail))} patients en détail'))
    if not selected_allergen and not selected_profile:
        selection.append(html.Span('Cliquer une barre ou un point PCA ; les menus permettent aussi la sélection.'))
    options = [{'label': f'Profil {group} · n={number(int(frame.cluster.astype(str).eq(group).sum()))}',
                'value': group} for group in valid_groups]
    excess_subtitle = (f'Profil {signature_group}' + (' (le plus nombreux)' if not selected_profile else '')
                       + ' − total filtré') if signature_group else 'Aucun profil disponible'
    return (
        number(n), median_label, number(complete), f'{number(known)} / {number(n)}',
        selection, hist, top, clinical, takeaway(frame, detail, outcome, selected_allergen, selected_profile),
        pca, excess, age, profile_clinical, options, excess_subtitle,
        f'{scope} · écart Oui − Non', f'{scope} · adultes − enfants',
    )


if __name__ == '__main__':
    app.run(host='127.0.0.1', port=int(os.environ.get('PORT', '8050')), debug=False)
