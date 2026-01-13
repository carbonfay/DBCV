import asyncio
import vk_api

async def test_vk_token():
    token = "vk1.a.GaAwWm4-DDSNNDaP5KA06keLpDKayAI4rh-F7J7oak0zJ1nEGrzfvAJaFaiVv1BTZJ0Q7PEMd48xpPeNL_fr6wGRhoA6Ak56-1sjVzPDNxGDr5dO1lUiv6zsUOvHzPdPrGByiHlT3bszLq-Z3he-XH_oRBGZGIrWOaJSoZaDv40sybHrrS3fZvkE_VIn16Nkq2Q_i2cklxCKhDO3548fiw"
    try:
        vk_session = vk_api.VkApi(token=token)
        vk = vk_session.get_api()
        user = vk.users.get()
        print("✓ Токен VK валиден")
        print(f"Пользователь: {user[0]['first_name']} {user[0]['last_name']} (ID: {user[0]['id']})")
        return True
    except Exception as e:
        print(f"✗ Ошибка токена VK: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(test_vk_token())