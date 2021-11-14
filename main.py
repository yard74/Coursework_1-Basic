from pprint import pprint
from datetime import datetime
import requests
import json
from tqdm import tqdm


class YaUploader:
    url = "https://cloud-api.yandex.net:443/v1/disk/resources"

    def __init__(self, token: str):
        self.token = token

    def get_headers(self):
        return {
            'Content-Type': 'application/json',
            'Authorization': 'OAuth {}'.format(self.token)
        }

    def _create_folder(self, path):
        if path is None:
            print('Невозможно создать папку для текущего профиля VK.')
            return
        create_url = self.url
        headers = self.get_headers()
        folder_name = 'id_' + str(list(path.keys())[0])
        params = {"path": folder_name}
        response = requests.put(create_url, headers=headers, params=params)
        if response.status_code == 201:
            print(f"Папка '{folder_name}' успешно создана.")
            return folder_name
        if response.status_code == 409:
            print(f"Папка '{folder_name}' уже существует.")
            question = str(input('Хотите создать новую папку для фото? (y/n): '))
            if question == 'n':
                while question == 'n':
                    question = str(input('Тогда фото не будут загружены. Создадим новую папку?? (y/n): '))
                    if question == 'n':
                        print('Новая папка для фотографий не была создана.')
                        break
                    elif question == 'y':
                        counter = 1
                        new_folder_name = folder_name + '_' + str(counter)
                        new_params = {"path": new_folder_name}
                        new_response = requests.put(create_url, headers=headers, params=new_params)
                        while new_response.status_code == 409:
                            print(f"Папка '{new_folder_name}' уже существует.")
                            counter += 1
                            new_folder_name = folder_name + '_' + str(counter)
                            new_params = {"path": new_folder_name}
                            new_response = requests.put(create_url, headers=headers, params=new_params)
                        if new_response.status_code == 201:
                            print(f"Папка '{new_folder_name}' успешно создана.")
                            return new_folder_name
                    else:
                        print('Вы ввели некорректный символ.')
                        continue
            elif question == 'y':
                counter = 1
                new_folder_name = folder_name + '_' + str(counter)
                new_params = {"path": new_folder_name}
                new_response = requests.put(create_url, headers=headers, params=new_params)
                while new_response.status_code == 409:
                    print(f"Папка '{new_folder_name}' уже существует.")
                    counter += 1
                    new_folder_name = folder_name + '_' + str(counter)
                    new_params = {"path": new_folder_name}
                    new_response = requests.put(create_url, headers=headers, params=new_params)
                if new_response.status_code == 201:
                    print(f"Папка '{new_folder_name}' успешно создана.")
                    return new_folder_name
            else:
                print('Вы ввели некорректный символ. Создание папки прекращено.')
                return
        else:
            response.raise_for_status()

    def upload_from_url(self, photos_dict):
        if photos_dict is None:
            print('Выполнение операции прервано.')
            return
        upload_url = self.url + '/upload'
        headers = self.get_headers()
        folder = self._create_folder(photos_dict)
        if folder is None:
            print('Загрузка файлов остановлена.')
            return
        else:
            for profile, photos in photos_dict.items():
                bar = tqdm(total=len(photos), desc='Загрузка фото на Я.Диск', ncols=100, unit=' photos',
                           bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}, {rate_fmt}{postfix}]')
                data = []
                for photo in photos:
                    path = folder + '/' + photo['file_name']
                    source_url = photo['source_url']
                    params = {"path": path, "url": source_url}
                    response = requests.post(upload_url, headers=headers, params=params)
                    response.raise_for_status()
                    bar.update()
                    if response.status_code == 202:
                        data.append({'file_name': photo['file_name'], 'size': photo['size']})
                bar.close()
                with open('successful_upload.json', 'w', encoding='utf-8') as file:
                    json.dump(data, file, ensure_ascii=False, indent=2)
            print('Все фотографии успешно загружены.')


class VkUser:
    url = 'https://api.vk.com/method/'

    def __init__(self, token, version):
        self.params = {
            'access_token': token,
            'v': version
        }

    def get_user_profile_photos(self, ids):
        user_photos_url = self.url + 'photos.get'
        user_photos_params = {
            'owner_id': ids,
            'album_id': 'profile',
            'rev': 0,
            'extended': 1,
            'photo_sizes': 1
        }
        response = requests.get(user_photos_url, params={**self.params, **user_photos_params}).json()
        res = list(response.keys())
        if res[0] == 'error':
            print(f"Ошибка: {response['error']['error_msg']}")
            print('Не удалось получить фотографии пользователя.')
            return
        else:
            result_list = response['response']['items']
            profile_photos_dict = {}
            photos_list = []
            for photo in result_list:
                file_name = str(photo['likes']['count']) + '.jpg'
                size = str(photo['sizes'][-1]['width']) + 'x' + str(photo['sizes'][-1]['height'])
                source_url = photo['sizes'][-1]['url']
                if len(photos_list) == 0:
                    photos_list.append({'file_name': file_name, 'size': size, 'source_url': source_url})
                else:
                    check = True
                    for element in photos_list:
                        if file_name != element['file_name']:
                            check = False
                        elif file_name == element['file_name']:
                            unix_date = int(photo['date'])
                            date_t = str(datetime.utcfromtimestamp(unix_date).strftime('%Y-%m-%d_%H-%M-%S'))
                            file_name = str(photo['likes']['count']) + '_' + date_t + '.jpg'
                            photos_list.append({'file_name': file_name, 'size': size, 'source_url': source_url})
                            check = True
                            break
                    if check is False:
                        photos_list.append({'file_name': file_name, 'size': size, 'source_url': source_url})
        profile_photos_dict[ids] = photos_list
        return profile_photos_dict


if __name__ == '__main__':
    HELP = '''
    Список доступных команд:
    gpp - получить фотографии профиля пользователя VK
    upp - загрузить фотографии профиля пользователя VK на Я.Диск
    change_id - ввести id пользователя VK
    exit - завершить работу программы
    '''


    def main():
        vk_token = '958eb5d439726565e9333aa30e50e0f937ee432e927f0dbd541c541887d919a7c56f95c04217915c32008'
        vk_api_ver = '5.131'
        vk_client = VkUser(vk_token, vk_api_ver)
        ya_token = str(input('Введите Ваш OAuth-токен от Я.Диск: '))
        print('Для ознакомления со списком доступных команд введите help.\n')
        ya_client = YaUploader(ya_token)
        vk_id = ''
        while True:
            command = input('Введите команду: ')
            if str(command) == 'gpp':
                if vk_id == '':
                    vk_id = str(input('Введите id пользователя VK: '))
                photos_dict = vk_client.get_user_profile_photos(vk_id)
                if photos_dict is not None:
                    pprint(photos_dict)
            elif str(command) == 'upp':
                if vk_id == '':
                    vk_id = str(input('Введите id пользователя VK: '))
                photos_dict = vk_client.get_user_profile_photos(vk_id)
                ya_client.upload_from_url(photos_dict)
            elif str(command) == 'change_id':
                vk_id = str(input('Введите новый id пользователя VK: '))
            elif command.upper() == 'HELP':
                print(HELP)
            elif command == 'exit':
                print('Вы завершили работу. До свидания!')
                break
            else:
                print('Неизвестная команда! Воспользуйтесь справкой -> help')
                print()

    main()
