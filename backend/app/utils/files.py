import json
import tempfile
import os


async def create_temp_json_file(data):
    temp_file = tempfile.NamedTemporaryFile(mode="w+", suffix=".json", delete=False)
    json.dump(data, temp_file, indent=4)
    temp_file.seek(0)
    temp_file.close()
    return temp_file.name