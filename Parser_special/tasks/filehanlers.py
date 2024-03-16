"""
Функции связанные с открытием и написанием файлов таких как инфо файл или основной файл со списком каналов
"""

import csv
import asyncio
import os
from datetime import datetime
import pathlib
import re
import pytz

from telethon import types, tl, events




from utility.client import bot, Client, get_chat_id
from utility.common_settings import Utility
from colorama import Fore

from utility.environs import env_reader



async def get_channel_by_entity(channel_info):
    try:
        if not channel_info.isnumeric():
            async for dialog in Client.shipper.iter_dialogs():
                if dialog.is_channel:
                    if channel_info.lower() == dialog.entity.title.lower():
                        # print('\nDialogs correnspanded -->', dialog.entity.id)
                        channel_info = dialog.entity.id
                        break
    except:
        if not type(channel_info) is int:
            return False

    channel = await Client.shipper.get_entity(int(channel_info))
    return channel


async def get_channel_path(id):
    All_channels_list = reload_csv_file_info(Utility.Global_files_list['bdg']['bdg_former']['file_path'], is_list=True) + reload_csv_file_info(Utility.Global_files_list['bdg']['bdg_news']['file_path'], is_list=True)
    News_folder_list = env_reader('News_from_folder',is_list=True)

    if len(All_channels_list) == 0:
      await asyncio.sleep(5)

    if not str(id).isdigit():
        return

    path = '/'+str(id)


    if not path.replace(' ','') in ['/','/None',None,'//',]:
        try:
            channel_info_reader = open(f'bdg{path}/info.csv','r')
            reader = csv.reader(channel_info_reader, delimiter =',')
            channel_info_reader.close()



        except:
            print('NEW INFO FILE CREATION')

            if not os.path.exists(f'bdg{path}'):
                os.makedirs(f'bdg{path}')

            with open(f'bdg{path}/info.csv', 'w') as channel_info_file:

                writer = csv.writer(channel_info_file,)
                print('\n', Utility.Signals_template,f'\nBoolean ----> ')
                for channel in All_channels_list:
                    # print('WRITER Channel --->', channel, channel['path'] == path)
                    if channel['id'] == id:

                        channel_obj = await Client.parse_client.get_entity(types.PeerChannel(int(channel['id'])))

                        channel_full_info = await Client.parse_client(tl.functions.channels.GetFullChannelRequest(channel=channel_obj))



                        channel_about = channel_full_info.full_chat.about.split()
                        channel_admins = ''
                        for channel_about_part in channel_about:
                            if '@' in channel_about_part:
                                channel_admins += f'{channel_about_part}/'


                        if channel['folder'] in News_folder_list:
                            writer.writerow(Utility.Global_files_list['bdg']['bdg_news']['template'])
                            writer.writerow([channel['id'],channel['channel_name'],None,channel_admins,50,None])

                        else:
                            print('INFO FILE CREATION OF SIGNAL CHANNEL')
                            writer.writerow(Utility.Signals_template)
                            writer.writerow([channel['id'],channel['channel_name'],None,channel_admins,50,50,50,None,None,None,None,None,None,None,None,None,])
                            writer.writerow([None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,None,])



        try:
            channel_info_reader = open(f'bdg{path}/bd_sig.csv','r')
            reader = csv.reader(channel_info_reader, delimiter =',')
            channel_info_reader.close()

        except:
            print('SIG_BD FILE CREATION')
            with open(f'bdg{path}/bd_sig.csv', 'w') as signal_bd_file:
                writer = csv.writer(signal_bd_file,)
                writer.writerow(Utility.Signals_bd_template)
                signal_bd_file.close()

        try:
            channel_info_reader = open(f'bdg{path}/bd_def.csv','r')
            reader = csv.reader(channel_info_reader, delimiter =',')
            channel_info_reader.close()

        except:
            print(Fore.RED)
            print('BD_DEF FILE CREATION')
            with open(f'bdg{path}/bd_def.csv', 'w') as signal_bd_file:
                writer = csv.writer(signal_bd_file,)
                writer.writerow(Utility.Def_signals_local_template)

                for channel in All_channels_list:
                    if channel['id'] == id:
                         writer.writerow([channel['id'],None,None,None,None,None,None,None,None,None])
                signal_bd_file.close()

            print(Fore.WHITE)

        try:
            signal_types = [signal['signal'] for signal in reload_csv_file_info(Utility.Global_files_list['templates']['signal_tmp']['file_path'], is_list=True)]
            try:
                print('SIGNAL TYPES -->', signal_types)
                for signal_type in signal_types:
                    try:
                        signal_file = open(f'bdg{path}/{signal_type}.csv', 'r')
                    except:
                        with open(f'bdg{path}/{signal_type}.csv', 'w') as signal_file_writer:
                            signal_file_writer = csv.writer(signal_file_writer)
                            signal_file_writer.writerow(Utility.Signal_type_template)
                            for channel in All_channels_list:
                            # print('WRITER Channel --->', channel, channel['path'] == path)
                                if channel['id'] == id:
                                    signal_file_writer.writerow([channel['id'], None, None])

            except Exception as err:print('ERROR IN SIGNAL FILE COMPLICATIONS -->', err)
        except:print('NO SIGNAL TYPE FILE EXIST')
        return f'bdg{path}'
    return





