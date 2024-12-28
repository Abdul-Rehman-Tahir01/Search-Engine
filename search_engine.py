import json
import string
import time
from nltk.corpus import stopwords

# Loading the lexicon in the RAM
with open('JSON Files/lexicon.json') as f:
    lexicon = json.load(f)


# Getting the closest match by jaccard similarity
def generate_ngrams(word, n=3):
    return [word[i:i+n] for i in range(len(word) - n + 1)]

def jaccard_similarity(grams1, grams2):
    intersection = set(grams1).intersection(set(grams2))
    union = set(grams1).union(set(grams2))
    return len(intersection) / len(union)

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


# Determining which barrel to search based on the word id
def get_barrel(word_id):
    # For barrel_10_1 to barrel_10_1000 (First 10000 words)
    if word_id < 10000:
        barrel_index = (word_id // 10) + 1
        return f'Barrels/barrel_10/barrel_10_{barrel_index}.json'
    
    # For barrel_250_1 to barrel_250_80 (Next 20000 words)
    elif word_id >= 10000 and word_id < 30000:
        barrel_index = ((word_id-10000) // 250) + 1
        return f'Barrels/barrel_250/barrel_250_{barrel_index}.json'
    
    # For barrel_10000_1 to barrel_10000_46 (Remaining words)
    else:
        barrel_index = (word_id // 10000) - 2
        return f'Barrels/barrel_10000/barrel_10000_{barrel_index}.json'


# Ranking the documents
def calculate_score(posting):
    score = 0

    # Getting the term frequency from the title and the text of document
    tf_title = posting['positions'].get('title', 0)
    tf_text = posting['positions'].get('text', 0)

    # Calculating the score
    score = (tf_title*10) + (tf_text*0.5)  # Giving more weight to the title than the text
    return score

def rank_documents(postings_list):
    ranked_docs = []
    
    for doc_id, posting in postings_list.items():
        score = calculate_score(posting)
        ranked_docs.append({'ID': doc_id, 'score': score})

    # Sorting the documents based on the score in descending order
    ranked_docs.sort(key=lambda x: x['score'], reverse=True)

    return ranked_docs


# The single word search function
def single_word_search(query, lexicon):
    query = query.lower()  # Normalizing the query
    result_metadata = {'message': None}

    if query not in lexicon:
        closest_match = get_closest_match(query, lexicon)
        print(f'No exact match found.\nInstead, showing results for {closest_match}')
        result_metadata['message'] = f'No exact match found. Instead, showing results for \'{closest_match}\''
        query = closest_match

    word_id = lexicon[query]
    print(f'The word id is {word_id}')
    if word_id is None:
        return f"Word '{query}' not found in the lexicon", result_metadata
    
    barrel_file = get_barrel(word_id)
    if barrel_file is None:
        return f"Word '{query}' not found in the inverted index", result_metadata
    
    try:
        barrel_start_time = time.perf_counter()
        with open(barrel_file, 'r') as f:
            barrel = json.load(f)
        barrel_end_time = time.perf_counter()
        print(f'{barrel_file} loaded in {(barrel_end_time - barrel_start_time) * 1000} ms.')

        if str(word_id) in barrel:
            return barrel[str(word_id)]['postings'], result_metadata
        else:
            return f"Word '{query}' not found in the barrel file", result_metadata
        
    except FileNotFoundError:
        return f"Barrel file '{barrel_file}' not found", result_metadata
    

# The multiple word search function
def multiple_word_search(query_string, lexicon=lexicon):
    original_query = query_string
    print(f"\nQuery: {original_query}")

    # Removing punctuation marks from the query
    for char in query_string:
        if char in string.punctuation:
            query_string = query_string.replace(char, '')  # Removing punctuation marks from the query

    query_words = query_string.lower().split()  # Normalizing and then splitting the query
    if not query_words:
        return f"No result found for query: '{original_query}'\nQuery contains only punctuation marks."
    
    query_words = [word for word in query_words if word not in stopwords.words('english') and word.isalpha()]  
    if not query_words:
        return f"Query '{original_query}' not found in the lexicon."
    
    print(f"Query words: {query_words}")

    # Getting the list of documents for each word in the query
    posting_list = []

    # Fetch posting list for each word in the query
    for word in query_words:
        postings, result_metadata = single_word_search(word, lexicon)

        if postings is not None and isinstance(postings, dict):
            posting_list.append(postings)  
    
    if not posting_list:
        return f"No result found for query: '{original_query}'"
    
    # Perform AND operation (intersection) on the posting lists
    intersection_docs = set(posting_list[0].keys())
    for postings in posting_list[1:]:
        intersection_docs.intersection_update(postings.keys())

    # Collecting final postings from intersection
    ranked_results = []
    if intersection_docs: 
        intersection_postings = {
            doc_id: postings[doc_id] for postings in posting_list for doc_id in intersection_docs
        }
        ranked_results = rank_documents(intersection_postings)
    print(f"Length of intersection: {len(intersection_docs)}")

    # Perform OR operation (union) on the posting lists if the result of intersection is very small
    if len(intersection_docs) <= 3:
        if(len(intersection_docs) == 0):
            result_metadata['message'] = 'No relevant results found. Here are some top results.'
        
        union_docs = set()

        for posting in posting_list:
            union_docs.update(posting.keys())
        
        # Excluding intersection documents from the union
        union_docs.difference_update(intersection_docs)

        # Collecting final postings from union
        union_postings = {
            doc_id: postings[doc_id] for postings in posting_list for doc_id in union_docs if doc_id in postings
        }
        ranked_results.extend(rank_documents(union_postings))

    return ranked_results[:15], result_metadata