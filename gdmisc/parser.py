import requests
import re


# [(0) Название уровня, [1] Ник автора, (2) ID уровня, (3) Текущая оценка, (4) Наименование оценки, (5) Загрузки, (6) Лайки, (7) Длина, (8) Сонг]
def get_parsed_level_data(level_id: int) -> list | None:
    print("get_parsed_level_data")
    page = requests.get(f'https://gdbrowser.com/{level_id}')

    matches = re.findall(r'content="(.+?)"', str(page.content))
    print(matches)

    if matches[0] == "Level Search":
        print(f"Рекурсия проверка: {matches[0]}")
        return None

    data = []
    data.append(matches[0].split(' by ')[0])
    data.append(matches[0].split(' by ')[1])
    data_stream = matches[1].split(" | ")
    for d in data_stream:
        data.append(d[d.find(":") + 2:])
    data.append(matches[2])


    return data

# возвращает КП
def get_parsed_creator_data(author_name: str) -> int:
    page = requests.get(f'https://gdbrowser.com/u/{author_name}')
    matches = re.findall(r'content="(.+?)"', str(page.content))

    cp = matches[1].split(" | ")[5]
    return int(cp[cp.find(":") + 2:])
