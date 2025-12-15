from search_engine import get_closest_match

# get_closest_match(query, lexicon, n=3)
# ------ Partitions ------
# exact match
# fuzzy match
# no overlap
# ambiguous / tie
# empty lexicon
# short query < n

# test case 01:
# exact match
def test_exact_match():
    lexicon = ["apple", "banana"]
    query = "banana"
    assert get_closest_match(query, lexicon) == "banana"

# test case 02:
# fuzzy match
def test_fuzzy_match():
    lexicon = ["search", "engine"]
    query = "serch"
    assert get_closest_match(query, lexicon) == "search"

# test case 03:
# no overlap
def test_no_overlap():
    lexicon = ["abc", "def"]
    query = "xyz"
    assert get_closest_match(query, lexicon) is None

# test case 04:
# ambiguous / tie
def test_tie_breaking():
    lexicon = ["pesting", "resting"]
    query = "testing"
    assert get_closest_match(query, lexicon) in {"pesting", "resting"}

# test case 05:
# empty lexicon
def test_empty_lexicon():
    lexicon = []
    query = "search"
    assert get_closest_match(query, lexicon) is None

# test case 06:
# short query < n
def test_short_query():
    lexicon = ["hi", "hit"]
    query = "hi"
    assert get_closest_match(query, lexicon) in {"hi", "hit", None}











