import asyncio
from datetime import datetime, timedelta
import inspect

from colorama import Fore
import pytz
import os

import csv
import pathlib

from telethon import TelegramClient, types, events, Button, tl, utils


from tasks.channel_reciever import channels_list_paginator,  reload_parse_channels
from tasks.graber import Parser, command_reload_parse_channels
from utility.common_settings import Utility
from tasks.filehanlers import (
    file_update_writer,
    get_channel_by_entity,
    put_link_on_workspace,
    read_file,
    reload_csv_file_info,
    get_render_channel_path,
    signal_bd_new_record,
    template_main_data_extractor,
)


from utility.client import Api_hash, Api_id, Client, bot, get_chat_id
from tasks.scan import check_folders_on_update, reload_check_folders
from tasks.functions import (
    replace_russian_letters,
    get_channel_path,
    reload_not_configured_channels_list,
    channels_info_message_sender,
    keyboard_buttons_constructor,
    check_message_is_full,
    resend_edit_message,
    send_message_to_chennal,
)
from utility.environs import env_reader, update_env_file


async def async_start_client(clients: list):
    clients_info = env_reader("User_ids", is_list=True)

    async def no_auth_check(type):
        for client in clients_info:
            if type in client:
                await update_env_file({"User_ids": client}, is_remove=True)

    print(f"CHECKING CLIENTS {clients}....")

    permissions = Utility.Permissions

    active_list = []

    for client in clients:
        if client in permissions.keys():
            await permissions[client].connect()
            if await permissions[client].is_user_authorized():
                await permissions[client].start()
                active_list.append(True)

                print(
                    Fore.LIGHTYELLOW_EX + f"{client} Client started  ^_^  ".upper(),
                    datetime.now(),
                    "=========================================" + Fore.WHITE,
                )

            else:
                await no_auth_check(client)
                active_list.append(False)
                print(f"{client} client doesn't started")

    try:
        await command_reload_parse_channels()
    except Exception as err:
        print("SOMETHING WRONG WITH REGULAR TASKS -->", err)

    print("FUNC RETURN")
    return all(active_list)


async def check_message_is_number(message_obj):
    message = message_obj.message.message.replace(" ", "")
    # print(message.strip('+').is_numeric())
    if Utility.State != 1:
        return False
    if message.strip("+").isnumeric() and len(message.strip("+")) >= 11:
        return True
    return False


async def check_message_is_code(message_obj):
    message = message_obj.message.message.replace(" ", "")

    if Utility.State != 2:
        return False
    if message.isnumeric() and len(message.strip("-")) == 5:
        return True
    return False


async def check_is_message_request(message_obj):
    query_text = message_obj.data.decode("utf-8")
    print("CALLBACKQUERY MESSAGE", query_text)
    query_message_keywords = ["send", "cancel", "edit"]
    must_have_signals = Utility.Must_have_signals_list
    for keyword in query_message_keywords:
        if keyword.lower() in query_text.lower():
            return True
    else:
        if query_text.lower() in must_have_signals:
            return True
        return False


async def check_is_command(message_obj):
    command_message = message_obj.message.message.lower()
    commands_data = Utility.Commands_list
    print("STATE -->", Utility.State)
    for command_data in commands_data:
        for command in command_data["check_commands"]:
            func = command_data["run_func"]

            if command.lower() in command_message:
                # print(Fore.BLUE+'function triggered message -->', command_message,f'\n{globals()[func]}',Fore.WHITE)
                if func in globals():
                    if (
                        command.startswith("/")
                        or len(command_data["states"]) == 0
                        or Utility.State in command_data["states"]
                    ):
                        if command_data["send_message_obj"]:
                            send_obj = message_obj
                        else:
                            send_obj = None

                        print("RUNNING FUNCION OBJ -->", globals()[func])
                        if inspect.iscoroutinefunction(globals()[func]):
                            await globals()[func](send_obj)
                        else:
                            globals()[func](send_obj)

                return
    return


async def check_sign_out_confirm(message_obj):
    if Utility.State != 12:
        return False
    menu_message = message_obj.message.message.lower()
    confirm_phrases = ["yes", "no", "да", "нет"]
    for check_phrase in confirm_phrases:
        if check_phrase in menu_message:
            return True
    return False


async def per_time_task_runner():
    # period = lambda:

    while Utility.Is_stats_update:
        try:
            Utility.Full_channels_amount = len(
                [
                    channel
                    for channel in await Client.parse_client.get_dialogs()
                    if channel.is_channel
                ]
            )
            Utility.Last_added_channels_amount = 0
            Utility.Last_removed_channels_amount = 0
            Parser.handled_messages_list = []

            try:
                print("___SIGNALS BD UPDATE___")
                await update_signals_base()
            except Exception as err:
                print("EXCEPTION --->", err)
                pass

        except Exception as err:
            print("ERROR IN per_time_task_runner -->".upper(), err)
            pass

        # print('PERIOD -->', Utility.Stats_update_time)
        await asyncio.sleep(Utility.Stats_update_time)
    # return


