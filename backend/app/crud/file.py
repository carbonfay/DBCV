from pathlib import Path
from fastapi import File


def delete_file(path):
    try:
        Path(path).unlink()
    except FileNotFoundError:
        ...


async def save_file(path: Path, file: File):
    path.parent.mkdir(exist_ok=True, parents=True)
    path.touch()
    with path.open("wb+") as buffer:
        buffer.write(await file.read())