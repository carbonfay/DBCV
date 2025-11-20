from fastapi import APIRouter

from app.api.routes import (login, users, channels, bots, steps, messages,
                            widgets, requests, attachments, sockets, emitters, notes, cron, credentials, autonomous_assistant,
                            integrations, presets, icons)
from app.api.routes import credentials_common
from app.api.routes.connections import connections, connection_groups
from app.api.routes.templates import templates, template_instance, template_group
api_router = APIRouter()
api_router.include_router(login.router, tags=["login"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(channels.router, prefix="/channels", tags=["channels"])
api_router.include_router(messages.router, prefix="/messages", tags=["messages"])
api_router.include_router(bots.router, prefix="/bots", tags=["bots"])
api_router.include_router(steps.router, prefix="/steps", tags=["steps"])
api_router.include_router(widgets.router, prefix="/widgets", tags=["widgets"])
api_router.include_router(notes.router, prefix="/notes", tags=["notes"])
api_router.include_router(requests.router, prefix="/requests", tags=["requests"])
api_router.include_router(connections.router, prefix="/connections", tags=["connections"])
api_router.include_router(connection_groups.router, prefix="/connection_groups", tags=["connection_groups"])
api_router.include_router(emitters.router, prefix="/emitters", tags=["emitters"])
api_router.include_router(cron.router, prefix="/crons", tags=["crons"])
api_router.include_router(templates.router, prefix="/templates", tags=["templates"])
api_router.include_router(template_instance.router, prefix="/template_instance", tags=["template_instance"])
api_router.include_router(template_group.router, prefix="/template_group", tags=["template_group"])
api_router.include_router(attachments.router, prefix="/attachments", tags=["attachments"])
api_router.include_router(credentials.router, prefix="/bots/{bot_id}/credentials", tags=["credentials"])
api_router.include_router(credentials_common.router, prefix="/credentials", tags=["credentials-common"])
api_router.include_router(autonomous_assistant.router, prefix="/autonomous-assistant", tags=["autonomous-assistant"])
api_router.include_router(integrations.router, prefix="/integrations", tags=["integrations"])
api_router.include_router(presets.router, prefix="/presets", tags=["presets"])
api_router.include_router(icons.router, prefix="/icons", tags=["icons"])
