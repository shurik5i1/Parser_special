"""
Сканирует файлы аккаунта на наличие изменений в списке каналов
"""

import asyncio

from telethon import types
from telethon import functions
from telethon import events

from utility.environs import env_reader
from utility.common_settings import Utility
from utility.client import Client, bot
from tasks.functions import (
    channels_info_message_sender,
    get_chat_id,
    reload_csv_file_info,
)
from tasks.filehanlers import file_update_writer


async def check_folders_on_update():
    channel_name_collector = []
    channel_info_collector = []

    channel_check_info_collector = []

    Parse_folders_list = env_reader("Parse_from_folder", is_list=True) + env_reader(
        "News_from_folder", is_list=True
    )

    All_Channels_list = reload_csv_file_info(
        Utility.Global_files_list["bdg"]["bdg_former"]["file_path"], is_list=True
    ) + reload_csv_file_info(
        Utility.Global_files_list["bdg"]["bdg_news"]["file_path"], is_list=True
    )

    if not await Client.parse_client.is_user_authorized():
        return

    folders = await Client.parse_client(functions.messages.GetDialogFiltersRequest())
    # print('FOLDERS IN ACC -->', folders)

    for f in folders:
        chat_folder = str(f).split()

        exist_chat_folders = []

        for chat_obj in chat_folder:
            if "title=" in chat_obj:
                folder_name = (
                    chat_obj.replace("title=", "").replace("'", "").replace(",", "")
                )
                exist_chat_folders.append(folder_name)

        for folder_id, parse_folder in enumerate(Parse_folders_list):
            for check_folder in exist_chat_folders:
                if parse_folder.lower() in check_folder.lower():
                    for obj_id, obj in enumerate(chat_folder):
                        if "InputPeerChannel".lower() in obj.lower():
                            channel_id = int(obj.replace(",", "").split("id=")[1])

                            try:
                                channel_obj = await Client.parse_client.get_entity(
                                    types.PeerChannel(channel_id)
                                )

                                if not channel_obj.title in channel_name_collector:
                                    channel_name_collector.append(channel_obj.title)

                                    channel_check_info_collector.append(
                                        {channel_obj.title: check_folder}
                                    )

                                    channel_main_info = {
                                        "id": channel_id,
                                        "channel_name": channel_obj.title,
                                        "folder": check_folder,
                                    }
                                    channel_info_collector.append(channel_main_info)
                                else:
                                    "IT SEEMS DUBLICATES"
                            except:
                                pass

    All_channels_check_info = [
        {channel_info["channel_name"]: channel_info["folder"]}
        for channel_info in All_Channels_list
    ]

    channel_info_collector_sorted = []

    for sort_channel in channel_info_collector:
        if not (sort_channel in channel_info_collector_sorted):
            channel_info_collector_sorted.append(
                channel_info_collector[channel_info_collector.index(sort_channel)]
            )

    # print('channel_check_info_collector -->',channel_check_info_collector,'\n\n All channels in base -->', All_channels_check_info)
    channels_check_list = [
        (check_channel in All_channels_check_info)
        for check_channel in channel_check_info_collector
    ]

    # print('channels_check_list -->',channels_check_list)
    if not all(channels_check_list) or len(All_channels_check_info) != len(
        channel_check_info_collector
    ):
        await file_update_writer(channels=channel_info_collector_sorted)
        await channels_info_message_sender()

        return True
    return False


@Client.client.on(event=events.userupdate.UserUpdate("me"))
async def check_folder(event):
    # print('Auto check!!')
    try:
        event.status.was_online
        return
    except:
        while event.online:
            try:
                me = await Client.client.get_me()
                online = me.status.was_online
                return
            except:
                pass

            await asyncio.sleep(Utility.Auto_check_time)
            if await check_folders_on_update():
                await asyncio.sleep(Utility.Auto_check_time)
                return

    return


async def reload_check_folders(scanning_command_message=None):
    print("\nCHECK UPDATE IS RUNNING")
    await bot.send_message(await get_chat_id(), "Сканируется")
    await check_folders_on_update()

    await bot.send_message(await get_chat_id(), "Сканирован")
    print("\nSCAN IS END !!")
    return
