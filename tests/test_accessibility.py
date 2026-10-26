"""Accessible chart descriptions and PCA labels preserve analytical content."""
import json

import numpy as np
import pandas as pd
import pytest
from plotly.utils import PlotlyJSONEncoder

from app import app
from src.charts import pca_scatter


def nodes(value):
    if isinstance(value, list):
        for child in value:
            yield from nodes(child)
    elif isinstance(value, dict):
        yield value
        yield from nodes(value.get("props", {}).get("children"))


def text_content(value):
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return " ".join(text_content(child) for child in value)
    if isinstance(value, dict):
        return text_content(value.get("props", {}).get("children"))
    return ""


def test_every_chart_has_a_resolvable_accessible_name_and_description():
    layout = json.loads(json.dumps(app.layout, cls=PlotlyJSONEncoder))
    all_nodes = list(nodes(layout))
    identified = [node for node in all_nodes if node.get("props", {}).get("id")]
    by_id = {node["props"]["id"]: node for node in identified}
    assert len(by_id) == len(identified), "Duplicate IDs break accessible references"
    graphs = [node for node in all_nodes if node.get("type") == "Graph"]
    assert len(graphs) == 7
    for graph in graphs:
        graph_id = graph["props"]["id"]
        regions = [node for node in all_nodes
                   if node.get("props", {}).get("role") == "group"
                   and any(child.get("props", {}).get("id") == graph_id
                           for child in nodes(node.get("props", {}).get("children")))]
        assert len(regions) == 1, graph_id
        region = regions[0]["props"]
        title = by_id[region["aria-labelledby"]]
        description = by_id[region["aria-describedby"]]
        assert title["type"] == "H2" and text_content(title).strip()
        assert text_content(description).strip()
        assert "sr-only" in description["props"].get("className", "").split()
        assert description["props"].get("aria-hidden") not in (True, "true")
        assert not description["props"].get("hidden")


@pytest.fixture
def projected_patients():
    return pd.DataFrame({
        "id": ["p1", "p2", "p3", "p4", "p5", "p6"],
        "pc1": [-4.0, -2.0, 0.0, 5.0, 9.0, np.nan],
        "pc2": [1.0, 3.0, 8.0, 4.0, 10.0, np.nan],
        "cluster": ["1", "1", "1", "2", "2", "3"],
        "age": [20.0] * 6,
        "sex": ["Femmes"] * 6,
        "chip": ["ALEX"] * 6,
        "common_count": [1.0, 2.0, 3.0, 15.0, 20.0, np.nan],
    })


def profile_labels(figure):
    return {annotation.name: annotation for annotation in figure.layout.annotations
            if (annotation.name or "").startswith("pca-profile-label-")}


@pytest.mark.parametrize("selected", [None, "1", "2", "missing"])
def test_pca_labels_use_existing_groups_without_changing_patients(projected_patients, selected):
    original = projected_patients.copy(deep=True)
    figure = pca_scatter(projected_patients, [0.4, 0.2], selected_cluster=selected)
    pd.testing.assert_frame_equal(projected_patients, original)
    labels = profile_labels(figure)
    assert set(labels) == {"pca-profile-label-1", "pca-profile-label-2"}
    for cluster, expected_x, expected_y in [("1", -2.0, 3.0), ("2", 7.0, 7.0)]:
        label = labels[f"pca-profile-label-{cluster}"]
        assert f"Profil {cluster}" in label.text
        assert (label.x, label.y) == (expected_x, expected_y)
        assert (label.xref, label.yref) == ("x", "y")
        assert label.captureevents is False, "Labels must not intercept point clicks"
    assert len(figure.data) == 2, "Labels belong to layout, never extra patient traces"
    for trace in figure.data:
        cluster = str(trace.customdata[0][5])
        expected = original.loc[original.cluster.eq(cluster)]
        np.testing.assert_array_equal(trace.x, expected.pc1)
        np.testing.assert_array_equal(trace.y, expected.pc2)
        assert list(trace.customdata[:, 0]) == expected.id.tolist()


def test_pca_filtered_groups_have_no_stale_labels(projected_patients):
    one_group = projected_patients.loc[projected_patients.cluster.eq("2")]
    figure = pca_scatter(one_group, selected_cluster="1")
    labels = profile_labels(figure)
    assert set(labels) == {"pca-profile-label-2"}
    assert (labels["pca-profile-label-2"].x, labels["pca-profile-label-2"].y) == (7.0, 7.0)


@pytest.mark.parametrize("invalid_coordinates_only", [False, True])
def test_empty_pca_never_invents_group_labels(projected_patients, invalid_coordinates_only):
    frame = (projected_patients.loc[projected_patients.cluster.eq("3")]
             if invalid_coordinates_only else projected_patients.iloc[:0])
    figure = pca_scatter(frame, selected_cluster="1")
    assert not profile_labels(figure)
    assert not figure.data
