"""
Файл отвечаюший за соеденения между клиентом и приложением
"""


from telethon import TelegramClient

from utility.common_settings import Utility
from utility.environs import Api_hash, Api_id, bot_token


async def get_chat_id(message=None):
    permissions = Utility.Permissions
    id = None
    if await permissions['admin_client'].is_user_authorized():
        me = await Client.client.get_me()
        id = me.id
    else:
        try:
            id = message.chat_id
        except: pass
    return id


class Client:
    client = TelegramClient('admin_client', Api_id, Api_hash, system_version="4.16.30-vxCUSTOM")
    parse_client = TelegramClient('parse_client', Api_id, Api_hash, system_version="4.16.30-vxCUSTOM")
    shipper = TelegramClient('shipper', Api_id, Api_hash, system_version="4.16.30-vxCUSTOM")


bot = TelegramClient('bot-session', Api_id, Api_hash).start(bot_token=bot_token)

Utility.Permissions = {'admin_client': Client.client, 'parse_client': Client.parse_client, 'shipper': Client.shipper}

