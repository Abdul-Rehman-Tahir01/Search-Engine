import json
import os
import pytest

from search_engine import multiple_word_search


@pytest.fixture()
def temp_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("JSON Files", exist_ok=True)
    with open("JSON Files/metadata.json", "w") as f:
        json.dump({"doc1": {}, "doc2": {}, "doc3": {}}, f)
    yield tmp_path


def test_and_operator(temp_env, monkeypatch):
    # Stub single_word_search to control postings
    def fake_single_word_search(term, lexicon):
        if term.lower() == "alpha":
            return {
                "doc1": {"positions": {"title": 1, "text": 0}},
                "doc2": {"positions": {"title": 0, "text": 2}},
            }, {"term": term, "message": None}
        if term.lower() == "beta":
            return {
                "doc2": {"positions": {"title": 1, "text": 0}},
            }, {"term": term, "message": None}
        return None, {"term": term, "message": "not found"}

    monkeypatch.setattr("search_engine.single_word_search", fake_single_word_search)
    lex = {"alpha": 1, "beta": 2}
    ranked, meta = multiple_word_search("alpha AND beta", lexicon=lex)
    ids = [item["ID"] for item in ranked]
    assert ids == ["doc2"]


def test_or_operator(temp_env, monkeypatch):
    def fake_single_word_search(term, lexicon):
        if term.lower() == "alpha":
            return {
                "doc1": {"positions": {"title": 1, "text": 0}},
                "doc2": {"positions": {"title": 0, "text": 2}},
            }, {"term": term, "message": None}
        if term.lower() == "beta":
            return {
                "doc2": {"positions": {"title": 1, "text": 0}},
            }, {"term": term, "message": None}
        return None, {"term": term, "message": "not found"}

    monkeypatch.setattr("search_engine.single_word_search", fake_single_word_search)
    lex = {"alpha": 1, "beta": 2}
    ranked, meta = multiple_word_search("alpha OR beta", lexicon=lex)
    ids = {item["ID"] for item in ranked}
    assert ids == {"doc1", "doc2"}


def test_not_operator(temp_env, monkeypatch):
    def fake_single_word_search(term, lexicon):
        if term.lower() == "beta":
            return {
                "doc2": {"positions": {"title": 1, "text": 0}},
            }, {"term": term, "message": None}
        return None, {"term": term, "message": "not found"}

    monkeypatch.setattr("search_engine.single_word_search", fake_single_word_search)
    lex = {"beta": 2}
    ranked, meta = multiple_word_search("NOT beta", lexicon=lex)
    ids = {item["ID"] for item in ranked}
    # universe was doc1, doc2, doc3; NOT beta should exclude doc2
    assert ids == {"doc1", "doc3"}
