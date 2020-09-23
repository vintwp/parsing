import requests
from bs4 import BeautifulSoup
import time
import random
import csv

headers = {'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:75.0) Gecko/20100101 Firefox/75.0',
           'accept': '*/*'}
host = 'https://mma.in.ua/'
file = 'mma.csv'
url = 'https://mma.in.ua/'

def get_html(url, params=None):
    r_time = random.randint(2,4) # рандомная константа для таймера
    time.sleep(r_time) # таймер для паузы между запросами
    r = requests.get(url, headers=headers, params=params)  # получаем страницу в виде байт кода
    return r


def get_mm_cats(html):
    soup = BeautifulSoup(html, 'html.parser') # "суп" - перекодированный html файл
    mm_cats = soup.find_all('div', class_='menu__item') #находим все div с классом menu__item (пункты в левом меню)
    categories = []
    for mm_cat in mm_cats:
        mm_childs = mm_cat.find_all('a', 'menu__link') #извлекаем из родительских классов - вложенные подкатегории.Каждый вложенный элемент будет новым элементом массива
        for mm_child in mm_childs:
            #из каждого элемента списка mm_childs ивзлекаем имя подраздела, и его ссылку (также имя родителя)
            categories.append({
                'category': mm_cat.find('span', 'menu__item-name').get_text(strip=True),
                'sub-category': mm_child.get_text(strip=True),
                'sub-category-url': mm_child.get('href')
            })

            # Получили значения всех родразделов, с ссылками и названиями в виде кортежа с вложенными словарями,
            # где каждый новый словарь - это подраздел
    return categories


def get_pages_nums(soup):
    # На каждой странице подраздела проверяем наличие блока pagination - счетчик страниц.
    # Логика работы:
    # Сперва проверяем наличие самого блока (товаров может быть меньше, чем максимальное кол-во на одной странице).
    # Если этого блока нет - возвращаем номер страницы 1, и последнюю страницу с номером
    # 2) В случае если блок есть, проверяем на наличие стрелки перехода страниц (на следующую страницу)
    # Если стрелка перехода есть, то последней странице присваиваем номер 0, а номер текущей страницы из значения в классе pagination__item--active
    # Если стрелка перехода нет (мы уже на последней странице), то присваиваем значение последней страницы
    if soup.find('div', class_='pagination'):
        pageNum = int(soup.find('span', class_='pagination__item--active').get_text())
        if soup.find('span', class_='pagination__item--next'):
            lastPageNum = 0
        else:
            lastPageNum = pageNum
    else:
        pageNum, lastPageNum = 1, 1
    return pageNum, lastPageNum


def get_content(soup, cat_name, sub_cut_name):
    # Получаем все блоки div с классом product-tile__wrapper
    # Извлекаем значения ссылок, цены, картинок в список cо словарями, где каждый словарь - это один товар

    products = []
    items = soup.find_all('div', class_='product-tile__wrapper')
    for item in items:
        products.append({
            'category-name': cat_name,
            'sub-category-name': sub_cut_name,
            'product-link': item.find('a', class_='product-tile__name').get('href'),
            'product-title': item.find('a', class_='product-tile__name').get_text(strip=True),
            'product-price': item.find('div', class_='product-tile__price').get_text(strip=True).partition(' ')[0],
            'product-image': item.find('img', class_='product-tile__thumb').get('src').replace('352x352', '1000x1000')
        })

    return products

def save_file(products, file):
    # Запись в сsv файл
    with open(file, 'w', newline='') as file:
        writer = csv.writer(file, delimiter=';')
        writer.writerow(['Категория','Подкатегория','Ссылка', 'Название', 'Цена', 'Картинка'])
        for item in products:
            writer.writerow([item['category-name'],
                             item['sub-category-name'],
                             item['product-link'],
                             item['product-title'],
                             item['product-price'],
                             item['product-image']])

html = get_html(url)
if html.status_code == 200:
    # 1) Проверяем на доступность страницы  сайта (html.status_code == 200)
    # 2) get_mm_cats c это функцией получаем список подразделов с товарами (конечные страницы c товарами). На вход получили ссылку url (основного сайта)
    # 3) Для дальнейшего использования в csv файле из переменной categories получили значения разделов и подразделов сайта cat_name, sub_cut_name = category.get('category'), category.get('sub-category')
    # 4) Основной цикл по подразделам сайта categories. получаем значение первого подраздела через category.get('sub-category-url')
    # 5) Запрашиваем страницу через html = get_html(url), и превращаем в "суп". soup = BeautifulSoup(html.text, 'html.parser')
    # 6) Получаем номера страниц подраздела got_pages = get_pages_nums(soup)
    # 7) Постоянный цикл до того момента, пока текущая страница не будет равна последней.
    # 8) Парсинг товаров на текущей странице products.extend(get_content(soup, cat_name, sub_cut_name))
    # 9) Сохранение в csv файл save_file(products, file)
    # 10) Запрос на переход на следующую страницу html = get_html(url, params={'page': pages[0]}) + также получаем код страницы
    # 11) Превращаем страницу в "суп" и проверяем страницу последняя/не последняя pages = [get_pages_nums(soup)[0], get_pages_nums(soup)[1]] для цикла While
    # 12) Если текущая и последняя странца равны, то парсим товары , сохраняем результат и выходим из цикла  while pages[0] != pages[1] (так как страницу у нас уже нет)
    # 13) Повторяем алгоритм для каждого подраздела из списка categories

    products = []
    categories = get_mm_cats(html.text)
    for category in categories:
        url = category.get('sub-category-url')
        cat_name, sub_cut_name = category.get('category'), category.get('sub-category')
        html = get_html(url)
        soup = BeautifulSoup(html.text, 'html.parser')
        #Получаем номер текущей страницы
        got_pages = get_pages_nums(soup)
        pages = [got_pages[0], got_pages[1]]
        while pages[0] != pages[1]:
            products.extend(get_content(soup, cat_name, sub_cut_name))
            save_file(products, file)
            print(f'Страница {pages[0]}, Категория - {sub_cut_name}')
            pages[0] += 1
            html = get_html(url, params={'page': pages[0]})
            soup = BeautifulSoup(html.text, 'html.parser')
            pages = [get_pages_nums(soup)[0], get_pages_nums(soup)[1]]
        else:
            products.extend(get_content(soup, cat_name, sub_cut_name))
            save_file(products, file)
            print(f'Страница {pages[0]}, Категория - {sub_cut_name}')
            pass
else:
    print('Something wrong')

print('done')