# NON-ACTUAL
def path_maker(channel_id, channel_name):
    Path_title = ""
    channel_name_parts_list = channel_name.split()
    channel_name_parts_list = [
        name_part for name_part in channel_name_parts_list if name_part.isalpha()
    ]

    for name_part_id, channel_name_part in enumerate(channel_name_parts_list):
        letter_collector = []
        for name_letter_id, channel_name_letter in enumerate(channel_name_part):
            if channel_name_letter.isalpha():
                letter_collector.append(name_letter_id)

        if len(letter_collector) != 0:
            Path_title += channel_name_part[min(letter_collector)]

    if len(channel_name_parts_list) <= 2 and not len(channel_name_parts_list) == 0:
        Path_title += channel_name_part[len(channel_name_part) // 2]
        if len(channel_name_parts_list) == 1:
            Path_title += channel_name_part[len(channel_name_part) - 1]

    Path_title = replace_russian_letters(Path_title)

    Path_full = f"{Path_title[:3].upper()}_{channel_id}"

    return Path_full




def get_parsed_signals_from_message(message):
    Signals_data = {}

    splitted_message_template = (
        open(
            Utility.Global_files_list["templates"]["templates_message"]["file_path"],
            "r",
        )
        .read()
        .split("\n")
    )
    check_symbols = {
        "check": {"var_name": "signal check symbol", "row_id": None},
        "devide": {"var_name": "signal devide symbol", "row_id": None},
        "full_message": {"var_name": "full signal message symbol", "row_id": None},
        "missing_message": {
            "var_name": "missing signal message symbol",
            "row_id": None,
        },
        "nf_signal": {"var_name": "not found signals symbol", "row_id": None},
    }

    check_symbols, message_template = template_main_data_extractor(
        splitted_message_template, check_symbols
    )

    symbol_extract = (
        lambda symbol_data: splitted_message_template[symbol_data["row_id"]]
        .replace(symbol_data["var_name"], "")
        .replace("=", "")
        .replace(" ", "")
    )
    check_symbol = symbol_extract(check_symbols["check"])
    devide_symbol = symbol_extract(check_symbols["devide"])
    full_message = symbol_extract(check_symbols["full_message"])
    missing_message = symbol_extract(check_symbols["missing_message"])
    nf_signal = symbol_extract(check_symbols["nf_signal"])

    signals_names_list = [signal.lower() for signal in Utility.Signals_template]
    message_splitted = []
    for message_row in message.message.split("\n"):
        message_row = [
            row.strip()
            for row in message_row.split(devide_symbol)
            if not row in ["", " ", None]
        ]
        message_splitted += message_row

    message_splitted[0] = (
        message_splitted[0].replace(full_message, "").replace(missing_message, "")
    )

    message_template = message_template.split("\n")

    message_template_splitted = []
    for message_row in message_template:
        message_row = [
            row.strip()
            for row in message_row.split(devide_symbol)
            if not row in ["", " ", None]
        ]
        message_template_splitted += message_row

    # print('\nSplitted messages lists :\n', message_template_splitted,'\n',message_splitted)

    for message_row_id, template_message_row in enumerate(message_template_splitted):
        for signal_name in signals_names_list:
            if (
                check_symbol[: len(check_symbol) // 2]
                + signal_name
                + check_symbol[len(check_symbol) // 2 :]
                in template_message_row
            ):
                signal_value = message_splitted[message_row_id].replace(
                    signal_name + Utility.Message_check_symbol, ""
                )
                if not nf_signal in signal_value:
                    Signals_data.update({signal_name: signal_value})

    # print('\nParsed Found Signals -->', Signals_data)
    return Signals_data, {
        "full_message": full_message,
        "missing_message": missing_message,
    }


async def update_signals_base():
    All_channels_list = reload_csv_file_info(
        Utility.Global_files_list["bdg"]["bdg_former"]["file_path"], is_list=True
    ) + reload_csv_file_info(
        Utility.Global_files_list["bdg"]["bdg_news"]["file_path"], is_list=True
    )

    with open(
        Utility.Global_files_list["bdg"]["bdg_sig"]["file_path"], "w"
    ) as signals_bd_writer:
        global_signals_bd = csv.writer(signals_bd_writer)
        global_signals_bd.writerow(
            Utility.Global_files_list["bdg"]["bdg_sig"]["template"]
        )

        reminder_channels = []
        for channel in All_channels_list:
            folder_path = await get_channel_path(channel["id"])
            channel_signal_bd_list = reload_csv_file_info(
                f"{folder_path}/bd_sig.csv", is_list=True
            )

            current_datetime_str = (
                datetime.now().astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M")
            )
            current_datetime = datetime.strptime(current_datetime_str, "%Y-%m-%d %H:%M")

            if not len(channel_signal_bd_list) == 0:
                last_signal_time = None

                last_signal_time = channel_signal_bd_list[-1]["catched_time"]
                last_signal_time = datetime.strptime(last_signal_time, "%Y-%m-%d %H:%M")

                if (current_datetime - last_signal_time).days > Utility.Check_days:
                    reminder_channels.append(
                        {
                            "channel_name": channel["channel_name"],
                            "last_signal": last_signal_time,
                        }
                    )

                signal_datetime_list = [
                    datetime.strptime(signal_memory["catched_time"], "%Y-%m-%d %H:%M")
                    for signal_memory in channel_signal_bd_list
                ]

                within_month = [
                    date_time
                    for date_time in signal_datetime_list
                    if (current_datetime - date_time).days <= current_datetime.day
                ]
                within_week = [
                    date_time
                    for date_time in signal_datetime_list
                    if (current_datetime - date_time).days <= 7
                ]
                within_day = [
                    date_time
                    for date_time in signal_datetime_list
                    if (current_datetime - date_time) <= timedelta(days=1)
                ]

                global_signals_bd.writerow(
                    [
                        channel["id"],
                        channel["channel_name"],
                        len(channel_signal_bd_list),
                        len(within_month),
                        len(within_week),
                        len(within_day),
                        channel_signal_bd_list[-1]["catched_time"]
                        if len(channel_signal_bd_list) > 0
                        else False,
                    ]
                )

            else:
                global_signals_bd.writerow(
                    [channel["id"], channel["channel_name"], 0, 0, 0, 0, False]
                )

        if len(reminder_channels) > 0:
            message_constructor = []
            for channel in reminder_channels:
                message_constructor.append(
                    f"{channel['channel_name']}: {channel['last_signal']}"
                )
            message_constructor = "\n".join(message_constructor)
            await bot.send_message(
                await get_chat_id(),
                f"Каналы у которых давно не было сигналов\n{message_constructor}",
            )
    return


#                                     ==============================================
#                                                  Bot_message_handlers
#                                     ==============================================


# MESSAGE ACTION CHECK ===============
@bot.on(events.NewMessage(func=check_is_command))
class Register:
    code_hash = None


async def bot_start(event, resigning=None):
    permissions = Utility.Permissions
    if not resigning is None:
        permissions[resigning] = TelegramClient(
            resigning, Api_id, Api_hash, system_version="4.16.30-vxCUSTOM"
        )
    else:
        await event.respond("Привет, я парсер бот! ")

    for client in permissions:
        await permissions[client].connect()

    user_id = event.message.peer_id.user_id

    Authorized_users = env_reader("User_ids", is_list=True)

    if (
        not str(user_id) in [user.split(":")[0] for user in Authorized_users]
        or len(Authorized_users) == 0
    ):
        Utility.State = 1

        await event.respond("пожалуйста введите телефонный номер")

        @bot.on(events.NewMessage(func=check_message_is_number))
        async def get_user_number(number_message):
            user_type_list = []
            print("number_message gotten")
            Phone_number = number_message.message.message.replace(" ", "")
            if not "+" in Phone_number:
                Phone_number = Phone_number.rjust(12, "+")

            print(Phone_number)
            Admin = env_reader("Admin_client").strip()
            Parser_user = env_reader("Parse_client").strip()
            Shipper = env_reader("Shipper").strip()
            Users = {
                "admin_client": Admin,
                "parse_client": Parser_user,
                "shipper": Shipper,
            }
            print("\n Access USERS -->", Users)
            Phone_number = Phone_number if "+" in Phone_number else f"+{Phone_number}"

            for user, phone_number in Users.items():
                print("IF CONDITION -->", Phone_number, phone_number)
                if Phone_number == phone_number:
                    user_type_list.append(user)

            if len(user_type_list) == 0:
                await number_message.respond("У вас нет достаточно прав")
                await bot_start(event)
                return

            is_send_code = False
            connection = False

            counter = 0
            type_index = 0
            Utility.State = 2

            print("\nuser_type_list -->".upper(), user_type_list)

            @bot.on(events.NewMessage(func=check_message_is_code))
            async def get_user_code(code_message):
                nonlocal is_send_code
                nonlocal connection
                nonlocal counter

                sign_code = code_message.message.message.strip("-")

                try:
                    print(
                        f"{user_type_list[type_index]} CONNECTION, with {Register.code_hash}".upper()
                    )
                    await permissions[user_type_list[type_index]].sign_in(
                        Phone_number, code=sign_code, phone_code_hash=Register.code_hash
                    )
                except Exception as err:
                    await code_message.respond("Неправильный код ")
                    print("ERROR IN CONNECT -->", err)
                    return

                await update_env_file(
                    {"User_ids": f"{user_id}:{user_type_list[type_index]}"}
                )

                if await async_start_client([user_type_list[type_index]]):
                    await code_message.respond("Вход завершен")
                    connection = True
                    is_send_code = False
                    counter = 0
                else:
                    await event.respond("Вход не завершен")
                return

            while type_index < len(user_type_list):
                if connection:
                    connection = False
                    type_index += 1

                print("TYPE INDEX -->", type_index)
                if not is_send_code:
                    try:
                        print(
                            "SENDING CLIENT -->",
                            permissions[user_type_list[type_index]],
                        )
                        send_code = await permissions[
                            user_type_list[type_index]
                        ].send_code_request(Phone_number)
                        Register.code_hash = send_code.phone_code_hash
                        print("SENT CODE  -->", send_code)
                        is_send_code = True
                        await number_message.respond(
                            f"Подключение как {user_type_list[type_index]}\nВведите код в с знаком пробелом, \nПример:12 345"
                        )
                    except Exception as err:
                        print("\n ERROR IN SENDING CODE -->", err)
                        is_send_code = False

                counter += 1
                if counter == 60:
                    break
                await asyncio.sleep(3)
            else:
                await async_start_client(permissions.keys())

            if connection:
                await per_time_task_runner()
                await give_menu_keyboard()
            return

    else:
        await async_start_client(permissions.keys())
        await give_menu_keyboard()
        await per_time_task_runner()

    return


async def give_menu_keyboard(info_message=None):
    Utility.State = 0

    menu_buttons = [
        "📚 Каналы",
        "⚙️ Настройки",
    ]
    menu_buttons = keyboard_buttons_constructor(menu_buttons)

    await bot.send_message(await get_chat_id(), "Menu:", buttons=menu_buttons)
    return


async def give_settings_keyboard(info_message=None):
    Utility.State = 11

    settings_buttons = [
        "🎛 Утилиты",
        "📝 Изменение папок для парсинга",
        "🛠 Аккаунты",
        "📁 Файлы для изъятия",
    ]

    settings_buttons = keyboard_buttons_constructor(settings_buttons, "меню")
    await bot.send_message(await get_chat_id(), "Настройки", buttons=settings_buttons)
    return


async def give_channels_menu_keyboard(info_message=None):
    # print(Fore.BLACK+'CHANNELS MENU ---->')
    Utility.State = 10
    channels_buttons = [
        "📜 Список каналов",
        "📃 Список не иннициализированных каналов",
        "📁 Основной Файл",
        "🔍 Сканировать папки",
    ]
    channels_buttons = keyboard_buttons_constructor(channels_buttons, "меню")
    await channels_info_message_sender(buttons=channels_buttons)
    return


async def accounts_menu(info_message=None):
    accounts_list = ""

    permissions = Utility.Permissions
    for index, user in enumerate(permissions.keys()):
        try:
            User_info = await permissions[user].get_me()
            accounts_list += f"<b>{index+1}.</b> {user} : {User_info.first_name+' '+(User_info.last_name if not User_info.last_name is None else '')}(+{User_info.phone})\n"
        except:
            pass

    account_action_buttons = [
        "⚖️ Изменить доступ",
        "🗑 Выйти с клиента",
    ]

    await bot.send_message(
        await get_chat_id(),
        f"Аккаунты:\n{accounts_list}",
        buttons=keyboard_buttons_constructor(account_action_buttons, "настройки"),
        parse_mode="html",
    )
    Utility.State = 24
    return


async def utilities_menu(info_message=None):
    parse_action_buttons = [
        "📌 Изменить количество каналов для пагинации",
        "⏳ Изменить время для автоматической проверке папок с каналами",
        "⏳ Изменить время для автоматической проверке обнулении и обновлении исторю сигналов",
    ]
    utility_data = ""
    utility_data += f"Количество каналов: {Utility.Paginator_value}\n"
    utility_data += f"Время для автоматичкской проверки: {Utility.Auto_check_time}s\n"
    await bot.send_message(
        await get_chat_id(),
        f"Утилиты:\n{utility_data}",
        buttons=keyboard_buttons_constructor(parse_action_buttons, "настройки"),
    )
    Utility.State = 18
    return


async def parse_folder_menu(info_message=None):
    parse_action_buttons = [
        "Добавить/Удалить папку для парсинга",
        "Каналы для отправки сигналов",
        "Добавить/Удалить папку для новостей",
    ]
    await bot.send_message(
        await get_chat_id(),
        "Выберите папку",
        buttons=keyboard_buttons_constructor(parse_action_buttons, "настройки"),
    )
    Utility.State = 19
    return


async def update_files_menu(info_message=None):
    parse_action_buttons = ["Файлы связанные с данными каналов", "Шаблонные файлы", "Файлы связанные с отправкой сигналов"]
    await bot.send_message(
        await get_chat_id(),
        "Выберите каталог",
        buttons=keyboard_buttons_constructor(parse_action_buttons, "настройки"),
    )
    Utility.State = 14
    return


async def bdg_files_menu(info_message=None):
    global_files_list = Utility.Global_files_list
    parse_action_buttons = [
        global_files_list[folder_name][file_name]["commands"][0]
        for folder_name in global_files_list.keys()
        if folder_name == "bdg"
        for file_name in global_files_list[folder_name].keys()
    ]
    await bot.send_message(
        await get_chat_id(),
        "Выберите папку",
        buttons=keyboard_buttons_constructor(parse_action_buttons, "файлы для изъятия"),
    )
    return


async def template_files_menu(info_message=None):
    global_files_list = Utility.Global_files_list
    parse_action_buttons = [
        global_files_list[folder_name][file_name]["commands"][0]
        for folder_name in global_files_list.keys()
        if folder_name == "templates"
        for file_name in global_files_list[folder_name].keys()
    ]
    await bot.send_message(
        await get_chat_id(),
        "Выберите папку",
        buttons=keyboard_buttons_constructor(parse_action_buttons, "файлы для изъятия"),
    )
    return


async def out_message_files_menu(info_message=None):
    global_files_list = Utility.Global_files_list
    parse_action_buttons = [
        global_files_list[folder_name][file_name]["commands"][0]
        for folder_name in global_files_list.keys()
        if folder_name == "out_message"
        for file_name in global_files_list[folder_name].keys()
    ]
    await bot.send_message(
        await get_chat_id(),
        "Выберите папку",
        buttons=keyboard_buttons_constructor(parse_action_buttons, "файлы для изъятия"),
    )
    return


class Folder_update:
    update_folder_data = None
    back_button_data = None


async def set_parsing_folder(info_message=None):
    parse_action_buttons = ["➕ Добавить папку", "➖ Удалить папку"]

    message = info_message.message.message
    Folder_update.update_folder_data = "Parse_from_folder"
    Folder_update.back_button_data = "папку для парсинга"

    if "новостей" in message:
        Folder_update.update_folder_data = "News_from_folder"
        Folder_update.back_button_data = "папку для новостей"

    parse_folders_list = env_reader(Folder_update.update_folder_data, is_list=True)
    channels_list_message = "\n"

    for folder_id, parse_folder in enumerate(parse_folders_list):
        channels_list_message += f"{folder_id+1}. {parse_folder}\n"

    await bot.send_message(
        await get_chat_id(),
        "Выберите действие" + channels_list_message,
        buttons=keyboard_buttons_constructor(
            parse_action_buttons, "изменение папок для парсинга"
        ),
    )
    Utility.State = 21

    return


async def add_parsing_folder(info_message=None):
    await bot.send_message(
        await get_chat_id(),
        "Введите названия папки с каналами для парсинга\nПример: Папка1, Папка2",
        buttons=keyboard_buttons_constructor([], Folder_update.back_button_data),
    )
    Utility.State = 3
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 3 else False)))
async def folder_names_get(folder_message):
    message = folder_message.message.message.split(",")
    message = [message.strip() for message in message]
    if (
        "Добавить папку" in folder_message.message.message
        or "назад" in folder_message.message.message
    ):
        return

    await folder_message.respond("Parsing...")
    print("Updating DATA -->", message)

    await update_env_file({Folder_update.update_folder_data: message})

    # time.sleep(3)
    await check_folders_on_update()

    await folder_message.respond("Parsing completed")
    return


