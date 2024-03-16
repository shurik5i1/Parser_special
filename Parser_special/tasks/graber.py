"""
Основной Парсер который вылавливает и проверяет новые сообшения из канала на сигналы
"""
import re
from colorama import Fore

from telethon import  events

from tasks.channel_reciever import reload_parse_channels
from tasks.filehanlers import get_channel_path, reload_csv_file_info, render_message_from_template
from tasks.functions import check_message_is_full, resend_edit_message, send_message_to_chennal
from utility.client import Client, get_chat_id, bot
from utility.common_settings import Utility


class Parser:
    handled_messages_list = []



async def check_message_in_news(channel_file_path, message):
    Info_list = reload_csv_file_info(f"{channel_file_path}/info.csv")

    try:
        Info_list.update({"keys": Info_list["keys"].split("/")})
    except:
        pass
    # print('INfo file data list -->', Info_list)
    message_row_list = message.split("\n")
    for message_row in message_row_list:
        for key in Info_list["keys"]:
            if key.lower() in message_row.lower():
                message_constructor = f"ID: {Info_list['id']}\n Channel name: {Info_list['channel_name']}\n Message: {message}"
                await bot.send_message(await get_chat_id(), message_constructor)
    return


def signal_type_identifier(signal_list:dict, channel_file_path):
    print('FOUND SIGNALS -->', signal_list)
    num_symbol = Utility.Signal_numer_symbol
    signal_types_changer = reload_csv_file_info(Utility.Global_files_list['out_message']['signal_all']['file_path'], is_list=True)

    for signal_name, signal_value in signal_list.items():
        try:
            signal_type_list =  reload_csv_file_info(f'{channel_file_path}/{signal_name}.csv', is_list=True)
            for signal_type in signal_type_list:
                # print('SIGNAL TYPE DATA -->', signal_type['value'])
                if not signal_type['value'] is list:
                    if '/' in signal_type['value']:
                        signal_type['value'] = signal_type['value'].split('/')
                    else:
                        signal_type['value'] = [signal_type['value'],]

                for template in signal_type['value']:
                    signal_value = signal_value.replace('$', '').strip()
                    print('\nTEMPLATES FOR SIGNAL TYPE -->', template)
                    print('CHECKING SENTENCE -->', signal_value)
                    template = template.replace(num_symbol, r'(\d+(\.\d+)?)').strip()
                    pattern = re.compile(template)
                    match = pattern.match(signal_value)
                    if match:
                        found_numbers = match.groups()[::2]


                        print('FOUND NUMBERS -->', found_numbers)
                        print('signal_types_changer -->', signal_types_changer)

                        for signal_type_data in signal_types_changer:
                            print('example -->',signal_type_data['signal'], signal_name,' || ', signal_type_data['type'].lower(), signal_type['type'].lower())
                            if signal_type_data['signal'].lower()==signal_name.lower() and signal_type_data['type'].lower()==signal_type['type'].lower():
                                print('CHANGER VALUE -->',signal_type_data['result'])
                                change_data_list:list = signal_type_data['result'].split('/') if '/' in signal_type_data['result'] else [signal_type_data['result'],]
                                for change_data in change_data_list:
                                    if change_data.count(num_symbol)!=len(found_numbers):
                                        continue

                                    for number in found_numbers:
                                        change_data = change_data.replace(num_symbol, number, 1)
                                    change_data = change_data.replace(num_symbol, '')
                                    signal_list.update({signal_name:change_data})
                    print()
        except Exception as err:
            print(f'{signal_name} ERROR -->', err)

    return signal_list


