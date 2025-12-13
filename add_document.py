import pandas as pd
import json
import string
import os
from nltk import pos_tag
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords, wordnet
from nltk.stem import WordNetLemmatizer



# ----------------------------------------------------------------------------------------------------------
def addDocument(data):
    df = pd.read_csv('Dataset/new_documents.csv')
    print(f'The new documents dataset loaded with shape {df.shape}')

    df_new_doc = pd.DataFrame(data)
    df = pd.concat([df, df_new_doc], ignore_index=True)
    print(f'The new document added to the dataset with shape {df.shape}')

    # Saving this in the same file
    df.to_csv('Dataset/new_documents.csv', index=False)
    print('New Document Added to csv!')

    addDocument_tolexicon_FI(df)
    addDocument_toMetadata(df)

# ----------------------------------------------------------------------------------------------------------

# Function to convert NLTK POS tags to WordNet POS tags
def get_wordnet_pos(tag):
    if tag.startswith('J'):  # Adjective
        return wordnet.ADJ
    elif tag.startswith('V'):  # Verb
        return wordnet.VERB
    elif tag.startswith('N'):  # Noun
        return wordnet.NOUN
    elif tag.startswith('R'):  # Adverb
        return wordnet.ADV
    else:
        return None  # Other POS
    

# Function to preprocess the title and text of the documents
def preprocess(title_text_pairs, doc_ids, lexicon):
    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()

    forward_index = {}
    
    for (title, text), doc_id in zip(title_text_pairs, doc_ids): 
        title_tokens = word_tokenize(title.lower())
        text_tokens = word_tokenize(text.lower())

        title_tokens = [
            lemmatizer.lemmatize(word, pos=get_wordnet_pos(pos_tag([word])[0][1]) or 'n')
            for word in title_tokens if word.isalpha()
            and word not in stop_words 
            and word not in string.punctuation
        ]
        
        text_tokens = [
            lemmatizer.lemmatize(word, pos=get_wordnet_pos(pos_tag([word])[0][1]) or 'n')
            for word in text_tokens if word.isalpha()
            and word not in stop_words 
            and word not in string.punctuation
        ]

        token_ids_title = []
        for word in title_tokens:
            if word not in lexicon:
                lexicon[word] = len(lexicon)  
            token_ids_title.append(lexicon[word])

        token_ids_text = []
        for word in text_tokens:
            if word not in lexicon:
                lexicon[word] = len(lexicon)  
            token_ids_text.append(lexicon[word])

        forward_index[doc_id] = {
            'title': token_ids_title,
            'text': token_ids_text
        }

    return forward_index, lexicon
    

def addDocument_tolexicon_FI(df):
# =====================================================================================
    # Assertions - For lexicon and FI
    
    # Schema must be complete
    required_cols = {'title', 'text', 'url', 'authors', 'tags', 'timestamp', 
                    'text_length', 'title_length', 'num_tags', 'num_authors'}
    missing_cols = required_cols - set(df.columns)
    assert not missing_cols, f"DataFrame missing required columns: {missing_cols}"

    # DataFrame must have at least 1 row (new document)
    assert len(df) >= 1, "DataFrame must contain at least the new document"

    # Last row (new document) must have valid content
    title = df['title'].iloc[-1]
    text = df['text'].iloc[-1]
    assert isinstance(title, str) and title.strip(), "Last row 'title' must be non-empty string"
    assert isinstance(text, str) and text.strip(), "Last row 'text' must be non-empty string"

    # Computed fields must be sensible
    assert df['text_length'].iloc[-1] >= 1, "text_length must be positive"
    assert df['title_length'].iloc[-1] >= 1, "title_length must be positive"
# =====================================================================================

    with open('JSON Files/lexicon.json', 'r') as f:
        lexicon = json.load(f)
    print(f'Lexicon loaded with length: {len(lexicon)}')

    # Initializing the forward index
    forward_index = {}

    # Process the single document
    title = df['title'].iloc[-1]  
    text = df['text'].iloc[-1]    

    starting_doc_id = 192361
    new_doc_id = starting_doc_id + len(df)
    doc_id = f"doc{new_doc_id}"

    # Preprocess the title and text of the document
    forward_index, lexicon = preprocess([(title, text)], [doc_id], lexicon)


    # Saving the updated lexicon to json file
    with open('JSON Files/lexicon.json', 'w') as f:
        json.dump(lexicon, f, indent=4)
    print(f'Lexicon updated with new word(s). Length: {len(lexicon)}')


    # Save the new forward index to the JSON file
    with open('JSON Files/new_forward_index.json', 'w') as f:
        json.dump(forward_index, f, indent=4)
    print('Forward index saved to new_forward_index.json. Length:', len(forward_index))

    addDocument_toBarrel(forward_index)

