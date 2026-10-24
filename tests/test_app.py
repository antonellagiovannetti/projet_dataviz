"""Integration checks for the compact dashboard and real Dash callback requests."""
import json

import pandas as pd
import pytest

import app as dashboard
from app import ALLERGENS, DS, FULL, MODEL, app, server


GRAPH_IDS = (
    "compact-count", "compact-top", "compact-pca", "compact-excess",
    "compact-clinical", "compact-cluster-clinical", "compact-profile-clinical",
)
CLICK_IDS = (
    "compact-top", "compact-clinical", "compact-excess",
    "compact-pca", "compact-cluster-clinical",
)


@pytest.fixture(scope="module")
def client():
    return server.test_client()


def callback_request(client, output_contains, values, changed):
    """Exercise Dash serialization, dispatch and response, not only Python helpers."""
    key = next(key for key in app.callback_map if output_contains in key)
    spec = app.callback_map[key]
    inputs = [{**item, "value": values.get(f"{item['id']}.{item['property']}")}
              for item in spec["inputs"]]
    states = [{**item, "value": values.get(f"{item['id']}.{item['property']}")}
              for item in spec["state"]]
    outputs = spec["output"]
    outputs = ([{"id": item.component_id, "property": item.component_property}
                for item in outputs] if isinstance(outputs, list)
               else {"id": outputs.component_id, "property": outputs.component_property})
    response = client.post("/_dash-update-component", json={
        "output": key, "outputs": outputs, "inputs": inputs, "state": states,
        "changedPropIds": [changed],
    })
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.json["response"]


def values(**overrides):
    current = {
        "compact-pop.value": "all", "compact-chip.value": "all",
        "compact-outcome.value": "skin", "compact-status.value": "all",
        "compact-focus-allergen.value": None, "compact-focus-profile.value": None,
        "compact-reset.n_clicks": 0,
    }
    current.update(overrides)
    return current


def render(client, current=None, changed="compact-pop.value"):
    return callback_request(client, "compact-patients.children", current or values(), changed)


def text_content(node):
    if isinstance(node, str):
        return node
    if isinstance(node, list):
        return " ".join(text_content(child) for child in node)
    if isinstance(node, dict):
        return text_content(node.get("props", {}).get("children"))
    return ""


def figure_text(figure):
    return " ".join(annotation["text"] for annotation in figure["layout"].get("annotations", []))


def test_endpoints_and_compact_layout(client):
    for url in ("/", "/_dash-layout", "/_dash-dependencies", "/assets/compact.css", "/assets/style.css"):
        assert client.get(url).status_code == 200
    layout = client.get("/_dash-layout").json
    serialized = json.dumps(layout, ensure_ascii=False)
    for graph_id in GRAPH_IDS:
        assert f'"id": "{graph_id}"' in serialized
    assert "compact-cohort" not in serialized
    copy = text_content(layout)
    assert "profils de détection IgE" in copy
    assert "Profils IgE complets" in copy
    assert "Statuts cliniques renseignés" in copy
    assert "sensibilisation IgE" not in copy


@pytest.mark.parametrize("tab,visible,hidden", [
    ("synthesis", "compact-synthesis", "compact-profiles"),
    ("profiles", "compact-profiles", "compact-synthesis"),
])
def test_tab_visibility_real_callback(client, tab, visible, hidden):
    result = callback_request(client, "compact-synthesis.style",
                              {"compact-tab.value": tab}, "compact-tab.value")
    assert result[visible]["style"].get("display") != "none"
    assert result[hidden]["style"]["display"] == "none"
    assert text_content(result["compact-intro"]["children"])