async def remove_parsing_folder(info_message=None):
    await bot.send_message(
        await get_chat_id(),
        "Выберите папку для удаления:\n",
        buttons=keyboard_buttons_constructor([], Folder_update.back_button_data),
    )
    Utility.State = 13
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 13 else False)))
async def remove_folder_names_get(folder_message):
    folder_order_number = folder_message.message.message
    print("\nFOLDER ORDER NUMBER -->", folder_order_number)
    parse_folders_list = env_reader(Folder_update.update_folder_data, is_list=True)

    if "Удалить папку" in folder_order_number or "назад" in folder_order_number:
        return

    elif folder_order_number.isnumeric() and int(folder_order_number) <= len(
        parse_folders_list
    ):
        remove_folder = parse_folders_list[int(folder_order_number) - 1]
        await update_env_file(
            {Folder_update.update_folder_data: remove_folder}, is_remove=True
        )
        await bot.send_message(await get_chat_id(), "Папка удалён")

    else:
        await bot.send_message(
            await get_chat_id(), "Папка не найден! Повторите попытку"
        )
    return


async def set_render_channel(info_message=None):
    parse_action_buttons = ["➕ Добавить канал", "➖ Удалить канал"]

    signal_channels_list = env_reader("Signal_channel", is_list=True)
    channels_list_message = ""

    for folder_id, parse_folder in enumerate(signal_channels_list):
        channel_id = parse_folder.split(":")[0].split("_")[-1]
        channel_info = await Client.shipper.get_entity(
            types.PeerChannel(int(channel_id))
        )
        channels_list_message += f"<b>{folder_id+1}.</b> {channel_info.title} ({parse_folder.split(':')[0]})\n"

    await bot.send_message(
        await get_chat_id(),
        "Выберите действие или введите число канала для выбара \n"
        + channels_list_message,
        buttons=keyboard_buttons_constructor(
            parse_action_buttons, "изменение папок для парсинга"
        ),
        parse_mode="html",
    )
    Utility.State = 22
    return


