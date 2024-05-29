## import library
import os
import sys
parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_path)

import random
import time
import re
import json
import requests
import pandas as pd 
from datetime import date 
from bs4 import BeautifulSoup
from urllib3.util.retry import Retry 
from requests.adapters import HTTPAdapter
import postgresql_module as sql

## initialize connection
conn, cursor = sql._connect()

## define attributes
flatform = 'alonhadat'
today = date.today() 
path_txt = f'data/source/{flatform}/{today}'

try:
    os.mkdir(path_txt)
except:
    pass 

## define function for crawling data
def request(): 
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

def get_content(url): 
    session = request()
    respone = session.get(url)
    soup = BeautifulSoup(respone.content, 'html5lib')
    return soup 

def create_url(id_page, type_news):
    dct = {'Cần bán':'can-ban', 'Cho thuê':'cho-thue', 'Cần mua':'can-mua', 'Cần thuê':'can-thue'} 
    url = f'https://alonhadat.com.vn/nha-dat/{dct[type_news]}/nha-dat/3/da-nang/trang--{id_page}.html'
    return url

def save_html(soup, post_id):
    html = soup.find('div', class_ = 'body').prettify()
    
    name_txt = f'{path_txt}/{post_id}.txt'
    with open(name_txt, "w", encoding = 'utf-8') as f:
        f.write(html)
    return

def crawl_data(content, type_news, link): 
    record = {}
    post_id = link.replace('.html', '').split('-')[-1]
    
    record['post_id'] = post_id
    record['Loại tin'] = type_news
    record['Tiêu đề'] = content.find('div', class_ = 'title').find('h1').text.strip()
    desc  = re.sub(r'[\r\n\t\xa0]', ' ', content.find('div', class_ = re.compile('detail text-content')).text).strip()
    record['Mô tả'] = re.sub(r'\s+', ' ', desc)
    
    moreinfor = content.find('div', class_ = 'moreinfor')
    labels = [l.text.replace(':', '') for l in moreinfor.find_all('span', class_ = 'label')]
    values = [v.text for v in moreinfor.find_all('span', class_ = 'value')]
    for label, value in zip(labels, values): 
        record[label.strip()] = value.strip()
    
    record['Địa chỉ'] = content.find('div', class_ = 'address').text.strip()

    moreinfor1 = [i.text for i in content.find('div', class_ = 'moreinfor1').find('div', class_ = 'infor').find_all('td')]
    keys = moreinfor1[0::2]
    values = moreinfor1[1::2]
    for key, value in zip(keys, values): 
        record[key.strip()] = value.strip()
    record['URL'] = link
    record['date'] = str(today)

    contact = content.find('div', class_ = 'contact-info')
    record['Liên hệ'] = contact.find('div', class_ = 'name').text.strip()
    record['phone'] = contact.find('div', class_ = 'fone').text.split('(')[0]
    
    # time.sleep(random.uniform(1, 10))
    save_html(content, post_id)
    time.sleep(1)
    
    return record

## crawling
data = [] 

try: 
    for type_news in ['Cần bán', 'Cho thuê']:
        for id_page in range(1, 3): 
            print(f'Crawling with {type_news} on {id_page} page')
            soup = get_content(create_url(id_page, type_news))
            items = soup.findAll('div', class_ = 'content-item')

            print(f'Page have {len(items)}')
            for item in items: 
                link = 'https://alonhadat.com.vn/' + item.find('a')['href']
                print(link)
                content = get_content(link)

                try: 
                    data.append(crawl_data(content, type_news, link))
                except: 
                    pass
                
except Exception as e: 
    print(e)

_, data_error = sql.insert_df(conn, cursor, 'ALONHADAT', data)

if len(data_error) > 0: 
    with open(f"alonhadat_{today}.json", 'w', encoding='utf-8') as file: 
        json.dump(data_error, file, indent=4, ensure_ascii=False)

sql._close(connection = conn, 
           cursor = cursor)