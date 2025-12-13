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

    # Invariant Assertion
    df = barrel_data[word_id]['df']
    postings = barrel_data[word_id]['postings']
    assert df == len(postings), f"df mismatch for word_id {word_id}: df={df}, postings={len(postings)}"
# =====================================================================================

    # Save the updated barrel data back to the file
    with open(barrel_file, 'w') as f:
        json.dump(barrel_data, f)
    print(f'{barrel_file} updated with {len(barrel_data)} words')


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