class Status:
    update_channel = None
    update_file_name = None


@bot.on(
    events.NewMessage(
        func=lambda event: (
            True if Utility.State == 22 and event.message.message.isnumeric() else False
        )
    )
)
async def render_channel(channel_index_messgae):
    channel_index = int(channel_index_messgae.message.message) - 1
    signal_channels_list = env_reader("Signal_channel", is_list=True)

    if channel_index >= 0:
        for signal_index, signal_channel in enumerate(signal_channels_list):
            if signal_index == channel_index:
                try:
                    Status.update_channel = signal_channel
                    channel_id = signal_channel.split(":")[0].split("_")[-1]
                    channel_info = await Client.shipper.get_entity(
                        types.PeerChannel(int(channel_id))
                    )

                    channel_status = signal_channel.split(":")[-1]
                    # buttons_list = ['Статус файл с данными','💎 Задать статус']
                    buttons_list = ["📁 Статус файл с данными", " 📝 Изменить данные"]

                    await bot.send_message(
                        await get_chat_id(),
                        f"Каналы : \n{channel_info.title} ({channel_status})",
                        buttons=keyboard_buttons_constructor(
                            buttons_list, "список каналов для отправки сигналов"
                        ),
                    )
                    Utility.State = 28
                    return
                except:
                    pass

    await bot.send_message(await get_chat_id(), f"Канал не найден")
    return


async def add_render_channel(render_channel_message=None):
    await bot.send_message(
        await get_chat_id(),
        "Введите названия канала или каналов для отправки сообшений \nПример: Канал1, Канал2 ",
        buttons=keyboard_buttons_constructor(
            [], "список каналов для отправки сигналов"
        ),
    )
    Utility.State = 16
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 16 else False)))
async def render_channel_update(channel_message):
    message_channels = [
        channel.strip() for channel in channel_message.message.message.split(",")
    ]
    signal_channels = []

    if (
        "➕ Добавить канал" in channel_message.message.message
        or "назад" in channel_message.message.message.lower()
    ):
        return

    for message_channel in message_channels:
        print("message_channel -->", message_channel)
        try:
            Signal_channel = await get_channel_by_entity(message_channel)
        except:
            continue

        signal_channels.append(str(Signal_channel.id))

    if len(signal_channels) == 0:
        await bot.send_message(await get_chat_id(), "Канал не найден")

    else:
        await update_env_file({"Signal_channel": signal_channels})
        for channel in signal_channels:
            await get_render_channel_path(channel)

        await bot.send_message(
            await get_chat_id(),
            f"Канал{'ы' if len(signal_channels) > 1 else ''} добавлен",
        )
    return


async def remove_render_channel(info_message=None):
    await bot.send_message(
        await get_chat_id(),
        "Выберите папку для удаления:",
        buttons=keyboard_buttons_constructor(
            [], "список каналов для отправки сигналов"
        ),
    )
    Utility.State = 17
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 17 else False)))
async def render_channel_names_get(folder_message):
    folder_order_number = folder_message.message.message
    signal_channels_list = env_reader("Signal_channel", is_list=True)
    print("\n CHANNEL ORDER NUMBER")

    if (
        "Удалить канал" in folder_message.message.message
        or "назад" in folder_message.message.message.lower()
    ):
        pass

    elif folder_order_number.isnumeric() and int(folder_order_number) <= len(
        signal_channels_list
    ):
        remove_folder = signal_channels_list[int(folder_order_number) - 1]

        await update_env_file({"Signal_channel": remove_folder}, is_remove=True)
        await bot.send_message(await get_chat_id(), " Канал удалён")

    else:
        await bot.send_message(
            await get_chat_id(), "Канал не найден! Повторите попытку"
        )
    return


