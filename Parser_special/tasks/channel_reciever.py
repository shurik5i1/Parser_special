"""
Отвечает за сбор каналов того или иного назначения
"""

from tasks.filehanlers import get_channel_path, read_file, reload_csv_file_info

from utility.client import Client ,bot , get_chat_id
from utility.common_settings import Utility


def reload_parse_channels():
    Parse_channels_id_list = []

    def parse_mode_check(reader):
        channel_parse_mod_row_id = 0
        channel_id_row_id = 0
        for row_index, row in enumerate(reader):
            # print('ROW -->', row)
            if (
                row_index != 0
                and not len(row) == 0
                and row[channel_parse_mod_row_id].lower() == "true"
            ):
                # print(row[channel_id_row_id])
                Parse_channels_id_list.append(row[channel_id_row_id])
            else:
                for title_index, title_name in enumerate(row):
                    if title_name.lower() == "id".lower():
                        channel_id_row_id = title_index
                    if title_name.lower() == "Parse_mode".lower():
                        channel_parse_mod_row_id = title_index

    reader = read_file(Utility.Global_files_list["bdg"]["bdg_former"]["file_path"])
    parse_mode_check(reader)
    reader = read_file(Utility.Global_files_list["bdg"]["bdg_news"]["file_path"])
    parse_mode_check(reader)

    # print(f'READER -->{reader}')
    return Parse_channels_id_list


async def reload_not_configured_channels_list():
    All_channels_list = reload_csv_file_info(Utility.Global_files_list['bdg']['bdg_former']['file_path'], is_list=True)

    Info_file_path_list = [f"{await get_channel_path(channel['id'])}/info.csv" for channel in All_channels_list]

    # print('Info_file_path_list -->', Info_file_path_list)
    Info_files = [reload_csv_file_info(path) for path in Info_file_path_list]
    Must_have_signals_list = Utility.Must_have_signals_list

    # print(Fore.LIGHTBLUE_EX,'\nInfo_files -->', Info_files, Fore.WHITE)

    not_configured_channels = []


    for file_index, info_file in enumerate(Info_files):
        main_signal_exist = True
        for must_have_signal in Must_have_signals_list:
            # print(Fore.LIGHTBLUE_EX, '\n info_file_data -->', info_file)
            try:
                if info_file[must_have_signal] in ['', ' ', None]:
                    try:
                        if info_file[f'def_{must_have_signal}'] in ['', ' ', None]:
                            main_signal_exist = False

                    except:
                        main_signal_exist = False
            except Exception:
                if Exception is KeyError:
                    await bot.send_message(await get_chat_id(), f'Error in {Info_file_path_list[file_index]} info file')

        if not main_signal_exist:
            # print('\not_configured_channels DATA -->', info_file)
            not_configured_channels.append(info_file)

    return not_configured_channels




async def channels_list_paginator(
    page, first_time=False, all_channels=False, no_initialized_channels=False
):
    channel_list_message = f'{"Пожалуйста выберите число канала, из которого хотите взять данные:" if first_time else ""}\n\n'
    All_channels_list = reload_csv_file_info(
        Utility.Global_files_list["bdg"]["bdg_former"]["file_path"], is_list=True
    ) + reload_csv_file_info(
        Utility.Global_files_list["bdg"]["bdg_news"]["file_path"], is_list=True
    )

    Not_configured_channels = await reload_not_configured_channels_list()

    if all_channels:
        Pagination_channels_list = All_channels_list

    if no_initialized_channels:
        Pagination_channels_list = Not_configured_channels

    paginator_value = Utility.Paginator_value

    if int(page) > len(Pagination_channels_list) // paginator_value:
        Channel_list_page = Pagination_channels_list[
            paginator_value * (int(page) - 1):
        ]
    else:
        Channel_list_page = Pagination_channels_list[
            paginator_value * (int(page) - 1): paginator_value * int(page)
        ]

    channels_list_buttons = []

    for paginator_index, paginator_channel in enumerate(Channel_list_page):
        not_configured_channels_names = [
            channel["channel_name"] for channel in Not_configured_channels
        ]
        if Pagination_channels_list != Not_configured_channels:
            if paginator_channel["channel_name"] in not_configured_channels_names:
                status_obj = "🟡"
            elif paginator_channel["parse_mode"].lower() == "false":
                status_obj = "🔴"
            else:
                status_obj = "🟢"

            channel_list_message += f"{status_obj}<b>{Pagination_channels_list.index(paginator_channel)+1}. </b>{'🔍' if paginator_channel['notify'].lower() == 'true' else ''} {paginator_channel['channel_name']} \n"
        else:
            channel_list_message += f"<b>{Pagination_channels_list.index(paginator_channel)+1}. </b> {paginator_channel['channel_name']}\n"

    channel_list_message += "\n"

    if (
        int(page) <= len(Pagination_channels_list) // paginator_value
        and len(Pagination_channels_list) / paginator_value > 1
    ):
        if len(Pagination_channels_list) % paginator_value == 0:
            if int(page) == len(Pagination_channels_list) / paginator_value:
                # print('Condition last page')
                channels_list_buttons.append("<- previous")

            else:
                if int(page) == 1:
                    # print('Condition first page')
                    channels_list_buttons.append("next ->")
                else:
                    # print('Condition not last page')
                    channels_list_buttons += ["<- previous", "next ->"]

        else:
            if int(page) == 1:
                channels_list_buttons.append("next ->")
            else:
                channels_list_buttons += ["<- previous", "next ->"]

    elif len(Pagination_channels_list) / paginator_value <= 1:
        # print('LEN IS EQUEL TO ONE')
        channels_list_buttons.clear()
    else:
        channels_list_buttons.append("<- previous")


    # print(Fore.GREEN+'channel_list_message -->', channel_list_message+Fore.WHITE)


    return channel_list_message, channels_list_buttons

