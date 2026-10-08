"""Integration checks for scientific states and actual Dash callback requests."""
import json
import pytest
from plotly.utils import PlotlyJSONEncoder
from app import app, dataset, model, server
from src.callbacks import preset_cohorts, selected_frame


@pytest.fixture(scope="module")
def client():
    return server.test_client()


def callback_request(client, output_contains, values, changed, status=200):
    key = next(key for key in app.callback_map if output_contains in key)
    spec = app.callback_map[key]
    inputs = [{**item, "value": values.get(f"{item['id']}.{item['property']}")} for item in spec["inputs"]]
    state = [{**item, "value": values.get(f"{item['id']}.{item['property']}")} for item in spec["state"]]
    outs = spec["output"]
    outputs = [{"id": o.component_id, "property": o.component_property} for o in outs] if isinstance(outs,list) else {"id": outs.component_id, "property": outs.component_property}
    response = client.post('/_dash-update-component', json={"output":key, "outputs":outputs, "inputs":inputs,
                                                           "state":state,"changedPropIds":[changed]})
    assert response.status_code == status, response.get_data(as_text=True)
    return response.json["response"] if status == 200 else None


def render_values(page="overview", filters=None, cross=None, cohorts=None, mode="explore"):
    return {"url.hash":f"#{page}", "filter-store.data":filters or {}, "cross-store.data":cross or {},
            "coverage-sort.value":"common", "show-missing.value":["yes"], "allergen-metric.value":"prevalence",
            "top-n.value":20, "age-mode.value":"standard", "heatmap-sort.value":"count",
            "clinical-outcome.value":"skin", "clinical-dimension.value":"sensitization",
            "cluster-k.value":model.best_k, "scale-mode.value":"within", "cohort-store.data":cohorts or {},
            "reading-mode.value": mode}


@pytest.mark.parametrize("page", ["overview","landscape","sensitization","clinical","profiles","explorer","conclusions","glossary"])
@pytest.mark.parametrize("empty", [False,True])
def test_all_chapters_real_callback(client,page,empty):
    values=render_values(page, cross={"ids":[]} if empty else {})
    result=callback_request(client,"page-body.children",values,"url.hash")
    assert result["cohort-size"]["children"] == ("0" if empty else "4\u202f271")
    assert result["page-body"]["children"]
    def nodes(value):
        if isinstance(value,list):
            for item in value:
                yield from nodes(item)
        elif isinstance(value,dict):
            yield value
            yield from nodes(value.get("props",{}).get("children"))
    for section in nodes(result["page-body"]["children"]):
        if "chart-panel" not in section.get("props",{}).get("className",""):
            continue
        descendants=list(nodes(section.get("props",{}).get("children")))
        assert any(node.get("props",{}).get("className")=="chart-takeaway" for node in descendants)


def test_endpoints_and_local_assets(client):
    for url in ['/', '/_dash-layout','/_dash-dependencies','/assets/style.css','/assets/logo.svg']:
        assert client.get(url).status_code == 200


def test_graph_chip_selection_and_removal(client):
    data={"overview-chips.clickData":{"points":[{"customdata":["ALEX",26.7]}]}, "cross-store.data":{}, "reading-mode.value":"explore"}
    result=callback_request(client,"cross-store.data",data,"overview-chips.clickData")
    assert result['cross-store']['data']=={"chip":"ALEX"}
    assert len(selected_frame(model,{},result['cross-store']['data']))==1139


def test_lasso_zero_does_not_select_everyone(client):
    data={"pca-chart.selectedData":{"points":[]}, "cross-store.data":{}, "reading-mode.value":"explore"}
    result=callback_request(client,"cross-store.data",data,"pca-chart.selectedData")
    assert result['cross-store']['data']=={"ids":[]}
    assert selected_frame(model,{},result['cross-store']['data']).empty