@bot.on(
    events.NewMessage(
        func=lambda event: (
            True
            if Utility.State in [28, 30]
            and "изменить данные" in event.message.message.lower()
            or "изменения данных" in event.message.message.lower()
            else False
        )
    )
)
async def set_render_channel_data(status_type=None):
    Utility.State = 29

    render_channel_buttons = [
        file_data["file_command"]
        for file_data in Utility.Local_files_list["out_message"]
    ]

    await bot.send_message(
        await get_chat_id(),
        "Выберите файл для изменения",
        buttons=keyboard_buttons_constructor(
            render_channel_buttons, "список каналов для отправки сигналов"
        ),
    )
    return


@bot.on(
    events.NewMessage(
        func=lambda event: (
            True
            if Utility.State == 29
            and not event.message.message.lower() == "изменить данные"
            else False
        )
    )
)
async def render_channel_data_update(update_file_name):
    file_name = update_file_name.message.message

    channel_file_data = Utility.Local_files_list["out_message"]
    for local_file_data in channel_file_data:
        if file_name == local_file_data["file_command"]:
            send_file = local_file_data["file_name"]
            break
    else:
        return

    try:
        edit_channel_path = await get_render_channel_path(Status.update_channel)
    except Exception as err:
        print("RENDER FILE NOT FOUND IN EDIT --> ERR:", err)
        await bot.send_message(await get_chat_id(), "Channel File Not Found")

    try:
        await bot.send_file(
            await get_chat_id(),
            f"{edit_channel_path}/{send_file}",
            caption="Для изменения файла скиньте его изменённый вариант:",
            buttons=keyboard_buttons_constructor([], "изменения данных канала"),
        )
    except:
        await bot.send_message(
            await get_chat_id(),
            f"Файл не существует \nДля создания файла скиньте его изменённый вариант:\n",
            buttons=keyboard_buttons_constructor([], "изменения данных канала"),
        )
        try:
            await bot.send_file(
                await get_chat_id(),
                Utility.Global_files_list["templates"]["templates_comment"][
                    "file_path"
                ],
                caption="Пример из общего файла",
            )
        except:
            pass

    Utility.State = 30
    Status.update_file_name = send_file
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 30 else False)))
async def render_channel_data_update_file(update_file):
    if update_file.document is None and update_file.media is None:
        return
    print("GATHERED MESSAGE -->", update_file.message.photo)
    print("GATHERED FILE -->", update_file.file.mime_type == "image/png")

    edit_channel_path = await get_render_channel_path(Status.update_channel)
    edit_file_local_name = Status.update_file_name

    print(
        "\nEDITING LOCAL FILE -->",
        edit_file_local_name,
    )
    if (
        not update_file.message.photo is None
        or str(update_file.file.mime_type).split("/")[0] == "image"
    ):
        try:
            await update_file.download_media(
                pathlib.Path(f"{edit_channel_path}/{edit_file_local_name}")
            )
            await bot.send_message(await get_chat_id(), "Файл обновлён")
        except Exception as err:
            await bot.send_message(await get_chat_id(), "Ошибка при обновлении")
            print("ERROR IN UPDATING FILE -->", err)

        await set_render_channel_data()
    else:
        await bot.send_message(await get_chat_id(), "Не принимаемый тип файла")

    return


async def send_render_channel_status_file(status_type):
    print("\n Status.update_channel -->", Status.update_channel)
    update_channel_path = Status.update_channel.split(":")[0]
    try:
        update_channel_path = await get_render_channel_path(update_channel_path)
        await bot.send_file(await get_chat_id(), f"{update_channel_path}/status.csv")
    except Exception as err:
        print("ERROR IN SENDING STATUS FILE -->", err)
        await bot.send_message(await get_chat_id(), "Файл не нашлось")
    return


async def set_paginator_value(info_message=None):
    await bot.send_message(
        await get_chat_id(),
        "Введите количество каналов для показа в листе",
        buttons=keyboard_buttons_constructor([], "утилиты"),
    )
    Utility.State = 4
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 4 else False)))
async def pagination_value_edit(paginator_value):
    # print(paginator_value.message.message.isnumeric())
    if paginator_value.message.message.isnumeric():
        Utility.Paginator_value = int(paginator_value.message.message)
        await bot.send_message(await get_chat_id(), "Сделан!")
    elif (
        paginator_value.message.message == "📌 Изменить количество каналов для пагинации"
        or "назад" in paginator_value.message.message
    ):
        pass
    else:
        await bot.send_message(await get_chat_id(), "Неправильно введено число")
        await set_paginator_value()
    return


async def file_check_time(info_obj=None):
    await bot.send_message(
        await get_chat_id(),
        "Введите время для проверки папок на изменения",
        buttons=keyboard_buttons_constructor([], "утилиты"),
    )
    Utility.State = 6
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 6 else False)))
async def set_check_time(paginator_value):
    print(paginator_value.message.message.isnumeric())
    if paginator_value.message.message.isnumeric():
        Utility.Auto_check_time = int(paginator_value.message.message)
        await bot.send_message(await get_chat_id(), "Время для проверки изменён!")
        await give_settings_keyboard()
    elif (
        paginator_value.message.message
        == "⏳ Изменить время для автоматической проверке папок с каналами"
        or "назад" in paginator_value.message.message
    ):
        pass
    else:
        await bot.send_message(await get_chat_id(), "Неправильно введено число")
    return


async def stats_check_time(info_obj=None):
    await bot.send_message(
        await get_chat_id(),
        "Введите время для проверки папок на изменения",
        buttons=keyboard_buttons_constructor([], "утилиты"),
    )
    Utility.State = 23
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 23 else False)))
async def set_check_time(paginator_value):
    print(paginator_value.message.message.isnumeric())
    if paginator_value.message.message.isnumeric():
        Utility.Stats_update_time = int(paginator_value.message.message)
        await bot.send_message(await get_chat_id(), "Время для проверки изменён!")
        await give_settings_keyboard()
    elif (
        paginator_value.message.message
        == "⏳ Изменить время для автоматической проверке обнулении и обновлении исторю сигналов"
        or "назад" in paginator_value.message.message
    ):
        pass
    else:
        await bot.send_message(await get_chat_id(), "Неправильно введено число")
    return


class Channels_List:

    Current_list = None
    Editing_channel = None
    Edit_channel_message = None
    Paginator_current_page = 0


# @bot.on(events.NewMessage(pattern='📜 Список каналов'))
async def get_channels_list(info_message=None):
    Channels_List.Paginator_current_page = 1

    print("PAGE -->", Channels_List.Paginator_current_page)
    channel_list_message, action_buttons = await channels_list_paginator(
        Channels_List.Paginator_current_page, first_time=True, all_channels=True
        )
    sent_message = await bot.send_message(
        await get_chat_id(),
        channel_list_message,
        buttons=keyboard_buttons_constructor(
        action_buttons, "каналы"
    ),
        parse_mode="html",
    )
    Utility.State = 5

    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 5 else False)))
