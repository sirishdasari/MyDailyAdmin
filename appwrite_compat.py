def normalize_limit(limit, default=25, maximum=100):
    return max(1, min(int(limit or default), maximum))


def to_plain(value):
    if hasattr(value, "to_dict"):
        value = value.to_dict()
    elif hasattr(value, "model_dump"):
        value = value.model_dump(by_alias=True, mode="json")

    if isinstance(value, list):
        return [to_plain(item) for item in value]
    if isinstance(value, dict):
        return {key: to_plain(item) for key, item in value.items()}

    return value


def flatten_row(row):
    data = to_plain(row)
    if isinstance(data, dict) and isinstance(data.get("data"), dict):
        nested = data.pop("data")
        data.update(nested)
    return data


def get_list_items(result, name):
    if isinstance(result, dict):
        items = result.get(name, [])
    else:
        items = getattr(result, name, [])
    return [flatten_row(item) if name == "rows" else to_plain(item) for item in items]
