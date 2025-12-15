import json
import string
import time
from nltk.corpus import stopwords
from barrel_tree import get_barrel

# Loading the lexicon in the RAM
with open('JSON Files/lexicon.json') as f:
    lexicon = json.load(f)

# Ranking configuration (loaded from JSON Files/ranking_config.json with safe defaults)
DEFAULT_RANKING_CONFIG = {
    "version": 1,
    "weights": {
        "tf_title": 10.0,
        "tf_text": 0.5,
        "tag_match": 0.0,
        "recency_days": 0.0,
    },
    "bias": 0.0,
}


def load_ranking_config(path="JSON Files/ranking_config.json"):
    try:
        with open(path, "r") as f:
            cfg = json.load(f)
        if not isinstance(cfg, dict):
            raise ValueError("Ranking config must be a JSON object")
        return cfg
    except Exception as e:
        print(f"Warning: using default ranking config due to error: {e}")
        return DEFAULT_RANKING_CONFIG


RANKING_CONFIG = load_ranking_config()


# ========= Getting the closest match by jaccard similarity =========
'''
Generate all contiguous character n-grams of length n from the given word.
@params
    word: str
        The input string from which n-grams will be generated.
    n: int
        The length of each n-gram (default 3).

    Preconditions:
        - word is a string (isinstance(word, str)).
        - n is an integer and n >= 1.

@return
    A list of strings, each of length n, representing all contiguous n-grams of 'word'.
'''
def generate_ngrams(word, n=3):
    return [word[i:i+n] for i in range(len(word) - n + 1)]


'''
Compute the Jaccard similarity between two collections of n-grams, defined as |intersection| / |union| of their n-gram sets.
@params
    grams1: iterable of hashable items 
    grams2: iterable of hashable items

    Preconditions:
        - grams1 and grams2 are iterable.
        - Elements of grams1 and grams2 are hashable (can be placed in a set).

@return
    A float value in the range [0, 1], representing the Jaccard similarity.
'''
def jaccard_similarity(grams1, grams2):
    intersection = set(grams1).intersection(set(grams2))
    union = set(grams1).union(set(grams2))
    return len(intersection) / len(union)


'''
Given a query string and a lexicon of words, find the lexicon word with the highest Jaccard similarity between their character n-grams.
@params
    query: str
        The input query word to match.
    lexicon: iterable or mapping of strings
        A collection of candidate words.
    n: int
        The n-gram length used to compute Jaccard similarity (default 3).

    Preconditions (for a non-None result):
        - query is a string with length >= n.
        - lexicon is non-empty.
        - Lexicon words are strings; at least one word has length >= n.
        - There exists at least one word in lexicon whose n-grams share
          at least one n-gram with generate_ngrams(query, n).

@return
    A string representing one closest-matching word from the lexicon,
    or None if no word achieves a positive similarity or lexicon is empty.

    Postconditions:
        - The return value 'best_match' is not None.
        - best_match is an element of lexicon.
        - For all words in lexicon:
              similarity(best_match) >= similarity(word).
        - If multiple words achieve the same maximum similarity value:
              The function returns the first such word encountered in the iteration order of lexicon
'''
def get_closest_match(query, lexicon, n=3):
    query_ngrams = generate_ngrams(query, n)
    best_match = None
    best_score = 0

    for word in lexicon:
        word_ngrams = generate_ngrams(word, n)
        score = jaccard_similarity(query_ngrams, word_ngrams)

        if score > best_score:
            best_score = score
            best_match = word
    
    return best_match


# ========= Ranking the documents =========
def calculate_score(posting, ranking_config=None):
    cfg = ranking_config or RANKING_CONFIG
    weights = cfg.get('weights', {}) if isinstance(cfg, dict) else {}
    bias = cfg.get('bias', 0.0) if isinstance(cfg, dict) else 0.0

    tf_title = posting.get('positions', {}).get('title', 0)
    tf_text = posting.get('positions', {}).get('text', 0)
    tag_match = posting.get('tag_match', 0)
    recency_days = posting.get('recency_days', 0)

    score = 0.0
    score += weights.get('tf_title', 0.0) * tf_title
    score += weights.get('tf_text', 0.0) * tf_text
    score += weights.get('tag_match', 0.0) * tag_match
    score += weights.get('recency_days', 0.0) * recency_days
    score += bias

    return score

def rank_documents(postings_list):
    ranked_docs = []
    
    for doc_id, posting in postings_list.items():
        score = calculate_score(posting)
        ranked_docs.append({'ID': doc_id, 'score': score})

    # Sorting the documents based on the score in descending order
    ranked_docs.sort(key=lambda x: x['score'], reverse=True)

    return ranked_docs


