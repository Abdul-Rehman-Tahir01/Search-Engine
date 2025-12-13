from urllib.parse import urlparse
from flask import Flask, render_template, jsonify, request
import json
import time
from search_engine import multiple_word_search
from add_document import addDocument

# Start the Flask app
app = Flask(__name__)

lexicon = None
metadata = None

# Loading the lexicon and metadata file in the RAM
def load_lexicon():
    global lexicon
    try:
        lex_start_time = time.perf_counter()
        with open('JSON Files/lexicon.json') as f:
            lexicon = json.load(f)
        lex_end_time = time.perf_counter()
        print(f'\nLexicon loaded in {(lex_end_time - lex_start_time) * 1000} ms.')
    except FileNotFoundError:
        print('Lexicon or Metadata file not found.')
    return lexicon

def load_metadata():
    global metadata
    try:
        meta_start_time = time.perf_counter()
        with open('JSON Files/metadata.json') as f:
            metadata = json.load(f)
        meta_end_time = time.perf_counter()
        print(f'Metadata loaded in {(meta_end_time - meta_start_time) * 1000} ms.')
    except FileNotFoundError:
        print('Lexicon or Metadata file not found.')
    return metadata

# Function for defining results
def results_with_metadata(results):
    enriched_results = []
    for result in results:
        doc_id = result['ID']
        score = result['score']

        if doc_id in metadata:
            tags = metadata[doc_id]['tags'].replace('[', '').replace(']', '').replace("'", '')
            authors = metadata[doc_id]['authors'].replace('[', '').replace(']', '').replace("'", '')

            enriched_result = {
                "doc_id": doc_id,
                "score": score,
                "title": metadata[doc_id]["title"],
                "url": metadata[doc_id]["url"],
                "tags": tags if len(tags) > 0 else "Not Provided",
                "authors": authors if len(authors) > 0 else "Not Provided",
            }
            enriched_results.append(enriched_result)
    return enriched_results


# Function for processing input
def processInput(title, text, url, authors, timestamp, tags):
    """
    Second line of defense: Backend validation of untrusted client data.
    Assumes frontend did basic checks, but verifies everything independently.
    """
# =====================================================================================    
    # Validation checks
    
    # Type and basic format checks
    if not isinstance(title, str):
        raise ValueError("Title must be a string")
    if not isinstance(text, str):
        raise ValueError("Text must be a string")
    if not isinstance(url, str):
        raise ValueError("URL must be a string")
    if not isinstance(authors, str):
        raise ValueError("Authors must be a string")
    if not isinstance(tags, str):
        raise ValueError("Tags must be a string")
    if not isinstance(timestamp, str):
        raise ValueError("Timestamp must be a string")
    
    # URL format validation (comprehensive)
    try:
        parsed_url = urlparse(url)
        if parsed_url.scheme not in ['http', 'https']:
            raise ValueError("URL must use http:// or https:// protocol")
        if not parsed_url.netloc:  # No domain
            raise ValueError("URL must contain a valid domain")
    except:
        raise ValueError("Invalid URL format")
    
    # Authors: valid comma-separated format
    authors_list = [a.strip() for a in authors.split(',') if a.strip()]
    if len(authors_list) == 0:
        raise ValueError("At least one author required")
    if len(authors_list) > 10:
        raise ValueError("Maximum 10 authors allowed")
    
    # Tags: valid comma-separated format
    tags_list = [t.strip() for t in tags.split(',') if t.strip()]
    if len(tags_list) == 0:
        raise ValueError("At least one tag required")
    if len(tags_list) > 15:
        raise ValueError("Maximum 15 tags allowed")
# =====================================================================================    

    tags_clean = [tag.strip() for tag in tags.split(',')]
    authors_clean = [author.strip() for author in authors.split(',')]

    text_length = len(text.split())
    title_length = len(title.split())
    num_tags = len(tags)
    num_authors = len(authors)

    data = {
        'title': [title],
        'text': [text],
        'url': [url],
        'authors': [str(authors_clean)],
        'timestamp': [timestamp],
        'tags': [str(tags_clean)],
        'text_length': [text_length],
        'title_length': [title_length],
        'num_tags': [num_tags],
        'num_authors': [num_authors]
    }

    return data


# Defining routes
@app.route('/')
def home():
    return render_template('index.html')


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return jsonify({'error': 'No query provided'}), 400

    # Calling the multiple_word_search() function from the script to perform the search
    try:
        search_start_time = time.perf_counter()
        search_results, result_metadata = multiple_word_search(query, lexicon)
        print(search_results)
        print(f'Length of search result: {len(search_results)}')
        search_end_time = time.perf_counter()
        print(f'Search completed in {(search_end_time - search_start_time) * 1000} ms.')

        result_start_time = time.perf_counter()
        final_results = results_with_metadata(search_results)
        print(f'Length of final result: {len(final_results)}')
        result_end_time = time.perf_counter()
        print(f'Results enriched in {(result_end_time - result_start_time) * 1000} ms.')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
    return jsonify({"results": final_results, 'message': result_metadata['message']})


@app.route('/add-document')
def add_document():
    return render_template('add_document.html')


@app.route('/submit-document', methods=['POST'])
def submit_document():
    try:
        # Retrieve JSON data from the request
        data = request.get_json()
        if not data:
            return jsonify({'message': 'No JSON data provided'}), 400

        title = data.get('title')
        text = data.get('text')
        url = data.get('url')
        authors = data.get('authors')
        timestamp = data.get('timestamp')
        tags = data.get('tags')

        data_made = processInput(title, text, url, authors, timestamp, tags)
        print(data_made)

        addDocuemnt_start_time = time.perf_counter()
        addDocument(data_made)
        addDocuemnt_end_time = time.perf_counter()
        print(f'Document added in {(addDocuemnt_end_time - addDocuemnt_start_time) * 1000} ms.')

        load_lexicon()
        load_metadata()

        return jsonify({'message': 'Document added successfully!'}), 200
    
    except ValueError as ve:
        return jsonify({'message': str(ve)}), 400
    except Exception as e:
        return jsonify({'message': str(e)}), 500


# Running the Flask app
if __name__ == '__main__':
    load_lexicon()
    load_metadata()

    app.run(debug=True)