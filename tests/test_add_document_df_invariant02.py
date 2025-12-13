import json
import os
from add_document import addDocument_toBarrel, get_barrel

def test_df_does_not_increase_when_same_docid_reapplied(tmp_path, monkeypatch):
    """
    Add inverted index for a word_id and doc_id, then apply the same data again.
    Verify that df does not increase and still equals len(postings).
    """

    # ----- Arrange: isolate Barrels directory -----
    barrels_dir = tmp_path / "Barrels"
    (barrels_dir / "barrel_10").mkdir(parents=True)
    (barrels_dir / "barrel_250").mkdir(parents=True)
    (barrels_dir / "barrel_10000").mkdir(parents=True)

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

    # ----- Arrange: forward index with a single word_id-doc_id pair -----
    word_id = 456
    doc_id = "docXYZ"
    new_forward_index = {
        doc_id: {
            "title": [word_id],
            "text": []
        }
    }

    # ----- Act: first application -----
    addDocument_toBarrel(new_forward_index)

    # ----- Act: second application with the same doc_id and word_id -----
    addDocument_toBarrel(new_forward_index)

    # ----- Assert: df == len(postings) and df == 1 -----
    barrel_file = fake_get_barrel(word_id)
    assert os.path.exists(barrel_file), "Barrel file should exist for the given word_id"

    with open(barrel_file) as f:
        barrel_data = json.load(f)

    entry = barrel_data[str(word_id)]
    df = entry["df"]
    postings = entry["postings"]

    # Only one doc_id should be present
    assert len(postings) == 1, f"Expected exactly 1 posting, got {len(postings)}"
    assert doc_id in postings, "Expected doc_id to be present in postings"
    assert df == len(postings), f"Expected df == len(postings), got df={df}, postings={len(postings)}"
    assert df == 1, f"Expected df == 1, got df={df}"
