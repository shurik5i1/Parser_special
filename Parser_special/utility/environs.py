"""
Файл с функциями для клиентского файла
"""

from utility.common_settings import Utility


def env_reader(value:str,is_list=False):
    env_file = open('environs.txt','r')
    env = env_file.read()
    for env_row in env.split('\n'):
        if value in env_row:
            env_value = env_row.replace(value+'=', '')
            if is_list:
                env_value = [value for value in env_value.split('/') if not value in ['',' ']]
            return env_value


async def update_env_file(update_data:dict=None,is_remove=False):

    env_file_info_list = open(Utility.Global_files_list['others']['environs']['file_path'], 'r').read()


    update_items = list(update_data.items())
    # print('UPDATING ITEMS LIST -->', update_items)

    for item in update_items:
        print('UPDATING ITEM -->', item)
        for env_info_row in env_file_info_list.split('\n'):
            env_data_item = env_info_row.split('=')
            env_data_name = env_data_item[0]
            env_data_value = (env_data_item[1] if len(env_data_item)>1 else '')


            if item[0].lower() == env_data_name.lower():

                if type(item[1]) is list:
                    item_value = '/'.join(['']+item[1])

                else:
                    item_value=item[1]


                if is_remove:
                    env_data_value = env_data_value.replace(item_value, '')
                else:
                    env_data_value += '/' + item_value
                print('env update item -->', item_value, '\nWhat we recieve -->', env_data_value)


                env_data_value_list = {env_value for env_value in env_data_value.split('/') if not env_value in [' ','',None]}
                print('env_data_value_list -->', env_data_value_list)
                data_constructor = '/'.join(env_data_value_list)

                env_file_info_list = env_file_info_list.replace(env_info_row,f"{env_data_name}={data_constructor}")


    with open(Utility.Global_files_list['others']['environs']['file_path'], "w") as fobj:
        fobj.write(env_file_info_list)
        fobj.close()



Api_id = env_reader('Api_id')
Api_hash = env_reader('Api_hash')
bot_token = env_reader('Bot_token')