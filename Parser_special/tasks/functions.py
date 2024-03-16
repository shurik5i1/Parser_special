"""
Вспомогательные функции
"""

from datetime import datetime, timedelta
import time
from colorama import Fore
from telethon import types, Button
from telethon.tl.types import (
                               ReplyKeyboardMarkup,
                               KeyboardButtonRow,
                               KeyboardButton,
                               )


import pytz
from tasks.channel_reciever import reload_not_configured_channels_list
from tasks.filehanlers import get_channel_path, get_render_channel_path, put_link_on_workspace, reload_csv_file_info, render_message_from_template, signal_bd_new_record
from utility.client import bot, Client, get_chat_id
from utility.common_settings import Utility
from utility.environs import env_reader









def replace_russian_letters(text):
    replacements = Utility.Russian_words_replacement


    result = ''
    for char in text:
        if char.lower() in replacements:
            replacement = replacements[char.lower()]
            if char.isupper():
                result += replacement.capitalize()
            else:
                result += replacement[0]

        else:
            result += char

    return result





async def channels_info_message_sender(buttons = None):


    All_channels_list = reload_csv_file_info(Utility.Global_files_list['bdg']['bdg_former']['file_path'], is_list=True) + reload_csv_file_info(Utility.Global_files_list['bdg']['bdg_news']['file_path'], is_list=True)

    Parse_channels_counter_list = [channel for channel in All_channels_list if channel["parse_mode"].lower()=='true']
    Values_list = [channel_info_value.title()
                   for channel in All_channels_list
                   for channel_info_value in channel.values()]

    Parsing_folders_list = list(set([channel['folder'].lower().title() for channel in All_channels_list]))

    Not_configured_channels = await reload_not_configured_channels_list()


    if len(Parsing_folders_list) != 0:
        client_channels_amount = Utility.Full_channels_amount

        first_part_time = time.time()

        def half_symbols_to_space(check_name):
            half_space_symbols = ['1','i','r','t','f','j','l','I']
            half_space_counter = 0
            for symobol in str(check_name):
                if symobol in half_space_symbols:
                    half_space_counter += 1
            return half_space_counter

        Folder_info = ''
        max_lenght = max([len(folder_name)*2-half_symbols_to_space(folder_name) for folder_name in Parsing_folders_list])
        # max_numbers_lenght = max([len(folder_name.replace(re.sub('[^a-zA-Zа-яА-Я]', '', folder_name),'').replace(' ', ''))*2 for folder_name in Parsing_folders_list])



        for folder_id,folder_name in enumerate(sorted(Parsing_folders_list)):
            folder_value_amount = (Values_list).count(folder_name)

            Active_channels_amount = len([active_channel for active_channel in Parse_channels_counter_list if active_channel['folder'].lower() == folder_name.lower()])
            Not_configured_channels_amount = len([channel
                                    for not_configured_channel in Not_configured_channels
                                    for channel in All_channels_list if channel['folder'].lower() == folder_name.lower() and not_configured_channel['id']==channel['id']
                                    ])
            Not_active_channels_amount = folder_value_amount-Active_channels_amount-Not_configured_channels_amount


            Folder_info += f"{folder_name}:  "

            space_amount = max_lenght-(len(folder_name)*2-half_symbols_to_space(folder_name))


            Folder_info += (' '*space_amount if space_amount > 0 else '') + f"🟢  -  {Active_channels_amount} " + ' '*(len(str(Active_channels_amount)) + (str(Active_channels_amount).count('1')//2))

            Folder_info += f"    🔴  -  {Not_active_channels_amount if Not_active_channels_amount > 0 else 0} "+' '*(len(str(Not_active_channels_amount)) + (str(Not_active_channels_amount).count('1')//2))
            Folder_info += f"    🟡  -  {Not_configured_channels_amount}\n"



        # update_handler = len(old_list if not (old_list is None) else All_channels_list)-len(All_channels_list)
    else:
        await bot.send_message(await get_chat_id(),"База Пуст")
        return

    updates_history = reload_csv_file_info(Utility.Global_files_list['bdg']['bdg_updates']['file_path'],is_list=True)


    current_datetime_str = datetime.now().astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M")
    current_datetime = datetime.strptime(current_datetime_str, "%Y-%m-%d %H:%M")

    add_signal_datetime_list = [datetime.strptime(signal_memory['update_time'], '%Y-%m-%d %H:%M') for signal_memory in updates_history if signal_memory['status'].upper() == 'ADD']
    remove_signal_datetime_list = [datetime.strptime(signal_memory['update_time'], '%Y-%m-%d %H:%M') for signal_memory in updates_history if signal_memory['status'].upper() == 'REMOVE']

    within_day_added = [date_time for date_time in add_signal_datetime_list if (current_datetime - date_time)  <= timedelta(days=1)]
    within_day_removed = [date_time for date_time in remove_signal_datetime_list if (current_datetime - date_time)  <= timedelta(days=1)]

    # print('\nupdate_handler -->', updates_history)



    await bot.send_message(await get_chat_id(),

    f"""
        всего папок <b>{len(Parsing_folders_list)}</b>, в папках <b>{len(All_channels_list)}</b> каналов из <b>{client_channels_amount}</b> имеющихся

{Folder_info}
За последние сутки:
{len(within_day_added)}   - добавлено\n{len(within_day_removed)}   - удалено\n""", parse_mode='html', buttons=buttons)

    return



def keyboard_buttons_constructor(items_list,back_state=None):

    # print('CONSTRUCTOR ITEM LIST', items_list)
    button_row_constructor = []
    keyboard_buttons = []

    for button_item in items_list:
        keyboard_button = KeyboardButton(button_item)
        button_row_constructor.append(keyboard_button)


    for i in range(0, len(button_row_constructor), 2):
        group = KeyboardButtonRow(button_row_constructor[i:i+2])
        keyboard_buttons.append(group)


    if not back_state is None:
        keyboard_buttons.append(KeyboardButtonRow([KeyboardButton(f'<<< назад в {back_state}')]))



    keyboard_buttons = ReplyKeyboardMarkup(
        rows=keyboard_buttons,
        resize=True
    )

    return keyboard_buttons



def check_message_is_full(check_signals: dict):
    Signal_names_list = [signal.lower() for signal in Utility.Signals_template]
    Not_check_signals = [signal.lower() for signal in Utility.Not_parse_signals_list]
    Not_check_signals += ["signals", "margin_type", "workspace"]

    Signals_list = list(set(Signal_names_list) - set(Not_check_signals))

    Check_signals_list = [
        check_signal
        for check_signal, check_signal_value in check_signals.items()
        if not check_signal_value in ["", " ", None]
    ]
    print("\n Signals_list -->", Signals_list)

    for signal in Signals_list:
        if not signal.lower() in Check_signals_list:
            print("NOT FOUND IN CHECK SIGNAL  -->", signal)
            return False
    return True



async def send_message_to_chennal(signals_list, notify=False, origin_message=None):
    channel_order = Utility.Channel_signal_send_order
    try:
        signal_channels = env_reader("Signal_channel", is_list=True)

        if len(signal_channels) == 0:
            await bot.send_message(
                await get_chat_id(),
                f"Не получилось отправить сообшению, количество каналов {len(signal_channels)}",
            )
            return False

        async def search_for_channel(test_mode, order=None):
            send_channels_list = []

            for channel_index, channel_path in enumerate(signal_channels[:]):
                try:
                    channel_path = await get_render_channel_path(channel_path)
                    render_channel_data = reload_csv_file_info(
                        f"{channel_path}/status.csv"
                    )
                    print(
                        Fore.GREEN,
                        test_mode,
                        "\t",
                        "SEARCH RENDER CHANNEL DATA --->",
                        render_channel_data,
                        signal_channels,
                        Fore.WHITE,
                    )
                    render_channel_data.update({"channel_path": channel_path})

                    print(
                        "ORDER --->", order, "RENDER CHANNEL INDEX -->", channel_index
                    )
                    if test_mode:
                        if (
                            str(notify).lower()
                            == render_channel_data["test_mode"].lower()
                        ):
                            send_channels_list.append(render_channel_data)
                    elif (
                        not order is None
                        and int(order) == channel_index
                        and str(not notify).lower()
                        != render_channel_data["test_mode"].lower()
                    ):
                        print("ORDER TRUE", render_channel_data)
                        send_channels_list.append(render_channel_data)

                except:
                    pass
            return send_channels_list

        attempt = 0
        while attempt < len(signal_channels) * 2:
            send_channels_list = await search_for_channel(
                notify, Utility.Channel_signal_send_order
            )

            print("send_channels_list".upper(), send_channels_list)
            if send_channels_list:
                for channel_status_data in send_channels_list:
                    try:
                        channel_id = channel_status_data["id"]
                        message_send_channel = await Client.shipper.get_entity(
                            types.PeerChannel(int(channel_id))
                        )
                        print("\nMESSAGE SENDING CHANNEL -->", message_send_channel)

                        try:
                            # sending_message, sending_image = await render_message_from_template(Utility.Global_files_list['templates']['templates_signal']['file_path'],signals_list)
                            (
                                sending_message,
                                tendency_type,
                            ) = await render_message_from_template(
                                f"{channel_status_data['channel_path']}/signal.txt",
                                signals_list,
                            )
                        except:
                            try:
                                (
                                    sending_message,
                                    tendency_type,
                                ) = await render_message_from_template(
                                    Utility.Global_files_list["templates"][
                                        "templates_signal"
                                    ]["file_path"],
                                    signals_list,
                                )
                            except:
                                print(Fore.RED + "MESSAGE IS NONE")
                                return False
                        try:
                            if (
                                channel_status_data["origin_message_send"].lower()
                                == "true"
                            ):
                                channel_sent_message = (
                                    await Client.shipper.send_message(
                                        message_send_channel,
                                        origin_message,
                                        parse_mode="html",
                                        link_preview=False,
                                    )
                                )

                            if channel_status_data["photo_send"].lower() == "true":
                                print(
                                    Fore.LIGHTMAGENTA_EX,
                                    "PHOTO SENDING -->",
                                    Fore.WHITE,
                                )
                                try:
                                    channel_sent_message = await Client.shipper.send_file(
                                        message_send_channel,
                                        file=f"{channel_status_data['channel_path']}/{tendency_type}_signal.jpg",
                                        caption=sending_message,
                                        parse_mode="html",
                                        link_preview=False,
                                    )
                                except Exception as err:
                                    print(
                                        Fore.LIGHTMAGENTA_EX,
                                        "PHOTO SENDING ERROR -->",
                                        err,
                                    )
                                    # channel_sent_message = await Client.shipper.send_message(message_send_channel,sending_message, parse_mode='html', link_preview=False)
                                    await bot.send_message(
                                        await get_chat_id(),
                                        f"Не получилось отправить изоброжению\nErr:{err}",
                                    )

                            else:
                                channel_sent_message = (
                                    await Client.shipper.send_message(
                                        message_send_channel,
                                        sending_message,
                                        parse_mode="html",
                                        link_preview=False,
                                    )
                                )

                            try:
                                if (
                                    channel_status_data["comment_send"].lower()
                                    == "true"
                                ):
                                    # await bot.reply(message_send_channel, comment, comment_to=channel_sent_message, parse_mode='html',link_preview=False)

                                    try:
                                        comment = await render_message_from_template(
                                            f"{channel_status_data['channel_path']}/comment.txt",
                                            signals_list,
                                        )
                                        # print('\n COMMENT FOR SIGNAL IN CHANNEL -->',comment)
                                    except:
                                        try:
                                            comment = (
                                                await render_message_from_template(
                                                    Utility.Global_files_list[
                                                        "templates"
                                                    ]["templates_comment"]["file_path"],
                                                    signals_list,
                                                )
                                            )
                                        except:
                                            comment = None

                                    comment = (
                                        comment
                                        if not type(comment) is tuple
                                        else list(comment)[0]
                                    )

                                    if not comment is None:
                                        await Client.shipper.send_message(
                                            message_send_channel,
                                            comment,
                                            comment_to=channel_sent_message,
                                            parse_mode="html",
                                            link_preview=False,
                                        )
                                    else:
                                        await bot.send_message(
                                            await get_chat_id(),
                                            f"Не получилось отправить Комментарии так как он пуст",
                                        )
                            except Exception as err:
                                await bot.send_message(
                                    await get_chat_id(),
                                    f"Не получилось отправить комментарию\nErr:{err}",
                                )

                        except Exception as err:
                            await bot.send_message(
                                await get_chat_id(),
                                f"Не получилось отправить изоброжению или комментарию\nErr:{err}",
                            )

                        # print('SENDING MESSAGE CHENNAL -->', message_send_channel)
                        try:
                            if not signals_list is None:
                                await signal_bd_new_record(
                                    signals_list, message_send_channel.title
                                )
                        except Exception as err:
                            await bot.send_message(
                                await get_chat_id(),
                                f"Не получилось Сохранить в базу сигналов\nErr:{err}",
                            )

                    except Exception as err:
                        print("\n\nCANNOT SEND -->", err)
                        await bot.send_message(
                            await get_chat_id(),
                            f"Не получилось отправить сообшению, количество каналов {len(signal_channels)}\nErr:{err}",
                        )
                        return False
                break
            else:
                attempt += 1
            Utility.Channel_signal_send_order = (
                channel_order + 1
                if not channel_order + 1 >= len(signal_channels)
                else 0
            )
        else:
            return False
        return True
    except Exception as err:
        print("Не получилось отправить сообщению в канал ---> Err:", err)
        return False





async def resend_edit_message(
    origin_message,
    message_id,
    edit_data: dict = None,
    channel_id=None,
    is_send=False,
    is_new=False,
    origin_channel_id=None,
):
    custom_check_margin_type = "margin_type"
    custom_check_workspace = "workspace"
    must_have_signals_list = Utility.Must_have_signals_list

    send_button = Button.inline("Send to channel", f"send_message channel={channel_id}")
    cancel_button = Button.inline("Cancel", b"cancel_message")

    origin_message_row_list = origin_message.split("\n")

    inline_action_buttons_row = [[send_button, cancel_button]]
    # buttons_constructor = []

    not_found_signals = []
    row_constructor = []

    for must_have_signal in must_have_signals_list:
        row_constructor.append(Button.inline(must_have_signal, f"{must_have_signal}"))
        # print('row_constructor -->', row_constructor)

        if len(row_constructor) == 2:
            inline_action_buttons_row.append(row_constructor)
            row_constructor = []
        # print(Fore.LIGHTGREEN_EX+'\ninline_action_buttons_row -->', inline_action_buttons_row, Fore.WHITE)

        is_signal_not_exist = False
        # print('SEARCH SIGNAl -->', must_have_signal)
        for message_row in origin_message_row_list:
            if custom_check_workspace in message_row:
                workspace_name = message_row.split(custom_check_workspace)[1]
                workspace_link = put_link_on_workspace(workspace_name)
                origin_message = origin_message.replace(
                    message_row, f"{custom_check_workspace} : {workspace_link}"
                )

            if must_have_signal.lower() in message_row.lower():
                # print('FOUND -->', must_have_signal)
                is_signal_not_exist = True

        if not is_signal_not_exist:
            not_found_signals.append(must_have_signal)

    edit_button_query_data = f"channel={origin_channel_id} origin_message={message_id}"
    edit_button = Button.inline("Edit", "edit " + edit_button_query_data)
    inline_action_buttons_row.insert(0, [edit_button])

    if not is_new is True:
        await bot.delete_messages(await get_chat_id(), message_ids=message_id)
    else:
        inline_action_buttons_row = inline_action_buttons_row[:2]

    for nf_signal in set(not_found_signals):
        origin_message += f"{nf_signal} :\n"

    signal_message_template = open(
        Utility.Global_files_list["templates"]["templates_message"]["file_path"], "r"
    ).read()
    signal_message_template = signal_message_template.split("\n")

    if not edit_data is None:
        not_found_signal_symbol = "not found signals symbol"
        for template_row in signal_message_template:
            if not_found_signal_symbol in template_row:
                not_found_signal_symbol = (
                    template_row.replace(not_found_signal_symbol, "")
                    .replace(" ", "")
                    .replace("=", "")
                )
        print("Edit OBJECTS -->", edit_data, not_found_signal_symbol)
        # print('Edit_Item -->',list(edit_data.items())[0])
        edit_item_values = list(edit_data.items())[0]
        edit_signal_name = edit_item_values[0]
        edit_signal_value = edit_item_values[1]

        # print('\nORIGINAL MESSAGE -->',origin_message_row_list, '\n')
        for message_row in origin_message_row_list:
            if edit_signal_name.lower() in message_row.lower():
                print("\nNF MESSAGE ROW ---->", message_row)
                # print('\n ORIGIN MESSAGE BEFORE CHANGE -->', origin_message)
                check_symbol = Utility.Message_check_symbol
                print(
                    f"{edit_signal_name}{check_symbol}{not_found_signal_symbol}",
                    "<-- replacing to -->",
                    f"{edit_signal_name}{check_symbol}{edit_signal_value}",
                )
                origin_message = origin_message.replace(
                    f"{edit_signal_name}{check_symbol}{not_found_signal_symbol}",
                    f"{edit_signal_name}{check_symbol}{edit_signal_value}",
                )

    if not is_send:
        new_formed_message = await bot.send_message(
            await get_chat_id(),
            message=origin_message,
            buttons=inline_action_buttons_row,
            parse_mode="html",
            link_preview=False,
        )
        return new_formed_message
    else:
        await bot.send_message(
            await get_chat_id(),
            message=origin_message.replace("Не полная информация", ""),
            parse_mode="html",
            link_preview=False,
        )

