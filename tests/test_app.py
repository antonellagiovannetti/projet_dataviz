"""Integration checks for scientific states and actual Dash callback requests."""
import json
import pytest
from plotly.utils import PlotlyJSONEncoder
from app import app, dataset, model, server
from src.callbacks import selected_frame


@pytest.fixture(scope="module")
def client():
    return server.test_client()


def callback_request(client, output_contains, values, changed):
    key = next(key for key in app.callback_map if output_contains in key)
    spec = app.callback_map[key]
    inputs = [{**item, "value": values.get(f"{item['id']}.{item['property']}")} for item in spec["inputs"]]
    state = [{**item, "value": values.get(f"{item['id']}.{item['property']}")} for item in spec["state"]]
    outs = spec["output"]
    outputs = [{"id": o.component_id, "property": o.component_property} for o in outs] if isinstance(outs,list) else {"id": outs.component_id, "property": outs.component_property}
    response = client.post('/_dash-update-component', json={"output":key, "outputs":outputs, "inputs":inputs,
                                                           "state":state,"changedPropIds":[changed]})
    assert response.status_code == 200, response.get_data(as_text=True)
    return response.json["response"]


def render_values(page="overview", filters=None, cross=None, cohorts=None):
    return {"url.hash":f"#{page}", "filter-store.data":filters or {}, "cross-store.data":cross or {},
            "coverage-sort.value":"common", "show-missing.value":["yes"], "allergen-metric.value":"prevalence",
            "top-n.value":20, "age-mode.value":"standard", "heatmap-sort.value":"count",
            "clinical-outcome.value":"skin", "clinical-dimension.value":"sensitization",
            "cluster-k.value":model.best_k, "scale-mode.value":"within", "cohort-store.data":cohorts or {}}


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
    data={"overview-chips.clickData":{"points":[{"customdata":["ALEX",26.7]}]}, "cross-store.data":{}}
    result=callback_request(client,"cross-store.data",data,"overview-chips.clickData")
    assert result['cross-store']['data']=={"chip":"ALEX"}
    assert len(selected_frame(model,{},result['cross-store']['data']))==1139


def test_lasso_zero_does_not_select_everyone(client):
    data={"pca-chart.selectedData":{"points":[]}, "cross-store.data":{}}
    result=callback_request(client,"cross-store.data",data,"pca-chart.selectedData")
    assert result['cross-store']['data']=={"ids":[]}
    assert selected_frame(model,{},result['cross-store']['data']).empty


def test_lasso_exact_ids_and_age_intersection(client):
    ids=model.frame.loc[model.frame.age.between(18,30),'id'].head(4).tolist()
    data={"pca-chart.selectedData":{"points":[{"customdata":[i,20,"Femmes","ALEX",10,"1"]} for i in ids]},"cross-store.data":{}}
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
    data={"cluster-k.value":3,"cross-store.data":{"cluster":"2","ids":["FHB0001"],"chip":"ALEX"}}
    result=callback_request(client,"cross-store.data",data,"cluster-k.value")
    assert result['cross-store']['data']=={"chip":"ALEX"}


def test_filters_reset_without_erasing_saved_cohorts(client):
    result=callback_request(client,"filter-age.value",{"reset-filters.n_clicks":1},"reset-filters.n_clicks")
    assert result['filter-chip']['value']==[]
    assert result['filter-allergen']['value'] is None
    assert 'cohort-store' not in result
