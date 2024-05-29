## import library 
import re
import os 
import sys 
parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_path)

import time
import json
import pandas as pd 
from datetime import date
from bs4 import BeautifulSoup
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
import postgresql_module as sql

## initialize connection
conn, cursor = sql._connect()

## define attributes
flatform = 'batdongsan'
today = date.today() 
path_txt = f'data/source/{flatform}/{today}'

try:
    os.mkdir(path_txt)
except:
    pass 

## define function for crawling data
def create_driver(): 
    opt = uc.ChromeOptions()
    opt.add_argument('--disable-popup-blocking')
    driver = uc.Chrome(options = opt)
    return driver

def count_page(driver, url): 
    driver.get(url)
    return driver, int(driver.find_elements(By.CLASS_NAME, 're__pagination-number')[-1].text.replace('.', ''))

def collect_item(driver, part):
    lst_url = []
    if part == 'du-an-bat-dong-san': 
        driver.execute_script("window.scrollBy(0, 100);")
        lst_items = driver.find_elements(By.CLASS_NAME, 'js__project-card.js__card-project-web.re__prj-card-full')
        for item in lst_items: 
            lst_url.append(item.find_element(By.TAG_NAME, 'a').get_attribute('href'))
    else:
        lst_items = driver.find_element(By.ID, 'product-lists-web').find_elements(By.CLASS_NAME, 'js__product-link-for-product-id')
        for item in lst_items: 
            lst_url.append(item.get_attribute('href'))
    
    return lst_url

def save_html(page_source, post_id):    
    html = BeautifulSoup(page_source, 'html5lib').find('div', class_ = 're__pr-info pr-info js__product-detail-web').prettify()
    
    name_txt = f'{path_txt}/{post_id}.txt'
    with open(name_txt, "w", encoding = 'utf-8') as f:
        f.write(html)
    return

def crawl_data(driver, news_type): 
    record = {}
    
    post_id = driver.current_url.split('-')[-1].split('pr')[1]
    
    record['post_id'] = post_id
    record['Loại tin'] = news_type
    record['Tiêu đề'] = driver.find_element(By.TAG_NAME, 'h1').text.strip()
    record['Địa chỉ'] = driver.find_element(By.CLASS_NAME, 're__pr-short-description.js__pr-address').text.strip()
    desc = re.sub(r'\n', ' ', driver.find_element(By.CLASS_NAME, 're__section-body.re__detail-content.js__section-body.js__pr-description.js__tracking').text.strip())
    record['Mô tả'] = re.sub(r'\s+', ' ', desc)
    
    keys = [i.text for i in driver.find_elements(By.CLASS_NAME, 're__pr-specs-content-item-title')]
    values = [i.text for i in driver.find_elements(By.CLASS_NAME, 're__pr-specs-content-item-value')]

    for key, value in zip(keys, values): 
        record[key.strip()] = value.strip()
       
    record['URL'] = driver.current_url
    record['date'] = str(today)
    
    contact = driver.find_elements(By.CLASS_NAME, "re__contact-name.js_contact-name")[1].find_element(By.TAG_NAME, 'a')
    record['Liên hệ'] = contact.text.strip()
    record['card_visit'] = contact.get_attribute("href")

    save_html(driver.page_source, post_id)
    
    return record

def switch_tab(driver, id_tag):
    if id_tag == 1: 
        driver.execute_script("window.open('', '_blank');")
    elif id_tag == 0: 
        driver.close()
    driver.switch_to.window(driver.window_handles[id_tag])        
    return driver


def process(driver, news_type, part, iter = 10):
    lst_data = []
    
    if iter == None: 
        print('No data in crawling process!')
        return
        
    for id_page in range(1, iter):    
        try:
            url = f'https://batdongsan.com.vn/{part}-da-nang/p{id_page}'
            print(f'Handling on page {id_page}')
            driver.get(url)
            lst_url = collect_item(driver, part)
            
            for url in lst_url: 
                print(f'Crawling on {url}')
                
                driver = switch_tab(driver, 1)
                
                driver.get(url)
                record = crawl_data(driver, news_type)
                lst_data.append(record)

                driver = switch_tab(driver, 0)
        except: 
            pass
    return driver, lst_data

## crawling 
driver = create_driver()

data = [] 

types_news = {'Nhà đất bán' : 'nha-dat-ban', 'Nhà đất cho thuê' : 'nha-dat-cho-thue'}

try: 
    for type, part in types_news.items(): 
        print(f'Crawling with {type} type')
        
        driver, number_of_pages = count_page(driver, f'https://batdongsan.com.vn/{part}-da-nang/p1')
        print(f'Have {number_of_pages} pages on website')
        
        driver, lst_data = process(driver, type, part, 2)
        data += lst_data
except Exception as e: 
    print(e)

driver.quit()

_, data_error = sql.insert_df(conn, cursor, 'BATDONGSAN', data)

if len(data_error) > 0: 
    with open(f"batdongsan_{today}.json", 'w', encoding='utf-8') as file: 
        json.dump(data_error, file, indent=4, ensure_ascii=False)

sql._close(connection = conn, 
           cursor = cursor)