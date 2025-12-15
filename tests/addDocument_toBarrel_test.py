import json
import os
import pytest
from add_document import addDocument_toBarrel


def _setup_barrels(tmp_path):
    base = tmp_path / "JSON Files" / "Barrels"
    (base / "barrel_10").mkdir(parents=True)
    (base / "barrel_250").mkdir(parents=True)
    (base / "barrel_10000").mkdir(parents=True)
    (base / ".locks").mkdir(parents=True)
    return base


def _fake_get_barrel_factory(base):
    def fake_get_barrel(word_id):
        if word_id < 10000:
            barrel_index = (word_id // 10) + 1
            return str(base / "barrel_10" / f"barrel_10_{barrel_index}.json")
        if word_id < 30000:
            barrel_index = ((word_id - 10000) // 250) + 1
            return str(base / "barrel_250" / f"barrel_250_{barrel_index}.json")
        barrel_index = (word_id // 10000) - 2
        return str(base / "barrel_10000" / f"barrel_10000_{barrel_index}.json")

    return fake_get_barrel


@pytest.fixture(autouse=True)
def isolate_barrels(tmp_path, monkeypatch):
    base = _setup_barrels(tmp_path)
    # ensure working dir is temp to keep writes isolated
    monkeypatch.chdir(tmp_path)
    # patch get_barrel used inside add_document
    monkeypatch.setattr("add_document.get_barrel", _fake_get_barrel_factory(base))
    yield base


def _load_barrel(path):
    with open(path) as f:
        return json.load(f)


def test_single_term(isolate_barrels):
    fi = {"doc1": {"text": [1], "title": []}}
    addDocument_toBarrel(fi)
    barrel_file = _fake_get_barrel_factory(isolate_barrels)(1)
    data = _load_barrel(barrel_file)
    assert data["1"]["df"] == len(data["1"]["postings"]) == 1


def test_multiple_terms(isolate_barrels):
    fi = {"doc1": {"text": [1, 2, 3], "title": []}}
    addDocument_toBarrel(fi)
    for wid in [1, 2, 3]:
        barrel_file = _fake_get_barrel_factory(isolate_barrels)(wid)
        data = _load_barrel(barrel_file)
        assert data[str(wid)]["df"] == 1


def test_same_word_docs(isolate_barrels):
    fi = {
        "doc1": {"text": [1], "title": []},
        "doc2": {"text": [1], "title": []},
    }
    addDocument_toBarrel(fi)
    barrel_file = _fake_get_barrel_factory(isolate_barrels)(1)
    data = _load_barrel(barrel_file)
    assert data["1"]["df"] == len(data["1"]["postings"]) == 2


def test_empty_fi(isolate_barrels):
    fi = {}
    addDocument_toBarrel(fi)
    # No barrels should be created
    assert not list((isolate_barrels).rglob("*.json"))