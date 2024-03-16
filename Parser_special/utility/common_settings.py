"""
Файл с основными данными которые могут быть изменены в ходе работы бота
"""


class Utility:

    Auto_check_time = 60  # время в промежутке которого проверяется аккаунт для проверки на обновления
    State = -1  # нынешний статус или ход на котором бот работает
    Paginator_value = 20  # количество каналов для показа в листе каналов

    Local_file_names = [
            {'bdg': ['info', 'bd_def', 'bd_sig', 'instrument', 'tendency', 'entrance_point', 'stop_loss', 'leverage', 'take_profit']},
            {'out_message': ['status']}
        ]

    Local_files_list = {
        'out_message': [
                        {
                            'file_command': 'Шаблон для сигнала',
                            'file_name': 'signal.txt',
                        },
                        {
                            'file_command': 'Комментария к сигналу',
                            'file_name': 'comment.txt',
                        },
                        {
                            'file_command': 'Фото сигналов типа Лонг',
                            'file_name': 'long_signal.jpg',
                        },
                        {
                            'file_command': 'Фото сигналов типа Шорт',
                            'file_name': 'short_signal.jpg',
                        },
                       ]
                        }

    Global_files_list = {
                        'bdg':
                        {
                            'bdg_former': {'commands': ['Основной Файл'],
                                           'file_path': 'bdg/bdg_former.csv',
                                           'template': ('ID', 'Channel_name', 'Parse_Mode', 'Folder', 'Notify')},

                            'bdg_news': {'commands': ['Файл с каналами без проверки на сигнал'],
                                         'file_path': 'bdg/bdg_news.csv',
                                         'template': ('ID', 'Channel_name', 'Channel_link', 'Admin', 'Rate', 'Keys')},

                            'bdg_def': {'commands': ['Общий файл с значениями по умолчанию'],
                                        'file_path': 'bdg/bdg_def.csv',
                                        'template': ('Signals', 'Instrument', 'Tendency', 'Leverage', 'Margin_type', 'Entrance_point', 'Stop_loss', 'Take_profit')},

                            'bdg_sig': {'commands': ['Общий файл с историей сигналов'],
                                        'file_path': 'bdg/bdg_sig.csv',
                                        'template': ('ID', 'Channel_name', 'Signals_amountfull', 'Signals_amount_month', 'Signals_amount_week', 'Signals_amount_day', 'Last_signal')},

                            'bdg_updates': {'commands': ['Общий файл с историей изменений в папок'],
                                            'file_path': 'bdg/bdg_updates.csv',
                                            'template': ('Channel_name', 'Status', 'Update_time')},

                            'bdg_links': {'commands': ['Файл ссылками на бирж сигналов'],
                                          'file_path': 'bdg/bdg_links.csv',
                                          'template': ('Workspace', 'Link')},
                        },

                        'templates':
                        {
                            'templates_signal': {'commands': ['Файл с шаблоном для отправки'], 'file_path': 'templates/templates_signal.txt'},
                            'templates_long_signal': {'commands': ['Фото для сигналов типа Лонг'], 'file_path': 'templates/templates_long_signal.jpg'},
                            'templates_comment': {'commands': ['Файл с шаблоном для комментария к сигналу'], 'file_path': 'templates/templates_comment.txt'},
                            'templates_short_signal': {'commands': ['Фото для сигналов типа Шорт'], 'file_path': 'templates/templates_short_signal.jpg'},
                            'templates_message': {'commands': ['Файл с шаблоном для сигналов отображения в боте'], 'file_path': 'templates/templates_message.txt'},

                        },
                        'out_message': {
                            'signal_all': {'commands': ['Файл с типами сигналов'], 'file_path': 'out_message/signal_all.csv'},
                        },

                        'others':
                        {
                            'environs': {'commands': [],
                                         'file_path': 'environs.txt',
                                         'template': ('Admin', 'Parser_user', 'Users', 'Api_id', 'Api_hash', 'Client_name', 'Bot_token', 'Signal_channel', 'Parse_from_folder', 'News_from_folder')},
                        }
                        }
    Commands_list = [
                    {'check_commands': ['/start', 'старт'], 'run_func': 'bot_start', 'states': [], 'send_message_obj': True},
                    {'check_commands': ['back menu', '<<< menu', '/menu', 'меню'], 'run_func': 'give_menu_keyboard', 'states': [], 'send_message_obj': False},
                    {'check_commands': ['back channels', '<<< channels', '/channels_menu', '📚 каналы', 'назад в каналы'], 'run_func': 'give_channels_menu_keyboard', 'states': [], 'send_message_obj': False},
                    {'check_commands': ['back settigns', '<<< settings', '/settings', '⚙️ настройки', 'настройки'], 'run_func': 'give_settings_keyboard', 'states': [], 'send_message_obj': False},
                    {'check_commands': ['/reload_parser', '♻️ Перезапустить парсер',], 'run_func': 'command_reload_parse_channels', 'states': [], 'send_message_obj': True},
                    {'check_commands': ['/account', 'аккаунты',], 'run_func': 'accounts_menu', 'states': [11, 25, 12, 26, 27], 'send_message_obj': False},
                    {'check_commands': ['/utility', 'утилиты',], 'run_func': 'utilities_menu', 'states': [11, 4, 6], 'send_message_obj': False},
                    {'check_commands': ['/parse_update', 'Изменение папок для парсинга',], 'run_func': 'parse_folder_menu', 'states': [11, 21, 22], 'send_message_obj': False},
                    {'check_commands': ['/files', 'Файлы для изъятия',], 'run_func': 'update_files_menu', 'states': [11, 14], 'send_message_obj': False},
                    {'check_commands': ['/permissions', 'Изменить доступ',], 'run_func': 'permissions_menu', 'states': [24], 'send_message_obj': True},
                    {'check_commands': ['/signout', 'Выйти с клиента',], 'run_func': 'log_out_menu', 'states': [24], 'send_message_obj': True},
                    {'check_commands': ['/parse_folder_update', 'папку для парсинга', 'папку для новостей'], 'run_func': 'set_parsing_folder', 'states': [19, 3, 13], 'send_message_obj': True},
                    {'check_commands': ['/render_channels', 'Каналы для отправки сигналов', 'список каналов для отправки сигналов'], 'run_func': 'set_render_channel', 'states': [19, 16, 17, 28, 29], 'send_message_obj': False},
                    {'check_commands': ['Добавить папку',], 'run_func': 'add_parsing_folder', 'states': [21], 'send_message_obj': False},
                    {'check_commands': ['Удалить папку',], 'run_func': 'remove_parsing_folder', 'states': [21], 'send_message_obj': False},
                    {'check_commands': ['Добавить канал',], 'run_func': 'add_render_channel', 'states': [22], 'send_message_obj': False},
                    {'check_commands': ['Удалить канал',], 'run_func': 'remove_render_channel', 'states': [22], 'send_message_obj': False},
                    {'check_commands': ['статус файл с данными',], 'run_func': 'send_render_channel_status_file', 'states': [28], 'send_message_obj': False},
                    {'check_commands': ['Задать статус',], 'run_func': 'set_render_channel_status', 'states': [22], 'send_message_obj': False},
                    {'check_commands': ['/file_check_time', 'Изменить время для автоматической проверке папок с каналами',], 'run_func': 'file_check_time', 'states': [18], 'send_message_obj': False},
                    {'check_commands': ['/stats_check_time', 'Изменить время для автоматической проверке обнулении и обновлении исторю сигналов',], 'run_func': 'stats_check_time', 'states': [18], 'send_message_obj': False},
                    {'check_commands': ['/paginator_value', 'Изменить количество каналов для пагинации',], 'run_func': 'set_paginator_value', 'states': [18], 'send_message_obj': False},
                    {'check_commands': ['/channels', 'список каналов',], 'run_func': 'get_channels_list', 'states': [10], 'send_message_obj': False},
                    {'check_commands': ['/not_conf_channels', 'список не инициализированных каналов',], 'run_func': 'get_no_configured_channels_list', 'states': [10], 'send_message_obj': False},
                    {'check_commands': ['/not_configured_channels', 'Cписок не инициализированных каналов',], 'run_func': 'get_no_configured_channels_list', 'states': [10], 'send_message_obj': False},
                    {'check_commands': ['/main_file',], 'run_func': 'file_sender', 'states': [10], 'send_message_obj': True},
                    {'check_commands': ['/scan', 'Сканировать папки',], 'run_func': 'reload_check_folders', 'states': [10], 'send_message_obj': False},
                    {'check_commands': ['/info_files', 'Файлы связанные с данными каналов',], 'run_func': 'bdg_files_menu', 'states': [14], 'send_message_obj': True},
                    {'check_commands': ['/template_files', 'Шаблонные файлы',], 'run_func': 'template_files_menu', ' states': [14], 'send_message_obj': True},
                    {'check_commands': ['/template_files', 'Файлы связанные с отправкой сигналов',], 'run_func': 'out_message_files_menu', 'states': [14], 'send_message_obj': True},
                    ]

    Must_have_signals_list = ('instrument', 'tendency', 'entrance_point', 'stop_loss', 'leverage', 'take_profit')
    Not_parse_signals_list = ('id', 'channel_name', 'channel_link', 'admin', 'rate', 'confidence_rate', 'signal_rate')
    Signals_template = ('ID', 'Channel_name', 'Channel_link', 'Admin', 'Rate', 'Confidence_rate', 'Signal_rate', 'Signals', 'Workspace', 'Instrument', 'Tendency', 'Leverage', 'Margin_type', 'Entrance_point', 'Stop_loss', 'Take_profit')
    Signals_bd_template = ('ID', 'Catched_time', 'Instrument', 'Sent_channel', 'Tendency', 'Leverage', 'Margin_type', 'Entrance_point', 'Stop_loss', 'Take_profit')
    Signal_type_template = ('ID', 'Type', 'Value')
    Def_signals_local_template = ('ID', 'Signals', 'Instrument', 'Tendency', 'Leverage', 'Margin_type', 'Entrance_point', 'Stop_loss', 'Take_profit')
    Channel_status_template = ('Priority', 'ID', 'Channel_name', 'Test_mode', 'Origin_message_send', 'Photo_send', 'Comment_send')

    Min_signal_amount = 2   # минимальное количество сигналов при нахождении которых сообщение будет считаться сигналом
    Common_tendency_signal_types = ('LONG', 'SHORT', 'ЛОНГ', 'ШОРТ')  # Основные типы тенденции
    Assumed_file_types = ('csv', 'txt', 'jpg')  # Типы файлов с которыми бот может работать
    Message_check_symbol = ' :  '  # символ в боте для разделения сигнала с его значением
    Signal_numer_symbol = '<num>'  # символ в сигнал файлах для обозначения чисел
    Channel_signal_send_order = 0
    Is_stats_update = True  # Нужно ли авто обновление некоторых данных как общее количество каналов, количество добавленных каналов и так далее(не стоит отключать)
    Stats_update_time = 86400  # Время авто обновление данных
    Full_channels_amount = 0
    Check_days = 3  # Время для проверки на отсутствие сигнала от каналов(к примеру 3 то если в течение 3 дней от канала не было сигналов то придёт оповещение)
    Russian_words_replacement = {'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'e', 'ж': 'j', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k',  'л': 'l', 'м': 'm', 'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u', 'ф': 'f', 'х': 'x', 'ц': 's', 'ч': 'ch', 'ш': 'sh', 'щ': 'sh', 'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'u', 'я': 'a'}
    Local_file_check_states = [30]