def read_file(file_name):
    try:
        my_file =  open(file_name, 'r')
        reader = csv.reader(my_file, delimiter =',')
    except:
        global_files_list = Utility.Global_files_list

        for global_folder in global_files_list.keys():
            for global_file_name in global_files_list[global_folder].keys():
                if global_file_name in file_name:
                    try:
                        template = global_files_list[global_folder][global_file_name]['template']
                        with open(global_files_list[global_folder][global_file_name]['file_path'], 'w') as global_file:
                             writer = csv.writer(global_file, delimiter =',')
                             writer.writerow(template)


                    except Exception as err:
                        print('Global file write error -->', err)

        my_file =  open(file_name, 'r')
        reader = csv.reader(my_file, delimiter =',')
    return reader



def reload_csv_file_info(file_path, is_list=False):
    info_reader = read_file(file_path)

    if is_list:
        File_info = []
    else:
        File_info = {}

    csv_title_list = []

    for row_index, row in enumerate(info_reader):
        # print('INFO FILE ROW -->', row)
        if row_index == 0:
            # print('FIRST ROW -->', row)
            for title_name in row:
                csv_title_list.append(title_name.strip())
            continue


        signal_data = {}

        for title_value_index, title_value in enumerate(row):
            # print('csv_title_list -->'.upper(), csv_title_list)
            try:
                if not is_list and row_index == 2:
                    column_key = csv_title_list[title_value_index].lower()
                    signal_data[f'def_{column_key}'] = title_value
                else:
                    column_key = csv_title_list[title_value_index].lower()
                    signal_data[column_key] = title_value.strip()
            except:
                pass


        if is_list:
            # File_info_values = [info_data.values() for info_data in File_info]
            if signal_data != {}:
                File_info.append(signal_data)
        else:
            File_info.update(signal_data)

    # print("\nFile_info -->", File_info)

    # if File_info in [{},[]]:
        # print(Fore.BLUE,'\nINfo FILE IS EMPTY -->', file_path, Fore.WHITE)

    return File_info


def update_folder_history(old_channels_list,new_channels_list):
    added_channels = [channel for channel in new_channels_list if not channel in old_channels_list]
    removed_channels = [channel for channel in old_channels_list if not channel in new_channels_list]

    updates_file_path = Utility.Global_files_list['bdg']['bdg_updates']['file_path']

    with open(updates_file_path, 'a') as updates_file:
        update_writer = csv.writer(updates_file,)

        current_datetime_str = datetime.now().astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M")

        for channel in added_channels:
            update_writer.writerow([channel['channel_name'],'ADD',current_datetime_str])

        for channel in removed_channels:
            update_writer.writerow([channel['channel_name'],'REMOVE',current_datetime_str])

    return



