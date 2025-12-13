# test_add_document_df_invariant.py

import json
import os
from add_document import addDocument_toBarrel, get_barrel

def test_df_matches_postings_for_same_logical_document_twice(tmp_path, monkeypatch):
    """
    Add two logically identical documents (same title/text) but with different doc_ids.
    Verify that for each affected word_id, df == len(postings).
    """

    # ----- Arrange: isolate Barrels directory -----
    barrels_dir = tmp_path / "Barrels"
    (barrels_dir / "barrel_10").mkdir(parents=True)
    (barrels_dir / "barrel_250").mkdir(parents=True)
    (barrels_dir / "barrel_10000").mkdir(parents=True)

    # Monkeypatch get_barrel to write into tmp_path instead of real Barrels/
    def fake_get_barrel(word_id):
        if word_id < 10000:
            barrel_index = (word_id // 10) + 1
            return str(barrels_dir / "barrel_10" / f"barrel_10_{barrel_index}.json")
        elif word_id < 30000:
            barrel_index = ((word_id - 10000) // 250) + 1
            return str(barrels_dir / "barrel_250" / f"barrel_250_{barrel_index}.json")
        else:
            barrel_index = (word_id // 10000) - 2
            return str(barrels_dir / "barrel_10000" / f"barrel_10000_{barrel_index}.json")

    monkeypatch.setattr("add_document.get_barrel", fake_get_barrel)

    # ----- Arrange: create a fake forward index for two docs with same content -----
    # Suppose word_id 123 appears in both docA and docB titles
    word_id = 123
    new_forward_index_1 = {
        "docA": {
            "title": [word_id],
            "text": []
        }
    }
    new_forward_index_2 = {
        "docB": {
            "title": [word_id],
            "text": []
        }
    }

    # ----- Act: add first logical document -----
    addDocument_toBarrel(new_forward_index_1)

    # ----- Act: add second logical document with different doc_id but same word -----
    addDocument_toBarrel(new_forward_index_2)

    # ----- Assert: df == number of distinct doc_ids in postings for this word_id -----
    barrel_file = fake_get_barrel(word_id)
    assert os.path.exists(barrel_file), "Barrel file should exist for the given word_id"

    with open(barrel_file) as f:
        barrel_data = json.load(f)

    entry = barrel_data[str(word_id)]
    df = entry["df"]
    postings = entry["postings"]

    assert df == len(postings), f"Expected df == len(postings), got df={df}, postings={len(postings)}"
    assert "docA" in postings and "docB" in postings