# ========= The single word search function =========
'''
Retrieve postings for a single query term from the inverted index.
@params
    query: str
        A single search term (will be lowercased).
    lexicon: mapping[str, int]
        Lexicon mapping terms to word_ids.

Preconditions:
    - query is a non-empty string.
    - lexicon is a mapping of lowercase terms to integer word_ids.
    - Barrel files referenced are readable JSON objects with postings.

@return:
    (postings, term_metadata)
        postings: dict mapping doc_id (str) to posting dict with 'positions' field, or error string if not found.
        term_metadata: dict with independent metadata for this term only:
            - 'message': str or None, describing any fallback (e.g., closest match used) or error.
            - 'term': str, the actual term searched after normalization/correction.

Postconditions:
    - Returns a new, independent term_metadata dict that does not share state with any other call.
    - If term not in lexicon, uses Jaccard correction and sets term_metadata['message'] accordingly.
    - If term found, postings is a dict of doc postings; otherwise returns error string and metadata.
'''
def single_word_search(query, lexicon):
    original_term = query
    query = query.lower()
    
    # Create independent metadata for this term only
    term_metadata = {
        'message': None,
        'term': query,
        'original_term': original_term
    }

    if query not in lexicon:
        closest_match = get_closest_match(query, lexicon)
        print(f'No exact match found.\nInstead, showing results for {closest_match}')
        term_metadata['message'] = f'No exact match found. Instead, showing results for \'{closest_match}\''
        term_metadata['term'] = closest_match
        query = closest_match

    word_id = lexicon.get(query)
    print(f'The word id is {word_id}')
    if word_id is None:
        term_metadata['message'] = f"Word '{query}' not found in the lexicon"
        return None, term_metadata
    
    barrel_file = get_barrel(word_id)
    if barrel_file is None:
        term_metadata['message'] = f"Word '{query}' not found in the inverted index"
        return None, term_metadata
    
    try:
        barrel_start_time = time.perf_counter()
        with open(barrel_file, 'r') as f:
            barrel = json.load(f)
        barrel_end_time = time.perf_counter()
        print(f'{barrel_file} loaded in {(barrel_end_time - barrel_start_time) * 1000} ms.')

        if str(word_id) in barrel:
            return barrel[str(word_id)]['postings'], term_metadata
        else:
            term_metadata['message'] = f"Word '{query}' not found in the barrel file"
            return None, term_metadata
        
    except FileNotFoundError:
        term_metadata['message'] = f"Barrel file '{barrel_file}' not found"
        return None, term_metadata
    

# ========= The multiple word search function =========
'''
Execute a multi-term search query with simple tokenization and stopword filtering, returning ranked postings.
@params
    query_string: str
        Raw user query string to search (may contain punctuation and mixed case).
    lexicon: mapping[str, int]
        Lexicon mapping terms to word_ids; defaults to module-level lexicon.

Preconditions:
    - query_string is a string.
    - lexicon is a mapping of lowercase terms to integer word_ids.
    - Barrel files referenced by terms are readable JSON objects.

@return:
    (ranked_results, result_metadata)
        ranked_results: list of dicts with keys 'ID' and 'score' (top 15 combined intersection/union ranking).
        result_metadata: dict with aggregate metadata for the full query:
            - 'message': str or None, overall feedback (e.g., "No relevant results found. Here are some top results.").
            - 'terms_searched': list of terms actually searched (after normalization).
            - 'per_term_messages': list of per-term messages for transparency (optional).

Postconditions:
    - If query has no valid tokens after cleaning, returns error string (not tuple).
    - If no postings found for any term, returns error string (not tuple).
    - Otherwise returns tuple: (ranked_results[:15], aggregate result_metadata).
    - result_metadata is newly constructed from collected per-term metadata, not shared during collection.
'''
def multiple_word_search(query_string, lexicon=lexicon):
    original_query = query_string
    print(f"\nQuery: {original_query}")

    for char in query_string:
        if char in string.punctuation:
            query_string = query_string.replace(char, '') 

    query_words = query_string.lower().split()  
    if not query_words:
        return f"No result found for query: '{original_query}'\nQuery contains only punctuation marks."
    
    query_words = [word for word in query_words if word not in stopwords.words('english') and word.isalpha()]  
    if not query_words:
        return f"Query '{original_query}' not found in the lexicon."
    
    print(f"Query words: {query_words}")

    # Collect postings and independent per-term metadata
    posting_list = []
    term_metadata_list = []

    for word in query_words:
        postings, term_metadata = single_word_search(word, lexicon)
        term_metadata_list.append(term_metadata)

        if postings is not None and isinstance(postings, dict):
            posting_list.append(postings)  
    
    if not posting_list:
        # Build aggregate metadata from collected term metadata
        aggregate_metadata = {
            'message': f"No result found for query: '{original_query}'",
            'terms_searched': [tm['term'] for tm in term_metadata_list],
            'per_term_messages': [tm['message'] for tm in term_metadata_list if tm['message']]
        }
        return [], aggregate_metadata
    
    # Perform AND operation (intersection) on the posting lists
    intersection_docs = set(posting_list[0].keys())
    for postings in posting_list[1:]:
        intersection_docs.intersection_update(postings.keys())

    ranked_results = []
    if intersection_docs: 
        intersection_postings = {
            doc_id: postings[doc_id] for postings in posting_list for doc_id in intersection_docs
        }
        ranked_results = rank_documents(intersection_postings)
    print(f"Length of intersection: {len(intersection_docs)}")

    # Build aggregate result_metadata
    aggregate_message = None
    
    # Perform OR operation (union) on the posting lists if the result of intersection is very small
    if len(intersection_docs) <= 3:
        if len(intersection_docs) == 0:
            aggregate_message = 'No relevant results found. Here are some top results.'
        
        union_docs = set()

        for posting in posting_list:
            union_docs.update(posting.keys())
        
        # Excluding intersection documents from the union
        union_docs.difference_update(intersection_docs)

        union_postings = {
            doc_id: postings[doc_id] for postings in posting_list for doc_id in union_docs if doc_id in postings
        }
        ranked_results.extend(rank_documents(union_postings))
    
    # Collect per-term messages for transparency
    per_term_messages = [tm['message'] for tm in term_metadata_list if tm.get('message')]
    
    # Build final aggregate metadata
    result_metadata = {
        'message': aggregate_message,
        'terms_searched': [tm['term'] for tm in term_metadata_list],
        'per_term_messages': per_term_messages if per_term_messages else None
    }

    return ranked_results[:15], result_metadata