async def file_update_writer(channels=None, parse_channels=None, notify_channels=None):
    file_path = Utility.Global_files_list['bdg']['bdg_former']['file_path']
    news_file_path = Utility.Global_files_list['bdg']['bdg_news']['file_path']
    All_channels_list = reload_csv_file_info(file_path,is_list=True) + reload_csv_file_info(news_file_path,is_list=True)
    All_channels_name_list = [channel['channel_name'] for channel in All_channels_list]
    News_folder = env_reader('News_from_folder', is_list=True)

    is_folder_update = False

    try:
        if channels is None:
            channels = All_channels_list
        else:
            is_folder_update = True
    except:pass
    try:
        if parse_channels is None:
            parse_channels = [channel['channel_name'] for channel in All_channels_list if channel['parse_mode'].lower() == 'true']

    except:pass
        # else:
            # print('NEW PARSE CHANNELS LIST -->', parse_channels)
    try:
        if notify_channels is None:
            notify_channels = [channel['channel_name'] for channel in All_channels_list if channel['notify'].lower() == 'true']
        # else:
            # print('NEW NOTIFY CHANNELS LIST -->', notify_channels)
    except:pass


    # print(Fore.LIGHTCYAN_EX + '\nChannels Lists -->', parse_channels,'\n',Notify_channels_list, Fore.WHITE)

    former_file = open(file_path, 'w')
    writer = csv.writer(former_file,)
    writer.writerow(Utility.Global_files_list['bdg']['bdg_former']['template'])

    news_file = open(news_file_path, 'w')
    writer_news = csv.writer(news_file,)
    writer_news.writerow(Utility.Global_files_list['bdg']['bdg_former']['template'])

    Updating_channels = []
    # print('\nNEW CHANNELS -->', channels)
    channels = sorted(channels, key=lambda x: x['id'])
    for parse_channel in channels:
        if not parse_channel['channel_name'] in Updating_channels:
            # print('\nNEWS CHECK --> ', parse_channel['folder'], News_folder)
            if not parse_channel['folder'] in News_folder:
                # print(Fore.CYAN+'ADDING CHANNEL -->', parse_channel['channel_name'],'||  ',parse_channel['channel_name'] in All_channels_name_list, Fore.WHITE)
                Updating_channels.append(parse_channel['channel_name'])
                writer.writerow([
                                parse_channel['id'],
                                parse_channel['channel_name'],
                                (True if parse_channel['channel_name'] in parse_channels else False),
                                parse_channel['folder'],
                                (True if parse_channel['channel_name'] in notify_channels or not parse_channel['channel_name'] in All_channels_name_list else False),
                                ])
            else:
                # print(Fore.CYAN+'ADDING NEWS CHANNEL -->', parse_channel['channel_name'],'||  ',parse_channel['channel_name'] in All_channels_name_list, Fore.WHITE)
                Updating_channels.append(parse_channel['channel_name'])
                writer_news.writerow([
                                parse_channel['id'],
                                parse_channel['channel_name'],
                                (True if parse_channel['channel_name'] in parse_channels else False),
                                parse_channel['folder'],
                                (True if parse_channel['channel_name'] in notify_channels or not parse_channel['channel_name'] in All_channels_name_list else False),
                                ])




    news_file.close()
    former_file.close()

    All_channels_list_updated = reload_csv_file_info(Utility.Global_files_list['bdg']['bdg_former']['file_path'],is_list=True)
    if len(All_channels_list_updated) > 0:
        # print('\nLIST IS NOT EMPTY', f'\nOLD ---> {All_channels_list}', f'\n NEW ONE --> {All_channels_list_updated}')

        await get_channel_path(parse_channel['id'])
        try:
            logo = open(f"bdg/{parse_channel['id']}/logo.jpg")
            logo.close()
        except:
            try:
                await Client.parse_client.download_profile_photo(parse_channel['id'], f"bdg/{parse_channel['id']}/logo.jpg")
            except:
                pass
        try:
            if is_folder_update:
                update_folder_history(All_channels_list, All_channels_list_updated)
        except Exception as err:
            return err
    else:
        print('\nLIST IS EMPTY -->', All_channels_list)
    return


async def get_render_channel_path(id=None):

    if not str(id).isdigit():
        return

    path = '/'+str(id)

    if not path.replace(' ','') in ['/','/None',None,'//',]:

        if not path.startswith('/'):
            path = '/'+path

        try:
            channel_info_reader = open(f'out_message{path}/status.csv','r')
            reader = csv.reader(channel_info_reader, delimiter =',')
            channel_info_reader.close()

        except:
            print('NEW STATUS FILE CREATION')

            if not os.path.exists(f'out_message{path}'):
                os.makedirs(f'out_message{path}')

            with open(f'out_message{path}/status.csv', 'w') as channel_info_file:

                writer = csv.writer(channel_info_file,)
                print('\n',Utility.Channel_status_template,f'\nBoolean ----> ')

                if id is None:
                    id = path.split('_')[-1]
                channel_obj = await get_channel_by_entity(id)

                print('INFO FILE CREATION OF SIGNAL CHANNEL')
                writer.writerow(Utility.Channel_status_template)
                writer.writerow([0,channel_obj.id,channel_obj.title,None,None,None,None,])

            print(Fore.WHITE)
        return f'out_message{path}'
    return