async def check_message_in_signals(
    channel_file_path: str, message: str, message_id: str, channel_id: str
):
    """
    Checks the given message to existance of signals and other
    """

    All_channels_list = reload_csv_file_info(
        Utility.Global_files_list["bdg"]["bdg_former"]["file_path"], is_list=True
    )
    # print('All_channels_list --> ',All_channels_list)

    custom_check_leverage = "leverage"
    custom_check_margin_type = "margin_type"
    custom_check_instrument = "instrument"
    custom_check_tendency = "tendency"

    # print('MESSAGE TEXT rows--->', message.split('\n'), '\n\n')
    Def_signals_list = reload_csv_file_info(
        Utility.Global_files_list["bdg"]["bdg_def"]["file_path"]
    )
    Local_def_signals_list = reload_csv_file_info(f"{channel_file_path}/bd_def.csv")
    Signals_list = reload_csv_file_info(f"{channel_file_path}/info.csv")
    Def_search_signals_list = dict(
        [
            (key, Signals_list[key])
            for key in Signals_list.keys()
            if key.startswith("def")
        ]
    )
    Signals_list = {
        key: value
        for key, value in Signals_list.items()
        if not key in Def_search_signals_list.keys()
    }

    not_parse_signal_name_list = Utility.Not_parse_signals_list
    not_parse_signals = {}
    for not_parse_signal in not_parse_signal_name_list:
        if not_parse_signal in Signals_list and Signals_list[not_parse_signal] != "":
            not_parse_signals.update({not_parse_signal: Signals_list[not_parse_signal]})

    Signals_list.update(
        {custom_check_tendency: Signals_list[custom_check_tendency].split("/")}
    )
    # print('SIGNALS LIST -->',Signals_list)
    # print('DEF LIST -->',Def_signals_list)

    must_have_signals_list = list(Utility.Must_have_signals_list)

    signals_names_list = list(Signals_list)
    not_found_signals = signals_names_list[:]
    found_signals_values = {}
    custom_found_signals = []

    message_row_list = message.split("\n")

    def has_number(text):
        pattern = r"\d"
        return bool(re.search(pattern, text))

    def add_signal(signal: dict, is_multiple=False):
        for adding_signal in signal.keys():
            if signal[adding_signal] in ["", " ", None]:
                print("SIGNAL IS EMPTY")
                return "Signal is empty"

            found_signal = found_signals_values.get(adding_signal)

            if found_signal is None or (
                not found_signal is None
                and is_multiple
                and not adding_signal == custom_check_tendency
            ):
                if adding_signal == custom_check_instrument:
                    signal_value = signal[custom_check_instrument].upper()
                    letter_only_signal = re.sub("[^a-zA-Zа-яА-Я]", "", signal_value)
                    letter_only_signal = (
                        letter_only_signal.replace("USDT", "") + "/USDT"
                    )
                    signal.update({adding_signal: letter_only_signal})
                elif adding_signal == custom_check_leverage:
                    signal.update(
                        {
                            custom_check_leverage: signal[custom_check_leverage]
                            .lower()
                            .replace("x", "")
                            .replace("х", "")
                        }
                    )
                print(
                    Fore.BLUE + "\nAdding Signal -->",
                    adding_signal,
                    "|| ADDING DATA -->",
                    signal,
                )
                if is_multiple:
                    print("\nMULTIPLE SIGNAL !!!!", signal)
                    try:
                        signal_name, signal_value = list(signal.items())[0]
                        exist_value = found_signals_values[signal_name]
                        found_signals_values.update(
                            {signal_name: exist_value + " " + signal_value}
                        )
                    except Exception as err:
                        print(" ERROR IN MULTIPLE SIGNAL -->", err)
                        found_signals_values.update(signal)
                else:
                    found_signals_values.update(signal)
                try:
                    not_found_signals.remove(adding_signal)
                except:
                    pass
                # print(Fore.GREEN,'NF LIST -->',Local_def_signals_list,Fore.WHITE)

                print(Fore.WHITE)

    def custom_message_check(message_row, message_row_id):
        message_row_splitted = message_row.split()

        for message_row_split_id, message_row_split in enumerate(message_row_splitted):
            # print('MIGHT BE THE INSTRUMENT -->', message_row_split)
            tendency_list = [
                tendencies.upper() for tendencies in Signals_list[custom_check_tendency]
            ] + [tendency.upper() for tendency in Utility.Common_tendency_signal_types]
            letter_only_signal = re.sub("[^a-zA-Zа-яА-Я]", "", message_row_split)
            russian_words = Utility.Russian_words_replacement

            if "usdt" in letter_only_signal.lower():
                found_instrument = found_signals_values.get(custom_check_instrument)
                if found_instrument in ["", " ", None]:
                    add_signal(
                        {
                            custom_check_instrument: letter_only_signal.lower()
                            .replace("usdt", "")
                            .upper()
                            + "/USDT"
                        }
                    )
                    custom_found_signals.append(custom_check_instrument)

            elif (
                message_row_split.isupper()
                and not letter_only_signal.upper() in tendency_list
            ):
                is_russian = False
                for letter in letter_only_signal.lower():
                    if letter in russian_words:
                        is_russian = True

                if not is_russian:
                    found_instrument = found_signals_values.get(custom_check_instrument)
                    if found_instrument in ["", " ", None]:
                        add_signal(
                            {
                                custom_check_instrument: letter_only_signal
                                + ("/USDT" if not "USDT" in letter_only_signal else "")
                            }
                        )

                        custom_found_signals.append(custom_check_instrument)

            elif letter_only_signal.upper() in tendency_list:
                add_signal({custom_check_tendency: letter_only_signal})
                custom_found_signals.append(custom_check_tendency)

            if (
                "x" in message_row_split or "х" in message_row_split
            ) and message_row_split.replace("x", "").replace("-", "").isnumeric():
                for symbol in [" ", "x", "х", "-", "="]:
                    message_row_split.replace(symbol, "")
                if has_number(message_row_split):
                    found_leverage = found_signals_values.get(custom_check_leverage)
                    # print('LEVERAGE EXAMPLE', message_row_split)
                    if found_leverage in ["", " ", None]:
                        add_signal(
                            {
                                custom_check_leverage: message_row_split.replace(
                                    "x", ""
                                ).replace("х", "")
                            }
                        )
                        custom_found_signals.append(custom_check_leverage)

        # print('\n Custom Check Found Signals -->', found_signals_values)

    def get_def_signals():
        found_signals = {}
        # print(Fore.GREEN+'NOT FOUND SIGNALS DEF CHECK -->', not_found_signals, Fore.WHITE)
        for NF_signal_id, NF_signal in enumerate(not_found_signals[:]):
            # print('\nDEF CHECK SIGNALS -->', NF_signal,'DEF CONDITION -->', Def_search_signals_list[f'def_{NF_signal}'])
            # print(Fore.GREEN+'\nNF SIGNAL -->', NF_signal,'DEF_BOOL -->',Local_def_signals_list,Fore.WHITE)
            if not Def_search_signals_list[f"def_{NF_signal}"] in ["", " ", None]:
                # print(Fore.GREEN+'\nNF SIGNAL -->',NF_signal)

                if NF_signal in Local_def_signals_list:
                    def_value = Local_def_signals_list[NF_signal]
                    # print('Local Def value found!!',NF_signal,'==>', def_value)
                    if not def_value is None and not def_value == "":
                        add_signal({NF_signal: def_value})
                        found_signals.update({NF_signal: def_value})
                        continue

                if NF_signal in Def_signals_list:
                    def_value = Def_signals_list[NF_signal]
                    # print('Global Def value found!!', def_value)
                    if not def_value is None and not def_value == "":
                        add_signal({NF_signal: def_value})
                        found_signals.update({NF_signal: def_value})
                        # print(Fore.LIGHTMAGENTA_EX+'NOT FOUND SIGNALS DEF CHECK -->', not_found_signals, Fore.WHITE)

                        # continue

        return found_signals

    next_row_check = None
    for item_signal_name, item_signal_value in Signals_list.items():
        if not type(item_signal_value) is list:
            try:
                item_signal_value_list = item_signal_value.split("/")
                item_signal_value_list = [
                    value for value in item_signal_value_list if not value == ""
                ]
            except Exception:
                print(
                    Fore.RED,
                    "SIGNAL VALUE CONVERTING TO LIST ERROR --->",
                    item_signal_value_list,
                    Fore.WHITE,
                )
        else:
            item_signal_value_list = item_signal_value

        is_signal_found = False
        for item_signal_value in item_signal_value_list:
            for message_row_id, message_row in enumerate(message_row_list[:]):
                # print(Fore.LIGHTYELLOW_EX+'\nSignal -->',item_signal_name.lower(),'    Signal Value -->',item_signal_value, 'Value Check-->', item_signal_value.lower() in message_row.lower(), '   Search Row -->', message_row.lower(), Fore.WHITE)
                if (
                    item_signal_value.lower() in message_row.lower()
                    and not item_signal_value == ""
                ):

                    if item_signal_name.lower() == custom_check_instrument.lower():
                        # print('FOUND INSTRUMENT !! -->', message_row)
                        message_row_splitted = message_row.split(item_signal_value)[1]
                        message_value = message_row_splitted.split()[0]

                        for tendency in Signals_list[custom_check_tendency]:
                            if tendency in message_row_splitted:
                                add_signal({custom_check_tendency: tendency})

                                # not_found_signals.remove(custom_check_tendency)
                        for message_row_split in message_row_splitted.split():
                            message_row_split = message_row_split.replace(
                                "x", ""
                            ).replace("х", "")
                            if (
                                "x" in message_row_split or "х" in message_row_split
                            ) and has_number(message_row_split):
                                print("LEVERAGE CUSTOM FOUND!!!")
                                add_signal({custom_check_leverage: message_row_split})
                                # not_found_signals.remove(custom_check_leverage)

                    elif item_signal_name.lower() == custom_check_leverage.lower():
                        try:
                            margin_value = message_row.split(item_signal_value)[1]
                            print("ELIF MARGIN -->", margin_value)

                            matches = re.findall(r"\((.*?)\)", margin_value)
                        except:
                            matches = None
                            margin_value = ""

                        if matches:
                            scope_content = matches[0]
                            add_signal({custom_check_margin_type: scope_content})

                            message_value = margin_value.replace(
                                f"({scope_content})", ""
                            )
                        else:
                            message_value = margin_value

                    else:
                        try:
                            if (
                                not item_signal_name.lower()
                                == custom_check_tendency.lower()
                            ):
                                message_value = message_row.lower().split(
                                    item_signal_value.lower()
                                )[1]
                                print("MESSAGE VALUE BEFORE SLICE -->", message_value)
                                if not message_value.replace(" ", "") in ["", None]:
                                    message_value_index = message_row.lower().find(
                                        message_value
                                    )
                                    message_value = message_row[message_value_index:]
                            else:
                                message_value = item_signal_value

                        except:
                            message_value = ""
                    # print('SIGNAL NAME --->',signals_names_list[value_id])
                    # print('\n ADD MESSAGE VALUE --X-->', {item_signal_name:message_value})
                    if not message_value.replace(" ", "") in ["", None]:
                        add_signal(
                            {item_signal_name: message_value},
                            is_multiple=len(item_signal_value_list) > 1,
                        )
                        is_signal_found = True
                        continue

                    elif (
                        not has_number(message_value)
                        and item_signal_name in must_have_signals_list
                    ):
                        next_row_check = [item_signal_name, message_row_id]
                        print("GO TO NEXT ROW CHECK -->", next_row_check)

                if not is_signal_found:
                    if (
                        item_signal_name.lower() == custom_check_instrument.lower()
                        or message_row_id in [0, 1]
                    ):
                        custom_message_check(message_row, message_row_id)
                    elif (
                        not next_row_check is None
                        and next_row_check[0] in not_found_signals
                    ):
                        next_row_index = next_row_check[1] + 1
                        letter_only_signal = re.sub(
                            "[^a-zA-Zа-яА-Я]", "", message_row_list[next_row_index]
                        )

                        print("\nNEXT ROW Letters -->", letter_only_signal)
                        while (
                            len(letter_only_signal) < 3
                            or message_row_list[next_row_index].startswith(
                                tuple(map(str, range(1, 10)))
                            )
                        ) and next_row_index < len(message_row_list):
                            print(
                                "\nNEXT ROW CHECK -->", message_row_list[next_row_index]
                            )

                            if message_row_list[next_row_index].replace(" ", "") in [
                                "",
                                None,
                            ]:
                                next_row_index += 1

                            if has_number(message_row_list[next_row_index]):
                                print(
                                    "HAS NUMBER -->",
                                    {
                                        next_row_check[0]: message_row_list[
                                            next_row_index
                                        ]
                                    },
                                    "  Is Multiple -->",
                                    len(item_signal_value_list) > 1,
                                )
                                add_signal(
                                    {
                                        next_row_check[0]: message_row_list[
                                            next_row_index
                                        ]
                                    },
                                    is_multiple=True,
                                )
                            next_row_index += 1
                            letter_only_signal = re.sub(
                                "[^a-zA-Zа-яА-Я]", "", message_row_list[next_row_index]
                            )

                        else:
                            next_row_check = None

                        # not_found_signals.append(signals_names_list[value_id])

    # print('\nCHECK IS MESSAGE IS SIGNAL -->\n',sorted(must_have_signals_list),'\n',sorted(list(set(not_found_signals)-set(not_parse_signal_name_list))), )

    found_must_have_signals = []
    for must_have_signal in must_have_signals_list:
        if (
            not must_have_signal
            in list(set(not_found_signals) - set(not_parse_signal_name_list))+[custom_check_tendency,custom_check_instrument]
            and not must_have_signal in custom_found_signals
        ):
            found_must_have_signals.append(must_have_signal)

    print(Fore.RED +'FOUND MUST HAVE SIGNALS ---->',(found_must_have_signals))
    print(f'BOOOELEAN --->{len(found_must_have_signals) < 2}'+Fore.WHITE)
    if len(found_must_have_signals) < Utility.Min_signal_amount:
        return

    found_signals_values = signal_type_identifier(found_signals_values, channel_file_path)

    check_important_signal_list = []

    def_found_signals = get_def_signals()
    # print('NOT Found Signals -->',not_found_signals,'\n')
    check_important_signal_list += list(def_found_signals.keys())

    not_found_signals = list(
        set(not_found_signals) - set(list(def_found_signals.keys()))
    )

    add_signal(not_parse_signals)

    if len(check_important_signal_list) == len(def_found_signals):
        if check_message_is_full(found_signals_values):
            print("FULL MESSAGE !!")

            message_constructor = await render_message_from_template(
                Utility.Global_files_list["templates"]["templates_message"][
                    "file_path"
                ],
                found_signals_values,
                True,
            )
            message_constructor = (
                message_constructor
                if not type(message_constructor) is tuple
                else list(message_constructor)[0]
            )

            channel = await Client.parse_client.get_entity(int(channel_id))

            Notify_channels = [
                channel["channel_name"]
                for channel in All_channels_list
                if channel["notify"].lower() == "true"
            ]
            # print(Fore.LIGHTRED_EX+'channel_id and notify channel list -->', channel_id,'||', Notify_channels, '\nChannel -->', channel.title, Fore.WHITE)

            if channel.title in Notify_channels:
                sent_message = await bot.send_message(
                    await get_chat_id(),
                    f"{message_constructor}",
                    parse_mode="html",
                    link_preview=False,
                )

            message_send_try = await send_message_to_chennal(
                found_signals_values,
                notify=(channel.title in Notify_channels),
                origin_message=message,
            )


            # message_send_try = await send_message_to_chennal(found_signals_values, origin_message=message)
            if not message_send_try:
                await bot.send_message(
                    await get_chat_id(),
                    f"{message_constructor}",
                    parse_mode="html",
                    link_preview=False,
                )
                await bot.send_message(
                    await get_chat_id(), "Не получилось отправить сообщению в канал!!!"
                )

            return

    message_constructor = await render_message_from_template(
        Utility.Global_files_list["templates"]["templates_message"]["file_path"],
        found_signals_values,
        False,
    )
    message_constructor = (
        message_constructor
        if not type(message_constructor) is tuple
        else list(message_constructor)[0]
    )

    await resend_edit_message(
        origin_message=f"{message_constructor}",
        message_id=message_id,
        is_new=True,
        origin_channel_id=channel_id,
    )






