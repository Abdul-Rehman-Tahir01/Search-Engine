import json
import os
import pandas as pd
import pytest
from add_document import addDocument_tolexicon_FI


@pytest.fixture()
def temp_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("JSON Files/Barrels/.locks", exist_ok=True)
    os.makedirs("JSON Files/Barrels/barrel_10", exist_ok=True)
    os.makedirs("JSON Files/Barrels/barrel_250", exist_ok=True)
    os.makedirs("JSON Files/Barrels/barrel_10000", exist_ok=True)

    # minimal lexicon
    with open("JSON Files/lexicon.json", "w") as f:
        json.dump({}, f)
    yield tmp_path


@pytest.fixture()
def sample_df():
    return pd.DataFrame(
        {
            "title": ["Hello"],
            "text": ["world"],
            "url": ["http://example.com"],
            "authors": ["['a']"],
            "tags": ["['t']"],
            "timestamp": ["2024-01-01"],
            "text_length": [1],
            "title_length": [1],
            "num_tags": [1],
            "num_authors": [1],
        }
    )


def test_single_doc_add(temp_env, sample_df):
    addDocument_tolexicon_FI(sample_df)
    assert os.path.exists("JSON Files/new_forward_index.json")


def test_new_words(temp_env, sample_df):
    sample_df = sample_df.copy()
    sample_df["text"] = ["completelynewword"]
    addDocument_tolexicon_FI(sample_df)
    with open("JSON Files/lexicon.json") as f:
        lexicon = json.load(f)
    assert "completelynewword" in lexicon


def test_empty_text(temp_env, sample_df):
    df_empty = sample_df.copy()
    df_empty["text"] = [" "]
    with pytest.raises(AssertionError):
        addDocument_tolexicon_FI(df_empty)


def test_missing_required_columns(temp_env, sample_df):
    df_missing = sample_df.drop(columns=["url"])
    with pytest.raises(AssertionError):
        addDocument_tolexicon_FI(df_missing)