async def get_channel_path_from_file(file_info, folder:str):

        channel_id_row_id = 0
        channel_name = None


        for row_index,row in enumerate(file_info):
            if row_index == 1:
                # for channel in All_channels_list:
                if folder == 'bdg':
                    channel_path = await get_channel_path(row[channel_id_row_id])
                else:
                    channel_path = await get_render_channel_path(id=row[channel_id_row_id])


            elif row_index == 0:
                for title_index, title_name in enumerate(row):
                    if title_name.lower()=='ID'.lower():
                            channel_id_row_id = title_index


            try:
                if folder == 'bdg':
                    # for channel in All_channels_list:
                    #     if row_index == 1 and row[channel_id_row_id] == channel['id']:
                    #         channel_name = channel['channel_name']
                    local_file_data =  reload_csv_file_info(f"{channel_path}/info.csv")

                else:
                    local_file_data =  reload_csv_file_info(f"{channel_path}/status.csv")

                channel_name = local_file_data['channel_name']
            except:
                channel_name = None


        print('\nCHANNEL PATH -->', channel_path)

        return channel_path,channel_name




#   ==========   GLOBAL FILE SENDER  ========


@bot.on(events.NewMessage())
async def file_sender(message_obj):
    message = message_obj.message.message
    # print('\nCHECKING MESSAGE -->', message)

    global_files_list = Utility.Global_files_list

    for folder_name in global_files_list.keys():
        for file_name in global_files_list[folder_name].keys():
            for search_command in global_files_list[folder_name][file_name]['commands']:
                if search_command in message:
                    # print('found file name -->', search_command)
                    try:
                        file_path = global_files_list[folder_name][file_name]['file_path']
                        await bot.send_file(await get_chat_id(), file_path)
                    except:
                        await bot.send_message(await get_chat_id(), 'Файл не найден')
    return



#   ==========   GLOBAL FILE RECEIVER  ========

@bot.on(events.NewMessage())
async def message_file_edit(message_obj):

    if Utility.State in Utility.Local_file_check_states:
        return

    if  message_obj.document is None:
        # print('FILE IS NOT DOCUMENT')
        # print(Fore.WHITE)
        return

    global_files_list = Utility.Global_files_list


    local_file_names = Utility.Local_file_names

    assumed_file_types = Utility.Assumed_file_types

    message = message_obj.file.name
    file_type = message.split('.')[-1]


    if not file_type in assumed_file_types:
        await bot.send_message(await get_chat_id(), 'Не поддержываемый тип файла')
        return



    new_file_name = f"new_file.{file_type}"
    await message_obj.download_media(file=new_file_name)

    message_file = None
    edit_file_path = None
    if file_type == 'csv' or file_type == 'txt':
        try:
            for global_folder_name in global_files_list.keys():
                for global_file_name in global_files_list[global_folder_name].keys():
                    # print(Fore.GREEN+'CHECKING FILE NAME -->', global_file_name, Fore.WHITE)
                    if global_file_name in message.lower():
                        edit_file_path = global_files_list[global_folder_name][global_file_name]['file_path']
                        print('EDITING FILE PATH -->', edit_file_path)
                        message = global_file_name
        except:
            pass
        if edit_file_path is None:
            try:
                print('FILE IS NOT GLOBAL')
                for local_folder_data in local_file_names:
                    try:
                        info_reader = read_file(new_file_name)
                        # print('\nLOCAL FOLDER DATA -->', local_folder_data)
                        for local_folder_name, file_names in local_folder_data.items():
                            # print(' local_folder_name -->', local_folder_name, ' local_file_name -->', file_names)
                            for local_file_name in file_names:
                                if local_file_name in message.lower():
                                    channel_path,channel_name = await get_channel_path_from_file(info_reader, local_folder_name)
                                    if channel_path in ['', ' ', None]:
                                        print('CHANNEL PATH IS NONE')
                                        await bot.send_message(await get_chat_id(), f'File not found')
                                        return
                                    edit_file_path = f"{channel_path}/{local_file_name}.{file_type}"
                                    message_file = f"{local_file_name}.{file_type}"
                                    message = f"{(channel_path.split('/')[-1] if channel_name is None else channel_name)} "
                    except Exception as err:
                        print('ERROR IN FINDING LOCAL FILE --->', err)
            except:
                pass


    if edit_file_path in ['', None]:
        await bot.send_message(await get_chat_id(), f'File not found')

    else:
        # print('NEW FILE -->', new_info_file)
        new_info_file = open(new_file_name, 'r').read()
        old_info_file = open(edit_file_path, 'w')
        old_info_file.write(new_info_file)

        old_info_file.close()
        print('edit_file_path -->', edit_file_path)
        await bot.send_message(await get_chat_id(), f"{message_file} файл канала {message} обновлен" if not message_file is None else f"{message.title()} файл обновлен")


    pathlib.Path.unlink(pathlib.Path(new_file_name))
    print(Fore.WHITE)
    return