@pytest.mark.parametrize("outcome", ["skin", "asthma", "rhinitis", "dermatitis"])
def test_all_clinical_variables_render_and_keep_unknown_counts(client, outcome):
    result = render(client, values(**{"compact-outcome.value": outcome}))
    assert result["compact-patients"]["children"] == dashboard.number(len(DS.frame))
    assert result["compact-complete"]["children"] == dashboard.number(int(FULL.common_complete.sum()))
    known = int(FULL[outcome].isin(["Oui", "Non"]).sum())
    kpi = text_content(result["compact-known"]["children"])
    assert f"{dashboard.number(known)} / {dashboard.number(len(FULL))}" in kpi
    assert dashboard.number(len(FULL) - known) in kpi and "inconnus" in kpi
    for graph_id in GRAPH_IDS:
        assert "layout" in result[graph_id]["figure"]
    empty = result["compact-profile-clinical"]["figure"]
    assert not empty["data"] and "profil" in figure_text(empty).lower()
    assert {item["value"] for item in result["compact-focus-profile"]["options"]} == set(MODEL.labels)


@pytest.mark.parametrize("population,chip,outcome,status", [
    ("children", "ALEX", "skin", "all"),
    ("adults", "ISAC V1", "asthma", "Oui"),
    ("all", "ISAC V2", "rhinitis", "Non"),
])
def test_global_filters_intersect_without_refitting(client, monkeypatch, population, chip, outcome, status):
    def unexpected_refit(*args, **kwargs):
        pytest.fail("Interactions must not refit the model")
    monkeypatch.setattr(dashboard, "get_profiles", unexpected_refit)
    labels_before = MODEL.labels.copy(deep=True)
    expected = FULL.loc[FULL.chip.eq(chip)]
    if population == "children":
        expected = expected.loc[expected.age.lt(18)]
    elif population == "adults":
        expected = expected.loc[expected.age.ge(18)]
    if status != "all":
        expected = expected.loc[expected[outcome].eq(status)]
    result = render(client, values(**{
        "compact-pop.value": population, "compact-chip.value": chip,
        "compact-outcome.value": outcome, "compact-status.value": status,
    }))
    assert result["compact-patients"]["children"] == dashboard.number(len(expected))
    pd.testing.assert_series_equal(MODEL.labels, labels_before)
    if status != "all":
        assert not result["compact-clinical"]["figure"]["data"]


def test_dropdown_profile_and_allergen_focus_reaches_all_relevant_panels(client):
    profile = dashboard.groups(FULL)[0]
    allergen = ALLERGENS[-1]
    result = render(client, values(**{
        "compact-focus-allergen.value": allergen,
        "compact-focus-profile.value": profile,
    }), "compact-focus-profile.value")
    assert f"Profil {profile}" in text_content(result["compact-selection"]["children"])
    assert allergen.replace("_", " ") in text_content(result["compact-selection"]["children"])
    assert result["compact-profile-clinical"]["figure"]["data"]
    assert "reste" in result["compact-excess-subtitle"]["children"].lower()
    for graph_id in ("compact-top", "compact-excess", "compact-clinical"):
        figure = result[graph_id]["figure"]
        if figure["data"]:
            assert any(row[0] == allergen for trace in figure["data"]
                       for row in trace.get("customdata", []))


@pytest.mark.parametrize("graph_id", ["compact-top", "compact-clinical", "compact-excess"])
def test_allergen_clicks_select_and_consume_events(client, graph_id):
    current = values(**{f"{graph_id}.clickData": {"points": [{"customdata": [ALLERGENS[0]]}]}})
    result = callback_request(client, "compact-pop.value", current, f"{graph_id}.clickData")
    assert result["compact-focus-allergen"]["value"] == ALLERGENS[0]
    for item in CLICK_IDS:
        assert result[item]["clickData"] is None


@pytest.mark.parametrize("graph_id", ["compact-pca", "compact-cluster-clinical"])
def test_profile_clicks_select_and_consume_events(client, graph_id):
    profile = dashboard.groups(FULL)[0]
    custom = ["patient-id", 20, "Femmes", "ALEX", 10, profile] if graph_id == "compact-pca" else [profile]
    current = values(**{f"{graph_id}.clickData": {"points": [{"customdata": custom}]}})
    result = callback_request(client, "compact-pop.value", current, f"{graph_id}.clickData")
    assert result["compact-focus-profile"]["value"] == profile
    for item in CLICK_IDS:
        assert result[item]["clickData"] is None


