from search_engine import rank_documents


def _posting(tf_title=0, tf_text=0):
    return {"positions": {"title": tf_title, "text": tf_text}}


def test_single_doc():
    postings = {"doc1": _posting(tf_title=1)}
    ranked = rank_documents(postings)
    assert ranked[0]["ID"] == "doc1"


def test_multiple_docs():
    postings = {"doc1": _posting(tf_title=1), "doc2": _posting(tf_title=3)}
    ranked = rank_documents(postings)
    assert ranked[0]["ID"] == "doc2"


def test_same_score_ordering():
    postings = {"doc1": _posting(tf_title=1), "doc2": _posting(tf_title=1)}
    ranked = rank_documents(postings)
    ids = {item["ID"] for item in ranked}
    assert ids == {"doc1", "doc2"}


def test_empty_postings():
    postings = {}
    assert rank_documents(postings) == []


def test_zero_score():
    postings = {"doc1": _posting(tf_title=0, tf_text=0)}
    ranked = rank_documents(postings)
    assert ranked[0]["ID"] == "doc1"