async def signal_bd_new_record(signals_list, channel):
    signals_bd_tamplate = [signal.lower() for signal in Utility.Signals_bd_template]

    Found_signals_db_add = []
    for bd_signal in signals_bd_tamplate:
        if not bd_signal in ["catched_time", "sent_channel"]:
            try:
                Found_signals_db_add.append(signals_list[bd_signal])
            except:
                Found_signals_db_add.append("Empty")

    print("\n Channel ID in SIG Recording --->", signals_list["id"])
    sinals_bd_path = f'{await get_channel_path(signals_list["id"])}/bd_sig.csv'

    Found_signals_db_add.insert(
        signals_bd_tamplate.index("catched_time"),
        datetime.now().astimezone(pytz.utc).strftime("%Y-%m-%d %H:%M"),
    )
    Found_signals_db_add.insert(signals_bd_tamplate.index("sent_channel"), channel)
    print("\nUpdating_record_signals -->".upper(), Found_signals_db_add)
    with open(sinals_bd_path, "a") as signals_bd_file:
        signal_bd_writer = csv.writer(signals_bd_file)
        signal_bd_writer.writerow(Found_signals_db_add)
        signals_bd_file.close()



def template_main_data_extractor(splitted_template, symbols_data: dict):
    start_row_id = -1
    end_row_id = -1
    signal_template_symbol = "/template"

    for tmp_row_id, tmp_row in enumerate(splitted_template):
        if signal_template_symbol in tmp_row:
            tmp_row = tmp_row.lower()
            if start_row_id == -1:
                start_row_id = tmp_row_id
            elif end_row_id == -1:
                end_row_id = tmp_row_id

        for symbol_name, symbol_data in symbols_data.items():
            if "=" in tmp_row and symbol_data["var_name"] in tmp_row:
                symbols_data[symbol_name].update({"row_id": tmp_row_id})

    signal_data = splitted_template[start_row_id + 1 : end_row_id]
    signal_data = "\n".join(signal_data)

    return symbols_data, signal_data