@pytest.mark.parametrize("event", [None, {}, {"points": []}, {"points": [None]},
                                   {"points": [{"customdata": "invalid"}]},
                                   {"points": [{"customdata": []}]},
                                   {"points": [{"customdata": ["not-an-allergen"]}]}])
def test_empty_and_malformed_clicks_do_not_change_selection(client, event):
    result = callback_request(client, "compact-pop.value", values(**{"compact-top.clickData": event}),
                              "compact-top.clickData")
    assert result == {}


def test_stale_profile_click_is_ignored(client):
    current = values(**{"compact-cluster-clinical.clickData": {"points": [{"customdata": ["999"]}]}})
    result = callback_request(client, "compact-pop.value", current, "compact-cluster-clinical.clickData")
    assert result == {}


@pytest.mark.parametrize("filter_id", ["compact-pop", "compact-chip", "compact-outcome", "compact-status"])
def test_filter_changes_clear_profile_and_clicks_but_keep_allergen(client, filter_id):
    current = values(**{"compact-focus-allergen.value": ALLERGENS[0], "compact-focus-profile.value": "1"})
    result = callback_request(client, "compact-pop.value", current, f"{filter_id}.value")
    assert result["compact-focus-profile"]["value"] is None
    assert "compact-focus-allergen" not in result
    for item in CLICK_IDS:
        assert result[item]["clickData"] is None


def test_reset_restores_filters_focus_and_click_events(client):
    current = values(**{
        "compact-pop.value": "children", "compact-chip.value": "ALEX",
        "compact-outcome.value": "asthma", "compact-status.value": "Oui",
        "compact-focus-allergen.value": ALLERGENS[0], "compact-focus-profile.value": "1",
        "compact-reset.n_clicks": 1,
    })
    result = callback_request(client, "compact-pop.value", current, "compact-reset.n_clicks")
    for component, expected in (("pop", "all"), ("chip", "all"), ("outcome", "skin"), ("status", "all"),
                                ("focus-allergen", None), ("focus-profile", None)):
        assert result[f"compact-{component}"]["value"] == expected
    for item in CLICK_IDS:
        assert result[item]["clickData"] is None


def test_invalid_dropdown_values_fall_back_to_unfocused_view(client):
    result = render(client, values(**{
        "compact-focus-allergen.value": "not-an-allergen", "compact-focus-profile.value": "999",
    }))
    assert not result["compact-profile-clinical"]["figure"]["data"]
    assert "999" not in text_content(result["compact-selection"]["children"])
    assert "not-an-allergen" not in text_content(result["compact-selection"]["children"])


def test_empty_cohort_never_restores_full_population(client, monkeypatch):
    monkeypatch.setattr(dashboard, "FULL", FULL.iloc[:0].copy())
    result = render(client, values(**{"compact-focus-profile.value": "1"}))
    assert result["compact-patients"]["children"] == "0"
    assert result["compact-complete"]["children"] == "0"
    assert result["compact-median"]["children"] == "—"
    assert result["compact-focus-profile"]["options"] == []
    for graph_id in GRAPH_IDS:
        assert not result[graph_id]["figure"]["data"]
        assert figure_text(result[graph_id]["figure"])


def test_unknown_clinical_statuses_remain_missing_not_zero(client, monkeypatch):
    frame = FULL.loc[FULL.cluster.ne("Non attribué")].head(8).copy()
    for outcome in dashboard.OUTCOMES:
        frame[outcome] = "Inconnu"
    monkeypatch.setattr(dashboard, "FULL", frame)
    result = render(client, values(**{"compact-focus-profile.value": str(frame.cluster.iloc[0])}))
    assert "0 / 8" in text_content(result["compact-known"]["children"])
    assert not result["compact-clinical"]["figure"]["data"]
    group_chart = result["compact-cluster-clinical"]["figure"]
    assert group_chart["data"]
    rates = [value for trace in group_chart["data"] for value in trace.get("y", [])]
    assert rates and all(value is None for value in rates)
    assert "sévérité" not in text_content(result["compact-takeaway"]["children"])
