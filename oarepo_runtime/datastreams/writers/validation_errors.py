def format_validation_error(err_messages):
    msg = {}
    for err, path in flatten_errors(err_messages, ""):
        if path.endswith("._schema") and err == "Unknown field.":
            continue
        path = path.replace(".value.", ".")
        msg[path] = err
    return msg


def flatten_errors(err_data, path):
    if isinstance(err_data, (list, tuple)):
        for err in err_data:
            yield from flatten_errors(err, path)
    elif isinstance(err_data, dict):
        for k, v in err_data.items():
            subpath = f"{path}.{k}" if path else k
            yield from flatten_errors(v, subpath)
    else:
        yield str(err_data), path