async def command_reload_parse_channels(reload_message=None):
    @Client.parse_client.on(
        events.NewMessage(chats=list(map(int, reload_parse_channels())))
    )
    async def get_channel_update(signal):
        sender = signal.sender
        sender_channel_id = sender.id
        sender_channel_name = sender.title

        All_news_channel_list = [
            channel["channel_name"]
            for channel in reload_csv_file_info(
                Utility.Global_files_list["bdg"]["bdg_news"]["file_path"], is_list=True
            )
        ]

        # print(Fore.LIGHTWHITE_EX+'\nHANDLED MESSAGE -->', signal, '\n'+Fore.WHITE)

        channels_file_path = f"{await get_channel_path(f'{sender_channel_id}')}"
        print("Channel File Path -->", channels_file_path)
        message_info = {
            "message": signal.message.message,
            "channel_id": sender_channel_id,
        }

        if not message_info in Parser.handled_messages_list:
            if not sender_channel_name in All_news_channel_list:
                Parser.handled_messages_list.append(message_info)
                # print('Parser.handled_messages_list -->', Parser.handled_messages_list)
                await check_message_in_signals(
                    channel_file_path=channels_file_path,
                    message=message_info["message"],
                    message_id=signal.message.id,
                    channel_id=signal.chat_id,
                )
                return
            else:
                Parser.handled_messages_list.append(message_info)
                await check_message_in_news(channels_file_path, message_info["message"])
        return

    print("PARSER RELOADED")
    if not reload_message is None:
        await bot.send_message(await get_chat_id(), "Parser has reloaded")
        return
