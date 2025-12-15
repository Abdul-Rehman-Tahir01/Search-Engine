"""Shared barrel range tree and lookup helpers for selecting barrel files by word_id."""

BARREL_TREE = {
    "start": 0,
    "end": 10 ** 9,  # large upper bound
    "path_prefix": "JSON Files/Barrels",
    "children": [
        {
            "start": 0,
            "end": 10000,
            "path_prefix": "JSON Files/Barrels/barrel_10",
            "leaf_size": 10,  # each leaf barrel covers 10 word_ids
            "children": []
        },
        {
            "start": 10000,
            "end": 30000,
            "path_prefix": "JSON Files/Barrels/barrel_250",
            "leaf_size": 250,  # each leaf barrel covers 250 word_ids
            "children": []
        },
        {
            "start": 30000,
            "end": 10 ** 9,
            "path_prefix": "JSON Files/Barrels/barrel_10000",
            "leaf_size": 10000,  # each leaf barrel covers 10000 word_ids
            "children": []
        }
    ]
}


def _get_barrel_recursive(word_id, node):
    """Recursively locate the barrel file for a given word_id based on range splits."""
    if not (node["start"] <= word_id < node["end"]):
        raise ValueError(f"word_id {word_id} out of range [{node['start']}, {node['end']})")

    children = node.get("children", [])
    if not children:
        leaf_size = node["leaf_size"]
        local_index = (word_id - node["start"]) // leaf_size
        barrel_index = local_index + 1
        return f"{node['path_prefix']}/barrel_{leaf_size}_{barrel_index}.json"

    for child in children:
        if child["start"] <= word_id < child["end"]:
            return _get_barrel_recursive(word_id, child)

    raise ValueError(f"No child range found for word_id {word_id}")


def get_barrel(word_id, root=BARREL_TREE):
    return _get_barrel_recursive(word_id, root)
