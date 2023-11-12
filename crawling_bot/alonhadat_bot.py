## import library
from bs4 import BeautifulSoup
import requests
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import re
import json 
from datetime import date
import os 
import random 

flatform = 'alonhadat'
today = date.today() 
name = 'huong'
# order = 0 # increase one when new run same day
order=int(input('Nhap order: '))
start=int(input('Start: '))

path_txt = f'd:/DUE/AI_Real_Estate/data/source/{flatform}/{today}'

exist = False 
try:
    os.mkdir(path_txt)
except:
    exist = True
    pass 

## define function 
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
    # url = f'https://alonhadat.com.vn/nha-dat/{dct[type_news]}/trang--{id_page}.html' # general url 
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
    record['Mô tả'] = desc = re.sub(r'[\n\t\xa0]', '', ' '.join([t.text for t in content.find_all('div', class_ = re.compile('detail'))])).strip()

    moreinfor = content.find('div', class_ = 'moreinfor')
    labels = [l.text for l in moreinfor.find_all('span', class_ = 'label')]
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
    
    time.sleep(3)
    # time.sleep(10)
    # time.sleep(random.uniform(2,5))
    save_html(content, post_id)
    time.sleep(1)
    
    return record

## crawling 
name_file = f'd:/DUE/AI_Real_Estate/data/record/{flatform}/{today}'

exist = False 
try:
    os.mkdir(name_file)
except:
    exist = True
    pass 

exist_data = [] 
try:
    with open(f'{name_file}/{name}_{order}.json', "r", encoding="utf-8") as file:
        exist_data = json.load(file)
        # for line in file:
        #     try:
        #         record = json.loads(line)
        #         exist_data.append(record)
        #     except json.decoder.JSONDecodeError as e:
        #         pass 
except FileNotFoundError:
    pass

try: 
    for type_news in ['Cần bán']: #limited
    # for type_news in ['Cần bán', 'Cho thuê', 'Cần mua', 'Cần thuê']: 
        for id_page in range(start,21): #limited  #80
            print(f'Crawling with {type_news} on {id_page} page')
            soup = get_content(create_url(id_page, type_news))
            items = soup.findAll('div', class_ = 'content-item')
            links = []

            # collect link of item 
            for item in items: 
                links.append('https://alonhadat.com.vn/' + item.find('a')['href'])

            print(f'Page have {len(links)}')
            for link in links: 
                print(link)
                content = get_content(link)
                try: 
                    exist_data.append(crawl_data(content, type_news, link))
                except: 
                    pass
except Exception as e: 
    print(e)


with open(f'{name_file}/{name}_{order}.json', "w", encoding="utf-8") as json_file:
    json.dump(exist_data, json_file, ensure_ascii=False, indent=4) 