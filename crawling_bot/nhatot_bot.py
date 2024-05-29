## import library
import re
import os
import sys
parent_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_path)

import json
import time
import pandas as pd 
from datetime import date
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support import expected_conditions as EC
import postgresql_module as sql 

## initialize connection
conn, cursor = sql._connect()

## define attributes 
flatform = 'nhatot'
today = date.today() 
path_txt = f'data/source/{flatform}/{today}'

try:
    os.mkdir(path_txt)
except:
    pass 

## attribute for selenium
opt = Options()
opt.add_argument("--disable-infobars")
opt.add_argument("start-maximized")
opt.add_argument("--disable-extensions")
opt.add_argument("--disable-notifications")
opt.add_argument("--disable-gpu")
# opt.add_argument("--headless")
opt.add_experimental_option("prefs", { \
    "profile.default_content_setting_values.media_stream_mic": 1, 
    "profile.default_content_setting_values.media_stream_camera": 1,
    "profile.default_content_setting_values.geolocation": 1, 
    "profile.default_content_setting_values.notifications": 1 
  })

## define function for crawling data
def create_driver(): 
    driver = webdriver.Chrome(options = opt)
    return driver

def create_url(id_page, type_news):
    dct = {'Mua bán':'mua-ban', 'Cho thuê':'thue', 'Dự án':'du-an', 'Môi giới':'chuyen-trang-moi-gioi'} 
    url = f'https://www.nhatot.com/{dct[type_news]}-bat-dong-san-da-nang?page={id_page}'
    return url

def close_advertise(driver): 
    width = driver.execute_script("return window.innerWidth")
    height = driver.execute_script("return window.innerHeight")

    actions = ActionChains(driver)
    actions.move_by_offset(0.5* width, 0.5* height).click().perform()

def count_item(driver): 
    return len(driver.find_elements(By.CLASS_NAME, 'AdItem_adItem__gDDQT')) 

def next_item(driver): 
    return driver.find_elements(By.CLASS_NAME, 'AdItem_adItem__gDDQT')

def save_html(page_source, post_id):    
    html = BeautifulSoup(page_source, 'html5lib').find('div', class_ = 'row base').prettify()

    name_txt = f'{path_txt}/{post_id}.txt'
    with open(name_txt, "w", encoding = 'utf-8') as f:
        f.write(html)
    return

def crawl_data(driver, type_news): 
    record = {}
    post_id = driver.current_url.split('/')[-1].split('.')[0]

    record['post_id'] = post_id
    record['Loại tin'] = type_news
    record['Tiêu đề'] = driver.find_element(By.CLASS_NAME, 'AdDecriptionVeh_adTitle__vEuKD').text.strip()
    record['Giá'], record['Diện tích'] = driver.find_element(By.CLASS_NAME, 'AdDecriptionVeh_price__u_N83').text.split(' - ')
    record['Địa chỉ'] = driver.find_element(By.CLASS_NAME, 'fz13').text.strip().replace('\nXem bản đồ', '')
    
    # detail table
    try: 
        driver.find_element(By.CLASS_NAME, 'styles_button__SVZnw').click() # button detail
    except: 
        pass
    
    for info in driver.find_elements(By.CLASS_NAME, 'col-xs-6.no-padding.AdParam_adParamItemVeh__mCpPS'): 
        try:
            k, v = info.text.split(':')
            record[k] = v
        except: 
            pass    

    desc = re.sub(r'\n', ' ', driver.find_element(By.CLASS_NAME, 'styles_adBody__vGW74').text.strip())
    record['Mô tả'] = re.sub(r'\s+', ' ', desc)
    
    record['URL'] = driver.current_url
    record['date'] = str(today)
    
    record['Liên hệ'] = driver.find_element(By.CLASS_NAME, 'SellerProfile_flexDiv__IEgQl').find_element(By.TAG_NAME, 'b').text.strip()
    record['card_visit'] = driver.find_element(By.CLASS_NAME, 'SellerProfile_sellerWrapperVeh__UFHlO').get_attribute("href")
    
    save_html(driver.page_source, post_id)

    return record

## crawling
data = []     

try: 
    for type_news in ['Mua bán', 'Cho thuê']: 
        for id_page in range(1, 2):
            
            driver = create_driver()
            driver.get(create_url(id_page, type_news))
            
            close_advertise(driver)

            time.sleep(1)
            
            count = count_item(driver)
            print(f'Crawling for {type_news} on {id_page} page with {count} items')
            
            for id in range(count):
                try:
                    next_item(driver)[id].click()
                    time.sleep(1)
                    
                    wait = WebDriverWait(driver, 10)
                    element_scroll = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "AdParam_adParamTitle__bU__w")))
                    
                    driver.execute_script("arguments[0].scrollIntoView(true);", element_scroll)
                    
                    time.sleep(1)
                    data.append(crawl_data(driver, type_news))
                    time.sleep(1)
                    
                    driver.back()   
                    time.sleep(1)   
                    
                    driver.execute_script("window.scrollTo(0, 100);")
                    time.sleep(1)
                except: 
                    print('Skip Error!!')
                    pass
            driver.quit()    
except Exception as e: 
    print(e)

_, data_error = sql.insert_df(conn, cursor, 'NHATOT', data)

if len(data_error) > 0: 
    with open(f"nhatot_{today}.json", 'w', encoding='utf-8') as file: 
        json.dump(data_error, file, indent=4, ensure_ascii=False)

sql._close(connection = conn, 
           cursor = cursor)

driver.quit()