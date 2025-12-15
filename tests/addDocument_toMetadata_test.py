import json
import os
import pandas as pd
import pytest
from add_document import addDocument_toMetadata


@pytest.fixture()
def temp_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    os.makedirs("JSON Files", exist_ok=True)
    # seed metadata file
    with open("JSON Files/metadata.json", "w") as f:
        json.dump({}, f)
    yield tmp_path


@pytest.fixture()
def sample_df():
    return pd.DataFrame(
        {
            "title": ["Doc"],
            "url": ["http://example.com"],
            "authors": ["['a']"],
            "tags": ["['t']"],
            "timestamp": ["2024-01-01"],
            "text": ["body"],
        }
    )


def test_valid_metadata(temp_env, sample_df):
    addDocument_toMetadata(sample_df)
    with open("JSON Files/metadata.json") as f:
        metadata = json.load(f)
    assert len(metadata) == 1


def test_missing_fields(temp_env, sample_df):
    df_missing = sample_df.drop(columns=["title"])
    with pytest.raises(AssertionError):
        addDocument_toMetadata(df_missing)


def test_empty_df(temp_env, sample_df):
    df_empty = sample_df.iloc[0:0]
    with pytest.raises(AssertionError):
        addDocument_toMetadata(df_empty)