def test_lasso_exact_ids_and_age_intersection(client):
    ids=model.frame.loc[model.frame.age.between(18,30),'id'].head(4).tolist()
    data={"pca-chart.selectedData":{"points":[{"customdata":[i,20,"Femmes","ALEX",10,"1"]} for i in ids]},"cross-store.data":{}, "reading-mode.value":"explore"}
    result=callback_request(client,"cross-store.data",data,"pca-chart.selectedData")
    assert set(selected_frame(model,{"age":[18,30]},result['cross-store']['data']).id)==set(ids)
    assert selected_frame(model,{"age":[0,17]},result['cross-store']['data']).empty


def test_saved_cohort_is_snapshot_and_comparison_renders(client):
    filters={"age":[0,17],"include_unknown_age":False}
    state={"save-a.n_clicks":1,"filter-store.data":filters,"cross-store.data":{},
           "cluster-k.value":model.k,"scale-mode.value":"within","cohort-store.data":{}}
    a=callback_request(client,"cohort-store.data",state,"save-a.n_clicks")["cohort-store"]["data"]
    expected=set(selected_frame(model,filters,{}).id)
    assert set(a['a']['ids'])==expected
    state.update({"save-a.n_clicks":None,"save-b.n_clicks":1,"filter-store.data":{"age":[18,100],"include_unknown_age":False},"cohort-store.data":a})
    both=callback_request(client,"cohort-store.data",state,"save-b.n_clicks")["cohort-store"]["data"]
    assert set(both['a']['ids'])==expected
    assert set(both['a']['ids']).isdisjoint(both['b']['ids'])
    result=callback_request(client,"page-body.children",render_values("explorer",cohorts=both),"cohort-store.data")
    assert "cohort-difference" in json.dumps(result,cls=PlotlyJSONEncoder)


def test_model_switch_clears_cluster_selection_only(client):
    data={"cluster-k.value":3,"cross-store.data":{"cluster":"2","ids":["FHB0001"],"chip":"ALEX"}, "reading-mode.value":"explore"}
    result=callback_request(client,"cross-store.data",data,"cluster-k.value")
    assert result['cross-store']['data']=={"chip":"ALEX"}


def test_filters_reset_without_erasing_saved_cohorts(client):
    result=callback_request(client,"filter-age.value",{"reset-filters.n_clicks":1},"reset-filters.n_clicks")
    assert result['filter-chip']['value']==[]
    assert result['filter-allergen']['value'] is None
    assert 'cohort-store' not in result


def test_story_ignores_saved_exploration_but_explore_restores_it(client, monkeypatch):
    import src.callbacks as callbacks
    observed = []
    def capture_page(**state):
        observed.append(state)
        return []
    monkeypatch.setitem(callbacks.PAGES, "overview", capture_page)
    values = render_values(filters={"chip":["ALEX"]}, cross={"cluster":"3"},
                           cohorts={"a":{"ids":["saved-id"]}}, mode="story")
    values.update({"cluster-k.value": 3, "scale-mode.value":"global", "clinical-outcome.value":"asthma",
                   "allergen-metric.value":"median", "top-n.value":10})
    calls = []
    original_get_profiles = callbacks.get_profiles
    def track_profiles(*args, **kwargs):
        calls.append((args, kwargs))
        return original_get_profiles(*args, **kwargs)
    monkeypatch.setattr(callbacks, "get_profiles", track_profiles)
    story = callback_request(client, "page-body.children", values, "reading-mode.value")
    state = observed[-1]
    assert calls == []
    assert len(state["df"]) == len(dataset.frame)
    assert state["model"] is model and state["model"].k == model.best_k
    assert state["controls"]["outcome"] == "skin" and state["controls"]["metric"] == "prevalence"
    assert state["controls"]["top_n"] == 20 and state["controls"]["mode"] == "story"
    assert state["cross"] == {} and state["cohorts"] == values["cohort-store.data"]
    assert story["app-shell"]["className"] == "app-shell mode-story"
    for untouched in ("filter-store", "cross-store", "cohort-store", "cluster-k", "scale-mode"):
        assert untouched not in story
    assert {option["value"] for option in story["filter-cluster"]["options"]} >= {"3"}
    values["reading-mode.value"] = "explore"
    explore = callback_request(client, "page-body.children", values, "reading-mode.value")
    state = observed[-1]
    assert calls and state["model"].k == 3
    assert state["df"].chip.eq("ALEX").all() and state["df"].cluster.eq("3").all()
    assert state["controls"]["outcome"] == "asthma" and state["controls"]["metric"] == "median"
    assert state["cross"] == {"cluster":"3"} and state["cohorts"] == values["cohort-store.data"]
    assert explore["app-shell"]["className"] == "app-shell mode-explore"