async def channels_handler(query_data):
    current_page = Channels_List.Paginator_current_page

    current_message_id = query_data.id
    # query_decode_data = query_data.data.decode('utf-8')
    query_data_message = query_data.message.message
    if query_data_message == "📜 Список каналов":
        return

    if "next" in query_data_message:
        print("NEXT PAGE")
        Channels_List.Paginator_current_page = current_page + 1
        await bot.delete_messages(await get_chat_id(), message_ids=current_message_id)

        channel_list_message, action_buttons = await channels_list_paginator(current_page + 1, all_channels=True)
        sent_message = await bot.send_message(
        await get_chat_id(),
        channel_list_message,
        buttons=keyboard_buttons_constructor(
        action_buttons, "каналы"
    ),
        parse_mode="html",
        )

    if "previous" in query_data_message:
        Channels_List.Paginator_current_page = current_page - 1
        print("PREVIOUS PAGE")
        await bot.delete_messages(await get_chat_id(), message_ids=current_message_id)
        channel_list_message, action_buttons = await channels_list_paginator(current_page - 1, all_channels=True)
        sent_message = await bot.send_message(
        await get_chat_id(),
        channel_list_message,
        buttons=keyboard_buttons_constructor(
        action_buttons, "каналы"
    ),
        parse_mode="html",
        )

    if "назад" in query_data_message:
        return

    elif query_data_message.isnumeric():
        try:
            channel_id = int(query_data_message) - 1

            if channel_id < 0:
                await bot.send_message(await get_chat_id(), "Неправиный номер канала")
                return

            print("channel_id -->", channel_id)
            All_channels_list = reload_csv_file_info(
                Utility.Global_files_list["bdg"]["bdg_former"]["file_path"],
                is_list=True,
            ) + reload_csv_file_info(
                Utility.Global_files_list["bdg"]["bdg_news"]["file_path"], is_list=True
            )
            channel = All_channels_list[channel_id]

            channel_action_buttons = keyboard_buttons_constructor(
                [
                    "Файл с информациями",
                    "Файл с канала историей сигналов",
                    "Файл с значениями канала по умолчению",
                    "Файлы с заменителями сигналов",
                    "✅️️ Включить парсинг"
                    if channel["parse_mode"].lower() == "false"
                    else "❌ Выключить парсинг",
                    "✅️️ Включить тестовый режим"
                    if channel["notify"].lower() == "false"
                    else "❌ Выключить тестовый режим",
                ],
                "Список каналов",
            )
            Channels_List.Editing_channel = channel
            Channels_List.Edit_channel_message = query_data
            Channels_List.Current_list = "Список каналов"

            Utility.State = 15
            print("GOTTEN CHANNEL -->", Channels_List.Editing_channel)

            await bot.send_message(
                await get_chat_id(),
                f"Канал ID: {channel['id']}\n       {channel['channel_name']}",
                buttons=channel_action_buttons,
            )

        except:
            await bot.send_message(await get_chat_id(), "Не получилось взять канал")
    return


# @bot.on(events.NewMessage(pattern='📃 список не инициализированных каналов'))
async def get_no_configured_channels_list(info_message=None):
    Channels_List.Paginator_current_page = 1

    print("PAGE -->", Channels_List.Paginator_current_page)


    channel_list_message, action_buttons = await channels_list_paginator(
        Channels_List.Paginator_current_page,
        first_time=True,
        no_initialized_channels=True,
    )
    sent_message = await bot.send_message(await get_chat_id(), channel_list_message, buttons=keyboard_buttons_constructor(action_buttons, "каналы"), parse_mode="html",)

    Utility.State = 7
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 7 else False)))
async def no_initilized_channels_handler(query_data):
    print("PAGE -->", Channels_List.Paginator_current_page)
    current_page = Channels_List.Paginator_current_page
    # sent_message_id = int(sent_message.id)
    current_message_id = query_data.id
    # query_decode_data = query_data.data.decode('utf-8')
    query_data_message = query_data.message.message
    if query_data_message == "📃 список не инициализированных каналов":
        return

    if "next" in query_data_message:
        print("NEXT PAGE")
        Channels_List.Paginator_current_page = current_page + 1
        await bot.delete_messages(await get_chat_id(), message_ids=current_message_id)

        channel_list_message, action_buttons = await channels_list_paginator(current_page + 1, no_initialized_channels=True)
        sent_message = await bot.send_message(await get_chat_id(), channel_list_message, buttons=keyboard_buttons_constructor(action_buttons, "каналы"), parse_mode="html",)
        return

    if "previous" in query_data_message:
        Channels_List.Paginator_current_page = current_page - 1
        print("PREVIOUS PAGE")
        await bot.delete_messages(await get_chat_id(), message_ids=current_message_id)
        channel_list_message, action_buttons = await channels_list_paginator(current_page - 1, no_initialized_channels=True)
        sent_message = await bot.send_message(await get_chat_id(), channel_list_message, buttons=keyboard_buttons_constructor(action_buttons, "каналы"), parse_mode="html",)
        return

    if "назад" in query_data_message:
        return
    elif query_data_message.isnumeric():
        try:
            channel_id = int(query_data_message) - 1
            if channel_id < 0:
                await bot.send_message(await get_chat_id(), "Не получилось взять канал")
                return
            print("not_configured_channel_id -->", channel_id)
            All_channels_list = reload_csv_file_info(
                Utility.Global_files_list["bdg"]["bdg_former"]["file_path"],
                is_list=True,
            ) + reload_csv_file_info(
                Utility.Global_files_list["bdg"]["bdg_news"]["file_path"], is_list=True
            )

            Not_configured_channels_list = await reload_not_configured_channels_list()

            channel_info = Not_configured_channels_list[channel_id]

            for channel in All_channels_list:
                if str(channel_info["id"]) == str(channel["id"]):
                    Channels_List.Editing_channel = channel
                    Channels_List.Edit_channel_message = query_data
                    Utility.State = 15
                    break

            channel_action_buttons = keyboard_buttons_constructor(
                [
                    "Файл с информациями",
                    "Файл с канала историей сигналов",
                    "Файл с значениями канала по умолчанию",
                    "Файлы с заменителями сигналов",
                    "✅️️ Включить парсинг"
                    if channel["parse_mode"].lower() == "false"
                    else "❌ Выключить парсинг",
                    "✅️️Включить тестовый режим"
                    if channel["notify"].lower() == "false"
                    else "❌ Выключить тестовый режим",
                ],
                "Список не инициализированных каналов",
            )
            Channels_List.Current_list = "Список не инициализированных каналов"
            print("GOTTEN CHANNEL -->", Channels_List.Editing_channel)
            await bot.send_message(
                await get_chat_id(),
                f"Канал:\n    {channel['channel_name']}",
                buttons=channel_action_buttons,
            )

        except:
            print(Fore.BLACK)
            await bot.send_message(await get_chat_id(), "Не получилось взять канал")
    return


