import os
from typing import Callable, IO


def atomic_write(path, init_file: Callable[[IO], None], modify_file: Callable[[IO], None], read_file: Callable[[IO], None] = None):
    if not os.path.isfile(path):
        with open(path, "ab") as f:
            init_file(f)

    with open(path, "rb+") as f:
        read_file(f)

    temp_file_path = path + ".temp"
    with open(temp_file_path, "wb+") as temp_file:
        modify_file(temp_file)

    os.replace(temp_file_path, path)