def test_story_graph_events_leave_saved_cross_filters_untouched(client):
    values = {"reading-mode.value":"story", "cross-store.data":{"chip":"ALEX"},
              "pca-chart.selectedData":{"points":[]}}
    callback_request(client, "cross-store.data", values, "pca-chart.selectedData", status=204)


def test_laboratory_mode_navigation_keeps_cohorts_and_filters(client):
    values = {"reading-mode.value":"story", "url.hash":"#explorer"}
    entered = callback_request(client, "reading-mode.value", values, "url.hash")
    assert entered == {"reading-mode":{"value":"explore"}}
    returned = callback_request(client, "reading-mode.value", values, "reading-mode.value")
    assert returned == {"url":{"hash":"#overview"}}
    callback_request(client, "reading-mode.value", {"reading-mode.value":"story", "url.hash":"#overview"},
                     "url.hash", status=204)


@pytest.mark.parametrize("key", ["age", "sex", "skin", "cluster"])
def test_cohort_presets_use_exact_source_populations(key):
    frame = model.frame
    expected = {
        "age": (frame.age.between(0,17), frame.age.ge(18)),
        "sex": (frame.sex.eq("Hommes"), frame.sex.eq("Femmes")),
        "skin": (frame.skin.eq("Oui"), frame.skin.eq("Non")),
        "cluster": (frame.cluster.eq("1"), frame.cluster.eq("2")),
    }
    cohorts = preset_cohorts(key, model, dataset, "within")
    for slot, mask in zip(("a", "b"), expected[key]):
        assert set(cohorts[slot]["ids"]) == set(frame.loc[mask,"id"])
        assert cohorts[slot]["model_k"] == model.k
        assert cohorts[slot]["scaling"] == "within"
        assert cohorts[slot]["source"] == dataset.source_path.name
        assert cohorts[slot]["saved_at"]
    assert set(cohorts["a"]["ids"]).isdisjoint(cohorts["b"]["ids"])


def test_preset_requires_explicit_click_and_overwrites_both_snapshots(client):
    preset_input = '{"key":["ALL"],"type":"cohort-preset"}.n_clicks'
    changed = '{"key":"skin","type":"cohort-preset"}.n_clicks'
    values = {preset_input:[0,0,0,0], "filter-store.data":{"chip":["ALEX"]}, "cross-store.data":{"ids":[]},
              "cohort-store.data":{"a":{"ids":["old"]}}, "cluster-k.value":model.k, "scale-mode.value":"within"}
    callback_request(client, "cohort-store.data", values, changed, status=204)
    values[preset_input] = [0,0,1,0]
    result = callback_request(client, "cohort-store.data", values, changed)["cohort-store"]["data"]
    assert set(result["a"]["ids"]) == set(model.frame.loc[model.frame.skin.eq("Oui"), "id"])
    assert set(result["b"]["ids"]) == set(model.frame.loc[model.frame.skin.eq("Non"), "id"])
    assert len(result["a"]["ids"]) == 1140 and len(result["b"]["ids"]) == 686


def test_group_preset_uses_current_model_not_story_reference():
    from src.clustering import get_profiles
    current = get_profiles(3, False)
    snapshots = preset_cohorts("cluster", current, dataset, "global")
    for slot, label in (("a","1"), ("b","2")):
        assert set(snapshots[slot]["ids"]) == set(current.frame.loc[current.frame.cluster.eq(label), "id"])
        assert snapshots[slot]["model_k"] == 3 and snapshots[slot]["scaling"] == "global"
        assert "K = 3" in snapshots[slot]["description"] and "globale" in snapshots[slot]["description"]
