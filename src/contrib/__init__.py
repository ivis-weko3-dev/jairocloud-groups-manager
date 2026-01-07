#
# Copyright (C) 2025 National Institute of Informatics.
#

"""Provides utilities to contribute to development."""

import json
import pathlib

from flask import current_app


if current_app.config["ENV"] != "development" or not current_app.debug:
    error = "Contrib utilities can only be used in development mode with debug enabled."
    raise RuntimeError(error)


def dump(obj: object, name: str) -> None:
    """Dump the given object into a file.

    The object will be dumped as JSON if possible, otherwise as plain text.

    Args:
        obj (object): The object to dump.
        name (str): The name of the file (without extension).
    """
    instance_path = pathlib.Path(current_app.instance_path) / "contrib"
    instance_path.mkdir(parents=True, exist_ok=True)

    try:
        if isinstance(obj, str) and obj.strip().startswith(("{", "[")):
            parsed = json.loads(obj)
            with (instance_path / f"{name}.json").open("w", encoding="utf-8") as f:
                json.dump(parsed, f, indent=2, ensure_ascii=False)
            return
        if not isinstance(obj, (str, bytes)):
            with (instance_path / f"{name}.json").open("w", encoding="utf-8") as f:
                json.dump(obj, f, indent=2, ensure_ascii=False)
            return
    except TypeError, ValueError, json.JSONDecodeError:
        pass

    file_path = instance_path / f"{name}.txt"

    if isinstance(obj, str):
        with file_path.open("w", encoding="utf-8") as f:
            f.write(obj)
        return
    if isinstance(obj, bytes):
        with file_path.open("w", encoding="utf-8") as f:
            f.write(obj.decode("utf-8", errors="replace"))
        return

    with file_path.open("w", encoding="utf-8") as f:
        f.write(repr(obj))
    return
