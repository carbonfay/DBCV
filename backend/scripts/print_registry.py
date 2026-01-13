import json
from app.integrations import registry

meta = registry.list_all()
out = []
for m in meta:
    out.append({
        'id': m.id,
        'version': m.version,
        'name': m.name,
        'category': m.category,
        'library_name': getattr(m, 'library_name', None),
    })
print(json.dumps(out, ensure_ascii=False, indent=2))