async def render_message_from_template(
    template_path, signals_list: dict = None, full_message: bool = None
):
    try:
        template_file = open(template_path, "r").read()
        # print('TEMPLATE FILE -->', template_file)
    except:
        await bot.send_message(
            await get_chat_id(), f"No such file or directory {template_path}"
        )
        return

    tendency_type = None
    splitted_template = template_file.split("\n")

    symbols_data = {
        "long": {"var_name": "long signal sticker", "row_id": None},
        "short": {"var_name": "short signal sticker", "row_id": None},
        "signal_check": {"var_name": "signal check symbol", "row_id": None},
        "nf_signal": {"var_name": "not found signals symbol", "row_id": None},
        "workspace": {"var_name": "workspace symbol between words", "row_id": None},
        "bold": {"var_name": "bold check symbol", "row_id": None},
        "italic": {"var_name": "italic check symbol", "row_id": None},
        "underline": {"var_name": "underline check symbol", "row_id": None},
        "strikethrough": {"var_name": "strikethrough check symbol", "row_id": None},
        "full_message": {"var_name": "full signal message symbol", "row_id": None},
        "missing_message": {
            "var_name": "missing signal message symbol",
            "row_id": None,
        },
    }

    symbols_data, signal_data = template_main_data_extractor(
        splitted_template, symbols_data
    )

    split_data = lambda index: splitted_template[index].split("=")[-1].replace(" ", "")
    str_half = lambda string: [string[: len(string) // 2], string[len(string) // 2 :]]

    try:
        if full_message:
            message_status = split_data(symbols_data["full_message"]["row_id"])
        else:
            message_status = split_data(symbols_data["missing_message"]["row_id"])
        signal_data = message_status + signal_data
    except:
        pass

    if not signals_list is None:
        tendency_long_variants = ["LONG", "ЛОНГ"]
        tendency_symbol = None
        # print('\nsignals_list.upper() in tendency_long_variants -->', signals_list['tendency'].upper() in tendency_long_variants, '\n', signals_list['tendency'])
        try:
            if signals_list["tendency"].upper() in tendency_long_variants:
                tendency_symbol = split_data(symbols_data["long"]["row_id"])
                tendency_type = "long"
            else:
                tendency_type = "short"
                tendency_symbol = split_data(symbols_data["short"]["row_id"])
            signals_list.update(
                {"tendency": tendency_symbol + signals_list["tendency"]}
            )
        except:
            print("NO TENDENCY symbol")
            pass

        # print('\n tendency_symbol --> ', tendency_symbol)

        try:
            workspace_list = reload_csv_file_info(
                Utility.Global_files_list["bdg"]["bdg_links"]["file_path"], is_list=True
            )
            workspace_list = [
                put_link_on_workspace(worspace["workspace"])
                for worspace in workspace_list
            ]
            space_symbol = split_data(symbols_data["workspace"]["row_id"])
            signals_list.update({"workspace": f" {space_symbol} ".join(workspace_list)})
        except:
            print("NO WORKSPACE")
            pass
        # print(Fore.MAGENTA+'SIGNALS LIST -->', signals_list)
        # print(Fore.WHITE)

        checking_symbol = split_data(symbols_data["signal_check"]["row_id"])
        checking_symbol = str_half(checking_symbol)
        # print('\nCHECKING SYMBOL -->', checking_symbol)

        for signal_name in list(signals_list.keys()):
            signal_data = signal_data.replace(
                checking_symbol[0] + signal_name + checking_symbol[-1],
                signals_list[signal_name].strip(),
            )

        try:
            try:
                not_found_symbol = split_data(symbols_data["nf_signal"]["row_id"])
            except:
                not_found_symbol = ""

            not_found_signal = re.findall(
                rf"{checking_symbol[0]}(.*?){checking_symbol[-1]}", signal_data
            )
            for signal_name in not_found_signal:
                signal_data = signal_data.replace(
                    checking_symbol[0] + signal_name + checking_symbol[-1],
                    not_found_symbol,
                )
        except:
            print("NO SIGNAL REPLACEMENT")
            pass

    html_tags = [
        {split_data(symbols_data["bold"]["row_id"]): "<b></b>"},
        {split_data(symbols_data["italic"]["row_id"]): "<i></i>"},
        {split_data(symbols_data["underline"]["row_id"]): "<u></u>"},
        {split_data(symbols_data["strikethrough"]["row_id"]): "<s></s>"},
    ]

    for tag in html_tags:
        tag_search = list(tag.keys())[0]
        tag_value = list(tag.values())[-1]

        search_obj = f"{str_half(tag_search)[0]}(.*?){str_half(tag_search)[-1]}"
        tag_content_list = re.findall(rf"{search_obj}", signal_data)

        for replacement_cnt in tag_content_list:
            replacement_obj = (
                str_half(tag_value)[0] + replacement_cnt + str_half(tag_value)[-1]
            )
            # print(Fore.LIGHTRED_EX,replacement_obj)

            signal_data = signal_data.replace(
                f"{str_half(tag_search)[0]}{replacement_cnt}{str_half(tag_search)[-1]}",
                replacement_obj,
            )

    # print('\nSending variant SIGNAL TEMPLATE -->', signal_data)

    # print('\n Image path -->', signal_image_path)
    return (signal_data, tendency_type) if not tendency_type is None else signal_data



def put_link_on_workspace(worspace_signal, def_workspace_signal=None):
    workspace_and_link = reload_csv_file_info(
        Utility.Global_files_list["bdg"]["bdg_links"]["file_path"], is_list=True
    )
    # print('\nWorkspace ---> ', workspace_and_link)
    linked_message = ""
    for workspace_obj in workspace_and_link:
        if workspace_obj["workspace"].lower() in worspace_signal.lower():
            linked_message = (
                f'<a href="{workspace_obj["link"]}">{workspace_obj["workspace"]}</a>'
            )
        # elif not def_workspace_signal is None:
        #     if workspace_obj["workspace"].lower() == def_workspace_signal.lower():
        #         linked_message = f'<a href="{workspace_obj["link"]}">{def_workspace_signal}</a>'

    return linked_message
