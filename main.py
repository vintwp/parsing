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
    r_time = random.randint(2,4)
    time.sleep(r_time)
    r = requests.get(url, headers=headers, params=params)  # получаем страницу в виде байт кода
    return r


def get_mm_cats(html):
    soup = BeautifulSoup(html, 'html.parser')
    mm_cats = soup.find_all('div', class_='menu__item')
    categories = []
    for mm_cat in mm_cats:
        mm_childs = mm_cat.find_all('a', 'menu__link')
        for mm_child in mm_childs:
            categories.append({
                'category': mm_cat.find('span', 'menu__item-name').get_text(strip=True),
                'sub-category': mm_child.get_text(strip=True),
                'sub-category-url': mm_child.get('href')
            })
    return categories


def get_pages_nums(soup):
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