async def signal_type_list():
    signal_types = list({signal['signal'] for signal in reload_csv_file_info(Utility.Global_files_list['out_message']['signal_all']['file_path'], is_list=True)})
    await bot.send_message(await get_chat_id(), 'Выберите тип сигнала', buttons=keyboard_buttons_constructor(signal_types, 'данные канала'))
    Utility.State = 31
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 31 else False)))
async def signal_type_file_sender(signal_type):

    signal_type_name = signal_type.message.message

    if 'назад' in signal_type_name.lower():
        if Channels_List.Current_list == "Список каналов":
            await channels_handler(Channels_List.Edit_channel_message)
        else:
            await no_initilized_channels_handler(Channels_List.Edit_channel_message)

    channel = Channels_List.Editing_channel
    folder_path = await get_channel_path(channel["id"])

    try:
        await bot.send_file(await get_chat_id(), f'{folder_path}/{signal_type_name}.csv')
    except Exception as err:
        await bot.send_message(await get_chat_id(), f'Не получилось отправить файл -->  {err}')




# Choosen channel info file sender
@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 15 else False)))
async def channel_main_action(channel_action):
    action_message = channel_action.message.message
    channel = Channels_List.Editing_channel
    folder_path = await get_channel_path(channel["id"])

    if "Файл с информациями" in action_message:
        await bot.send_file(await get_chat_id(), file=f"{folder_path}/info.csv")

    if "Файл с значениями канала по умолчанию" in action_message:
        await bot.send_file(await get_chat_id(), file=f"{folder_path}/bd_def.csv")

    if "Файл с канала историей сигналов" in action_message:
        await bot.send_file(await get_chat_id(), file=f"{folder_path}/bd_sig.csv")

    if "Файлы с заменителями сигналов" in action_message:
        await signal_type_list()

    if "Список не инициализированных каналов" in action_message:
        await get_no_configured_channels_list()

    if "Список каналов" in action_message:
        await get_channels_list()

    if (
        len(
            [
                action
                for action in ["выключить", "включить"]
                if action in action_message.lower()
            ]
        )
        > 0
    ):
        Channels_data_list_reload = lambda: reload_csv_file_info(
            Utility.Global_files_list["bdg"]["bdg_former"]["file_path"], is_list=True
        ) + reload_csv_file_info(
            Utility.Global_files_list["bdg"]["bdg_news"]["file_path"], is_list=True
        )
        parse_channels_list_reload = lambda list: [
            channel["channel_name"]
            for channel in list
            if channel["parse_mode"].lower() == "true"
        ]
        notify_channels_list_reload = lambda list: [
            channel["channel_name"]
            for channel in list
            if channel["notify"].lower() == "true"
        ]
        not_configured_channels_list_reload = lambda list: [
            not_configured_channel["channel_name"] for not_configured_channel in list
        ]

        All_channels_list = Channels_data_list_reload()

        Parse_channels_list = parse_channels_list_reload(All_channels_list)
        Notify_channels_list = notify_channels_list_reload(All_channels_list)
        Not_configured_channels = not_configured_channels_list_reload(
            await reload_not_configured_channels_list()
        )
        editing_channel = Channels_List.Editing_channel
        # editing_channel.update({'parse_mode':'True'  else 'False'})

        bot_send_message = ""
        if "парсинг" in action_message:
            Edit_channels_list = Parse_channels_list
        else:
            Edit_channels_list = Notify_channels_list

        print(
            "\nEDIT CHANNEL LIST --->",
            Edit_channels_list,
            f"\n Channel-->",
            editing_channel["channel_name"],
        )
        if editing_channel["channel_name"] in Edit_channels_list:
            Edit_channels_list.remove(editing_channel["channel_name"])
            bot_send_message = "Выключен"

        else:
            if editing_channel["channel_name"] in Not_configured_channels:
                bot_send_message = "Канал не инициализирован"
                list_buttons = None
            else:
                Edit_channels_list.append(editing_channel["channel_name"])
                bot_send_message = "Включен"

        if "парсинг" in action_message:
            print(f"\n{action_message}", "PARSING CHANGE", Edit_channels_list)
            file_update_err = await file_update_writer(
                parse_channels=Edit_channels_list
            )
        else:
            print("Notify CHANGE", Edit_channels_list)
            file_update_err = await file_update_writer(
                notify_channels=Edit_channels_list
            )

        if not file_update_err is None:
            await bot.send_message(
                await get_chat_id(),
                f"Ошибка при записи изменения в папке\nERROR:{file_update_err}",
            )

        All_channels_list = Channels_data_list_reload()

        Parse_channels_list = parse_channels_list_reload(All_channels_list)
        Notify_channels_list = notify_channels_list_reload(All_channels_list)

        list_buttons = [
            "Файл с информациями",
            "Файл с канала историей сигналов",
            "Файл с значениями канала по умолчанию",
            "Файлы с заменителями сигналов",
            "✅️️ Включить парсинг"
            if not editing_channel["channel_name"] in Parse_channels_list
            else "❌ Выключить парсинг",
            "✅️️ Включить тестовый режим"
            if not editing_channel["channel_name"] in Notify_channels_list
            else "❌ Выключить тестовый режим",
        ]

        await bot.send_message(
            await get_chat_id(),
            bot_send_message,
            buttons=keyboard_buttons_constructor(
                list_buttons, Channels_List.Current_list
            ),
        )

    return



class Account:
    account_type = None


async def permissions_menu(info_message=None):
    account_type_data = "Список номеров по которым выдаётся доступ:\n"
    permissions = Utility.Permissions

    for user in permissions.keys():
        # print('User type in env -->', user.capitalize())
        User_phone_number = env_reader(user.capitalize())
        account_type_data += f"{user}: {User_phone_number}\n"

    accounts_buttons = [("изменить " + account) for account in permissions.keys()]
    await bot.send_message(
        await get_chat_id(),
        account_type_data,
        buttons=keyboard_buttons_constructor(accounts_buttons, "аккаунты"),
    )
    Utility.State = 26
    return


@bot.on(
    events.NewMessage(
        func=lambda event: (
            True
            if Utility.State == 26 and not "доступ" in event.message.message
            else False
        )
    )
)
async def permission_change_account(account_message):
    Account.account_type = account_message.message.message.replace("изменить ", "")
    Utility.State = 27
    await bot.send_message(
        await get_chat_id(),
        f"Введите номер для доступа в {Account.account_type}",
        buttons=keyboard_buttons_constructor([], "аккаунты"),
    )
    return


@bot.on(
    events.NewMessage(
        func=lambda event: (
            True
            if Utility.State == 27
            and not "Изменить".lower() in event.message.message.lower()
            and not "назад" in event.message.message
            else False
        )
    )
)
async def permission_change(phone_value_message):
    user_type = Account.account_type.capitalize()
    phone_number = phone_value_message.message.message
    print("Phone number to change -->", phone_number)

    if "+" in phone_number and phone_number.replace("+", "").isnumeric():
        current_phone = env_reader(user_type)
        await update_env_file({user_type: current_phone}, is_remove=True)
        await update_env_file({user_type: phone_number})
        await permissions_menu()
    else:
        await bot.send_message(
            await get_chat_id(),
            f"Неправильный тип номера",
            buttons=keyboard_buttons_constructor([], "аккаунты"),
        )
    return