# ----------------------------------------------------------------------------------------------------------

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
    

'''
Merge a partial inverted index entry for a single word_id into the corresponding barrel file. If the word_id is already present in the barrel, update its postings and df accordingly. 
If not, create a new entry for that word_id. Enforce index invariants for that word_id.

@params
    word_id: int
    A valid word identifier (as used in the lexicon and inverted index)

    Preconditions:
            - word_id is a non-negative integer.
            - get_barrel(word_id) returns a valid path for the barrel file where this word_id belongs.
    
    inverted_data: dict
    An inverted index for the provided word_id

    Preconditions:
            - inverted_data has keys 'df' and 'postings'.
            - inverted_data['df'] equals the number of distinct doc_ids in inverted_data['postings'].
            - For each posting:
                - 'tf' and 'positions' keys exist.
                - 'positions' contains 'title' and 'text'.
                - tf == positions['title'] + positions['text'] and tf ≥ 1.

@returns
    None (no direct return value). Mutates the barrel object by loading and updating the corresponding barrel.

    PostConditions:
        For every word_id that appear in new_forward_index[doc_id]['title'] or ['text'] for any doc_id:
            - The barrel file exists on disk after the call.
            - In that barrel, there is an entry of that word_id with correct posting list structure.
            - For each doc_id ∈ D where word_id appears in its title/text:
                - doc_id is present in postings.
                - tf == positions['title'] + positions['text'] for that doc_id.
            - For that word_id:
                - df equals the number of distinct doc_ids in postings.
        No other word_id entries in barrel_data (i.e., other keys than W_id) are modified by this call.
'''
# Function to add the new inverted index words to the respective barrel
def update_barrel(word_id, inverted_data):
    barrel_file = get_barrel(word_id)

    if os.path.exists(barrel_file):
        with open(barrel_file) as f:
            barrel_data = json.load(f)
        print(f'{barrel_file} loaded with {len(barrel_data)} words')
    else:
        print(f"{barrel_file} does not exist, creating a new barrel.")
        barrel_data = {}

# =====================================================================================
    word_id = str(word_id)
    
    if word_id in barrel_data:
        print(f"Word ID {word_id} already exists in the barrel.")
    

        for doc_id, posting in inverted_data['postings'].items():
            if doc_id not in barrel_data[word_id]['postings']:
                # New document for this word_id → increment df
                barrel_data[word_id]['df'] += 1

            # In all cases, set/overwrite posting
            barrel_data[word_id]['postings'][doc_id] = posting
    else:
        print(f"Word ID {word_id} does not exist, adding to the barrel.")
        barrel_data[word_id] = inverted_data

    # Invariant Assertion, df == len(postings)
    df = barrel_data[word_id]['df']
    postings = barrel_data[word_id]['postings']
    assert df == len(postings), f"df mismatch for word_id {word_id}: df={df}, postings={len(postings)}"

    # Invariant Assertion, positing must have 'tf' and 'position' keys
    for doc_id, posting in barrel_data[word_id]['postings'].items():
        assert 'tf' in posting, (
            f"Missing 'tf' in posting for word_id {word_id}, doc_id {doc_id}"
        )
        assert 'positions' in posting, (
            f"Missing 'positions' in posting for word_id {word_id}, doc_id {doc_id}"
        )

        positions = posting['positions']
        assert isinstance(positions, dict), (
            f"'positions' must be a dict for word_id {word_id}, doc_id {doc_id}"
        )
        assert 'title' in positions and 'text' in positions, (
            f"Missing 'title' or 'text' in positions for word_id {word_id}, doc_id {doc_id}"
        )

    # Invariant Assertion, tf must be equal to the sum of 'title' and 'text'
    for doc_id, posting in barrel_data[word_id]['postings'].items():
        positions = posting['positions']
        title_pos = positions.get('title', 0)
        text_pos = positions.get('text', 0)
        
        # tf must be positive and equal to sum of title + text occurrences
        assert posting['tf'] == title_pos + text_pos, (
            f"tf mismatch for word_id {word_id}, doc_id {doc_id}: "
            f"tf={posting['tf']}, title_pos={title_pos}, text_pos={text_pos}"
        )
        assert posting['tf'] >= 1, (
            f"tf must be >= 1 for word_id {word_id}, doc_id {doc_id}"
        )

# =====================================================================================

    # Save the updated barrel data back to the file
    with open(barrel_file, 'w') as f:
        json.dump(barrel_data, f)
    print(f'{barrel_file} updated with {len(barrel_data)} words')


