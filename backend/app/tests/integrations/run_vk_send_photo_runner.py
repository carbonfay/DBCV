import asyncio
import os
from uuid import UUID
from pathlib import Path
import tempfile

from app.integrations.vk import send_photo as vk_module
from app.integrations.vk.send_photo import VkSendPhotoIntegration


class DummyLogger:
    def __init__(self):
        self.errors = []

    async def error(self, msg):
        self.errors.append(str(msg))


class DummyCredentialsResolver:
    def __init__(self, creds):
        self._creds = creds

    async def get_default_for(self, *, bot_id: UUID, provider: str, strategy: str | None):
        return self._creds


async def run_success_case():
    # prepare temp photo
    tmp = tempfile.gettempdir()
    photo_path = os.path.join(tmp, "runner_test.jpg")
    Path(photo_path).write_bytes(b"JPEGDATA")

    creds = {"payload": {"access_token": "fake_token"}}
    creds_resolver = DummyCredentialsResolver(creds)
    logger = DummyLogger()

    class FakeUpload:
        def __init__(self, session):
            pass

        def photo_messages(self, paths):
            return [{"owner_id": 1, "id": 2, "access_key": "k"}]

    class FakeVkApi:
        def __init__(self, token=None):
            self._token = token

        def get_api(self):
            class API:
                def __getattr__(self, item):
                    if item == "messages":
                        class Msgs:
                            def send(self_inner, **kw):
                                return {"message_id": 123}

                        return Msgs()
                    raise AttributeError(item)

            return API()

    # patch module
    vk_module.VkApi = FakeVkApi
    vk_module.VkUpload = FakeUpload
    vk_module.VK_API_AVAILABLE = True

    integration = VkSendPhotoIntegration()
    config = {"peer_id": 9999, "photo_path": photo_path, "message": "Hi from runner"}
    result = await integration.execute(config, creds_resolver, UUID(int=1), logger)
    print("SUCCESS CASE RESULT:")
    print(result)
    print("LOGGER ERRORS:", logger.errors)


async def run_error_case():
    tmp = tempfile.gettempdir()
    photo_path = os.path.join(tmp, "runner_test.jpg")

    creds = {"payload": {"access_token": "fake_token"}}
    creds_resolver = DummyCredentialsResolver(creds)
    logger = DummyLogger()

    class FakeUploadError:
        def __init__(self, session):
            pass

        def photo_messages(self, paths):
            return [{"owner_id": 1, "id": 2}]

    class FakeVkApiErr:
        def __init__(self, token=None):
            pass

        def get_api(self):
            class API:
                def __getattr__(self, item):
                    if item == "messages":
                        class Msgs:
                            def send(self_inner, **kw):
                                raise Exception("vk api send failed")

                        return Msgs()
                    raise AttributeError(item)

            return API()

    vk_module.VkApi = FakeVkApiErr
    vk_module.VkUpload = FakeUploadError
    vk_module.VK_API_AVAILABLE = True

    integration = VkSendPhotoIntegration()
    config = {"peer_id": 9999, "photo_path": photo_path, "message": "Hi error"}
    result = await integration.execute(config, creds_resolver, UUID(int=1), logger)
    print("ERROR CASE RESULT:")
    print(result)
    print("LOGGER ERRORS:", logger.errors)


if __name__ == "__main__":
    asyncio.run(run_success_case())
    asyncio.run(run_error_case())