async def log_out_menu(info_message=None):
    accounts_buttons = Utility.Permissions.keys()
    await bot.send_message(
        await get_chat_id(),
        "Выберите аккаунт для отсоеденения",
        buttons=keyboard_buttons_constructor(accounts_buttons, "аккаунты"),
    )
    Utility.State = 25
    return


@bot.on(
    events.NewMessage(
        func=lambda event: (
            True
            if Utility.State == 25 and not "Выйти" in event.message.message
            else False
        )
    )
)
async def log_out_confirm(account_message):
    Utility.State = 12
    Account.account_type = account_message.message.message

    await account_message.respond(
        "Вы уверены",
        buttons=keyboard_buttons_constructor(["❌ НЕТ", "✅️️️️️️️ Да"], "аккаунты"),
    )
    return


@bot.on(events.NewMessage(func=check_sign_out_confirm))
async def sign_out_confirm(confirm_message):
    permissions = Utility.Permissions

    if confirm_message.message.message == Account.account_type:
        return

    checking_message = confirm_message.message.message

    print(
        "\naccount_type -->", Account.account_type, "\nresponse -->", checking_message
    )
    if "да" in checking_message.lower() or "yes" in checking_message.lower():
        client_chat_id = await get_chat_id()

        await permissions[Account.account_type].log_out()
        if not await permissions[Account.account_type].is_user_authorized():
            await bot.send_message(client_chat_id, "Выход завершён")
            await bot_start(confirm_message, resigning=Account.account_type)
        else:
            await bot.send_message(client_chat_id, "Не удалось отсоединиться")
    else:
        await accounts_menu()
    return


#                                                  ==============================================
#                                                          Channels message handler(PARSER)
#                                                  ==============================================




class Edit:
    edit_signal_name = ""
    message = ""
    message_id = ""
    request_message = ""
    origin_message_data = {}


@bot.on(events.CallbackQuery(func=check_is_message_request))
async def message_action(request_message):
    query_message_text = request_message.data.decode("utf-8")
    must_have_signals = Utility.Must_have_signals_list
    origin_message = await request_message.get_message()
    # def_signals = reload_csv_file_info(Utility.Global_files_list['bdg']['bdg_def']['file_path'])

    if "send" in query_message_text.lower():
        found_signals, status_symbols = get_parsed_signals_from_message(origin_message)

        if check_message_is_full(found_signals):
            try:
                await bot.delete_messages(
                    await get_chat_id(),
                    message_ids=Edit.origin_message_data["message_id"].id,
                )
                await bot.delete_messages(
                    await get_chat_id(),
                    message_ids=Edit.origin_message_data["photo_id"].id,
                )
            except:
                print("NO PHOTO OR MESSAGE TO DELETE")

            resend_message = origin_message.message.replace(
                status_symbols["missing_message"], status_symbols["full_message"]
            )

            for message_row in resend_message.split("\n"):
                if "workspace" in message_row:
                    resend_message = resend_message.replace(
                        message_row, f"workspace : {put_link_on_workspace(message_row)}"
                    )

            await resend_edit_message(resend_message, origin_message.id, is_send=True)
            try:
                await send_message_to_chennal(found_signals)
                # if Edit.origin_message_data['message_id'] == Edit.message_id:
            except Exception as err:
                await bot.send_message(
                    await get_chat_id(),
                    f"Не получилось отправить сообщению в канал\nERR:{err}",
                )
            await give_menu_keyboard()
        else:
            await bot.send_message(await get_chat_id(), "MESSAGE IS NOT FULL!!")

    elif "cancel" in query_message_text.lower():
        print("ORIGINAL MESSAGE'S ID -->", origin_message.id)
        await bot.edit_message(
            await get_chat_id(),
            message=origin_message.id,
            text=str(origin_message.message).replace("⚠️ ", "❌ "),
        )

    elif "edit" in query_message_text.lower():
        query_data_list = query_message_text.replace("edit ", "").split()
        print("QUERY DATA LIST -->", query_data_list)

        channel_id = query_data_list[0].replace("channel=", "")

        if len(query_data_list) > 1:
            origin_message_id = query_data_list[1].replace("origin_message=", "")
        else:
            origin_message_id = None
        # print('\nCHANNEL ID :--->', channel_id)

        def delete_image(image_path):
            try:
                os.remove(image_path)
            except OSError as e:
                print(f"Error occurred while deleting the image file: {e}".upper())

        if not origin_message_id is None and not channel_id in ["", " ", None, "None"]:
            print("\norigin_message_id :--->", origin_message_id)
            # bot.send_message(await get_chat_id(), )

            origin_channel_obj = await Client.parse_client.get_entity(int(channel_id))
            origin_message_from_channel = await Client.parse_client.get_messages(
                origin_channel_obj, ids=int(origin_message_id)
            )
            print("\nORIGIN MESSAGE --->", origin_message_from_channel)
            sent_origin_message_photo = None

            photo = origin_message_from_channel.media
            if photo:
                photo_path = "edit_message_photo.jpg"
                await Client.parse_client.download_media(photo, file=photo_path)
                try:
                    sent_origin_message_photo = await bot.send_file(
                        await get_chat_id(), file=photo_path
                    )
                    delete_image(photo_path)
                except Exception as err:
                    print("\nERROR IN SENDING ORIGIN MESSAGE IMAGE -->", err)
                finally:
                    delete_image(photo_path)

            sent_origin_message = await bot.send_message(
                await get_chat_id(), message=origin_message_from_channel.message
            )
            Edit.origin_message_data.update(
                {
                    "message_id": sent_origin_message,
                    "photo_id": sent_origin_message_photo,
                }
            )

        send_message = await resend_edit_message(
            origin_message.message, channel_id=channel_id, message_id=origin_message.id
        )
        Utility.State = 8

        Edit.message = origin_message.message
        Edit.message_id = send_message.id
        Edit.origin_message_data.update({"bot_message_id": send_message.id})

    elif query_message_text.lower() in must_have_signals:
        print("\nEditing data -->", query_message_text)
        Edit.edit_signal_name = query_message_text

        bot_request_message = await bot.send_message(
            await get_chat_id(), "введите значение для изменения "
        )
        Edit.request_message = bot_request_message.id
        Utility.State = 9
    return


@bot.on(events.NewMessage(func=lambda event: (True if Utility.State == 9 else False)))
async def edit_signal_value_message(edit_value_message):
    signal_value = edit_value_message.message.message

    try:
        await bot.delete_messages(await get_chat_id(), message_ids=Edit.request_message)
        await bot.delete_messages(
            await get_chat_id(), message_ids=edit_value_message.id
        )
    except:
        pass
    print("EDIT OBJS -->", {Edit.edit_signal_name: str(signal_value)})
    editted_message = await resend_edit_message(
        Edit.message,
        edit_data={Edit.edit_signal_name: str(signal_value)},
        message_id=Edit.message_id,
    )

    Edit.message = editted_message.message
    Edit.message_id = editted_message.id

    Utility.State = 8
    return


with bot:

    Client.parse_client.loop.run_until_complete(
        async_start_client(Utility.Permissions.keys())
    )
    bot.run_until_disconnected()
    Client.client.run_until_disconnected()
    Client.parse_client.run_until_disconnected()

