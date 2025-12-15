import pytest
from search_engine import multiple_word_search


@pytest.fixture(autouse=True)
def stub_stopwords(monkeypatch):
    monkeypatch.setattr("search_engine.stopwords.words", lambda lang: ["the", "and", "is"])


@pytest.fixture()
def tiny_lexicon():
    return {"search": 1, "engine": 2}


def test_single_word(tiny_lexicon):
    res, meta = multiple_word_search("search", lexicon=tiny_lexicon)
    assert isinstance(res, list)


def test_multi_word(tiny_lexicon):
    res, meta = multiple_word_search("search engine", lexicon=tiny_lexicon)
    assert isinstance(res, list)


def test_punctuation(tiny_lexicon):
    res, meta = multiple_word_search("search, engine!", lexicon=tiny_lexicon)
    assert isinstance(res, list)


def test_stopword_only(tiny_lexicon, monkeypatch):
    msg = multiple_word_search("the and is", lexicon=tiny_lexicon)
    assert isinstance(msg, str)


def test_empty_query(tiny_lexicon):
    msg = multiple_word_search("", lexicon=tiny_lexicon)
    assert isinstance(msg, str)