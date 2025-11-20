from .base import AuthWebsocketBase
from .bot import AuthWebsocketBot
from .channel import AuthWebsocketChannel

from typing import Annotated


AuthWebsocketDataChannel = AuthWebsocketChannel.authorize(entity_type="channel")
AuthWebsocketDataChannelDep = Annotated[dict, AuthWebsocketDataChannel]

AuthWebsocketDataBot = AuthWebsocketBot.authorize(entity_type="bot")
AuthWebsocketDataBotDep = Annotated[dict, AuthWebsocketDataBot]