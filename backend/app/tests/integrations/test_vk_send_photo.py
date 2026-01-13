import pytest
import asyncio
from uuid import UUID

from app.integrations.vk.send_photo import VkSendPhotoIntegration


@pytest.fixture
def integration():
    """Создает экземпляр VK Send Photo интеграции."""
    return VkSendPhotoIntegration()


def test_vk_send_photo_metadata(integration):
    """Тест метаданных VK Send Photo интеграции."""
    metadata = integration.metadata
    
    assert metadata.id == "vk_send_photo"
    assert metadata.version == "1.0.1"
    assert metadata.name == "VK Send Photo"
    assert metadata.category == "messaging"
    assert metadata.credentials_provider == "other"
    assert metadata.credentials_strategy == "api_key"


class DummyLogger:
    def __init__(self):
        self.errors = []

    async def error(self, msg):
        self.errors.append(msg)


class DummyCredentialsResolver:
    def __init__(self, creds):
        self._creds = creds

    async def get_default_for(self, *, bot_id: UUID, provider: str, strategy: str | None):
        return self._creds


@pytest.mark.asyncio
async def test_vk_send_photo_success(monkeypatch, tmp_path):
    # Prepare a dummy image file
    photo = tmp_path / "test.jpg"
    photo.write_bytes(b"JPEGDATA")

    # Prepare credentials
    creds = {"payload": {"access_token": "fake_token"}}
    creds_resolver = DummyCredentialsResolver(creds)
    logger = DummyLogger()

    # Fake vk_api objects
    class FakeUpload:
        def __init__(self, session):
            pass

        def photo_messages(self, paths):
            return [{"owner_id": 1, "id": 2, "access_key": "k"}]

    class FakeVk:
        def __init__(self):
            pass

        def messages(self):
            pass

        def messages_send(self, **kwargs):
            return {"message_id": 123}

    class FakeVkApi:
        def __init__(self, token=None):
            self._token = token

        def get_api(self):
            class API:
                def __init__(self):
                    self.messages = self

                def send(self, **kw):
                    return {"message_id": 123}

            return API()

    # Monkeypatch vk_api classes used in integration
    monkeypatch.setattr("app.integrations.vk.send_photo.VkApi", FakeVkApi)
    monkeypatch.setattr("app.integrations.vk.send_photo.VkUpload", FakeUpload)
    # Ensure integration believes vk-api is available
    monkeypatch.setattr("app.integrations.vk.send_photo.VK_API_AVAILABLE", True)

    integration = VkSendPhotoIntegration()

    config = {"peer_id": 9999, "photo_path": str(photo), "message": "Hi"}
    result = await integration.execute(config, creds_resolver, UUID(int=1), logger)

    assert result["response"]["ok"] is True
    assert "result" in result["response"]


@pytest.mark.asyncio
async def test_vk_send_photo_api_error(monkeypatch, tmp_path):
    photo = tmp_path / "test.jpg"
    photo.write_bytes(b"JPEGDATA")

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
                def __init__(self):
                    self.messages = self

                def send(self, **kw):
                    raise Exception("vk api send failed")

            return API()

    monkeypatch.setattr("app.integrations.vk.send_photo.VkApi", FakeVkApiErr)
    monkeypatch.setattr("app.integrations.vk.send_photo.VkUpload", FakeUploadError)
    # Ensure integration believes vk-api is available
    monkeypatch.setattr("app.integrations.vk.send_photo.VK_API_AVAILABLE", True)

    integration = VkSendPhotoIntegration()
    config = {"peer_id": 9999, "photo_path": str(photo), "message": "Hi"}
    result = await integration.execute(config, creds_resolver, UUID(int=1), logger)

    assert result["response"]["ok"] is False
    assert logger.errors
