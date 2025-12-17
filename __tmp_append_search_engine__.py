# ========= Boolean query parsing and evaluation =========
from boolean_query_parser import parse as parse_boolean


def _looks_like_boolean_query(q: str) -> bool:
    upper = q.upper()
    return any(op in upper for op in (" AND ", " OR ", " NOT ")) or "(" in q or ")" in q


def _load_all_doc_ids(path="JSON Files/metadata.json"):
    try:
        with open(path, "r") as f:
            metadata = json.load(f)
        # metadata is expected to be a mapping from doc_id to info
        return set(metadata.keys()) if isinstance(metadata, dict) else set()
    except Exception:
        # If metadata missing or unreadable, fall back to empty set
        return set()


def _sum_postings(postings_maps, restrict_to=None):
    """Aggregate postings across terms by summing title/text counts per doc."""
    aggregated = {}
    for pm in postings_maps:
        if not pm or not isinstance(pm, dict):
            continue
        for doc_id, posting in pm.items():
            if restrict_to is not None and doc_id not in restrict_to:
                continue
            pos = posting.get("positions", {})
            title = pos.get("title", 0)
            text = pos.get("text", 0)
            agg = aggregated.setdefault(doc_id, {"positions": {"title": 0, "text": 0}})
            agg_pos = agg["positions"]
            agg_pos["title"] += title
            agg_pos["text"] += text
    return aggregated


def _evaluate_ast(node, lexicon, universe):
    """Return (doc_set, postings_map) for AST node.
    For NOT nodes, postings_map is empty (used only for filtering).
    """
    from boolean_query_parser import Word, And, Or, Not

    if isinstance(node, Word):
        postings, _meta = single_word_search(node.term, lexicon)
        postings = postings or {}
        return set(postings.keys()), postings

    if isinstance(node, Not):
        child_set, _child_pm = _evaluate_ast(node.child, lexicon, universe)
        return (universe - child_set), {}

    if isinstance(node, And):
        child_sets = []
        child_pms = []
        for part in node.parts:
            s, pm = _evaluate_ast(part, lexicon, universe)
            child_sets.append(s)
            child_pms.append(pm)
        if not child_sets:
            return set(), {}
        inter = child_sets[0].copy()
        for s in child_sets[1:]:
            inter.intersection_update(s)
        aggregated = _sum_postings(child_pms, restrict_to=inter)
        return inter, aggregated

    if isinstance(node, Or):
        child_sets = []
        child_pms = []
        for part in node.parts:
            s, pm = _evaluate_ast(part, lexicon, universe)
            child_sets.append(s)
            child_pms.append(pm)
        union = set()
        for s in child_sets:
            union.update(s)
        aggregated = _sum_postings(child_pms, restrict_to=union)
        return union, aggregated

    # Unknown node type
    return set(), {}


def boolean_search(query_string, lexicon=lexicon):
    try:
        ast = parse_boolean(query_string)
    except SyntaxError as e:
        return [], {"message": f"Invalid boolean query: {e}", "terms_searched": [], "per_term_messages": None}

    universe = _load_all_doc_ids()
    doc_set, postings_map = _evaluate_ast(ast, lexicon, universe)

    if not doc_set:
        return [], {"message": "No documents match the boolean query.", "terms_searched": [], "per_term_messages": None}

    ranked = rank_documents(postings_map)
    return ranked[:15], {"message": None, "terms_searched": [], "per_term_messages": None}


# Hook boolean parser into multiple_word_search when operators are present
_old_multiple_word_search = multiple_word_search


def multiple_word_search(query_string, lexicon=lexicon):
    if _looks_like_boolean_query(query_string):
        return boolean_search(query_string, lexicon=lexicon)
    return _old_multiple_word_search(query_string, lexicon=lexicon)