'''
Given a forward index for one or more documents, construct the corresponding inverted index entries for those word_ids and persistently merge them into
the appropriate barrel files so that the documents become searchable by those words.

@params
    new_forward_index: dict - Forward index of the new document

    PreConditions: 
        - new_forward_index is non-empty.
        - For each doc_id:
            - 'title' and 'text' keys exist.
            - new_forward_index[doc_id]['title'] and ['text'] are lists of non-negative integers (word_ids).
        - All word_ids used in new_forward_index are consistent with the global lexicon (i.e., valid ids).
        - Each document in new_forward_index represents a new logical document to be indexed.

@returns
    None (no direct return value). Mutates the barrel object by loading and updating the corresponding barrel.

    PostConditions:
        For every word_id that appear in new_forward_index[doc_id]['title'] or ['text'] for any doc_id:
            - The barrel file exists on disk after the call.
            - In that barrel, there is an entry of that word_id with correct posting list structure.
            - For each doc_id ∈ D where word_id appears in its title/text:
                - doc_id is present in postings.
                - tf == positions['title'] + positions['text'] for that doc_id.
            - For that word_id:
                - df equals the number of distinct doc_ids in postings.
'''
def addDocument_toBarrel(new_forward_index):
    # Initializing inverted index
    inverted_index = {}

    # Iterate through each document in the forward index
    for doc_id, fields in new_forward_index.items():
        for field, word_ids in fields.items():  # 'field' can be "title" or "text"
            for word_id in word_ids:  # Iterate over word IDs in each field
                if word_id not in inverted_index:
                    inverted_index[word_id] = {"df": 0, "postings": {}}
                
                if doc_id not in inverted_index[word_id]["postings"]:
                    inverted_index[word_id]["postings"][doc_id] = {"tf": 0, "positions": {"title": 0, "text": 0}}
                    inverted_index[word_id]["df"] += 1  
                
                # Increment term frequency and track positions in the respective field
                inverted_index[word_id]["postings"][doc_id]["tf"] += 1
                inverted_index[word_id]["postings"][doc_id]["positions"][field] += 1  # Increment title/text position count
        
    
    print(f'The length of created inverted index: {len(inverted_index)}')

    # Update the barrels with the new inverted index data
    for word_id, inverted_data in inverted_index.items():
        update_barrel(word_id, inverted_data)

    print("Barrels updated successfully.")

# ----------------------------------------------------------------------------------------------------------

def addDocument_toMetadata(df):
# =====================================================================================
    # Assertions - For the Metadata
    
    # Schema check (subset needed for metadata)
    metadata_cols = {'title', 'url', 'authors', 'tags'}
    missing_cols = metadata_cols - set(df.columns)
    assert not missing_cols, f"DataFrame missing metadata columns: {missing_cols}"
    
    # DataFrame must have at least 1 row
    assert len(df) >= 1, "DataFrame must contain the new document for metadata"
    
    # Last row content validation
    title = df['title'].iloc[-1]
    url = df['url'].iloc[-1]
    authors = df['authors'].iloc[-1]
    tags = df['tags'].iloc[-1]
    
    assert isinstance(title, str) and title.strip(), "Metadata title must be non-empty string"
    assert isinstance(url, str) and url.strip(), "Metadata URL must be non-empty string"
    assert isinstance(authors, str), "Authors must be string representation of list"
    assert isinstance(tags, str), "Tags must be string representation of list"
    
    # Load existing metadata and validate structure
    with open('JSON Files/metadata.json', 'r') as f:
        metadata = json.load(f)
    assert isinstance(metadata, dict), "Metadata must be a dictionary"
    
    print(f'Metadata loaded with length: {len(metadata)}')
# =====================================================================================
    
    # Add the new document to the metadata file
    print(f'Dataset loaded with {df.shape}\n')

    starting_doc_id = 192361
    new_doc_id = starting_doc_id + len(df)
    doc_id = f"doc{new_doc_id}"
    
    metadata[doc_id] = {
        "title": df['title'].iloc[-1],
        "url": df['url'].iloc[-1],
        "authors": df['authors'].iloc[-1],
        "tags": df['tags'].iloc[-1],
    }

    # Final assertion: verify new entry was created
    assert doc_id in metadata, f"Failed to add doc_id {doc_id} to metadata"
    assert metadata[doc_id]['title'] == title, "Metadata title mismatch"

    # Save updated metadata back to the file
    with open('JSON Files/metadata.json', 'w') as f:
        json.dump(metadata, f, indent=4)
    print("Metadata saved to 'metadata.json'")

    print(f'Metadata updated with new document. Length: {len(metadata)}')
    print(dict([list(metadata.items())[-1]]))