## import library 
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

import json 
import time
import warnings
warnings.filterwarnings('ignore')

## attribute
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


## define function 
def create_driver(): 
    driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options = opt)
    return driver

def count_page(url): 
    driver = create_driver()
    driver.get(url)
    return int(driver.find_elements(By.CLASS_NAME, 're__pagination-number')[-1].text.replace('.', ''))

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

def crawl_data(driver, news_type): 
    record = {}
    
    record['Loại tin'] = news_type
    record['Tiêu đề'] = driver.find_element(By.TAG_NAME, 'h1').text.strip()
    record['Địa chỉ'] = driver.find_element(By.CLASS_NAME, 're__pr-short-description.js__pr-address').text.strip()
    record['Mô tả'] = driver.find_element(By.CLASS_NAME, 're__section-body.re__detail-content.js__section-body.js__pr-description.js__tracking').text.strip()
    
    keys = [i.text for i in driver.find_elements(By.CLASS_NAME, 're__pr-specs-content-item-title')]
    values = [i.text for i in driver.find_elements(By.CLASS_NAME, 're__pr-specs-content-item-value')]
    for key, value in zip(keys, values): 
        record[key.strip()] = value.strip()
        
    return record

# def crawl_type_PJ(driver): 
#     record = {} 
    
#     record['Loại tin'] = 'Dự án'
#     record['Tiêu đề'] = driver.find_element(By.TAG_NAME, 'h2').text.strip()
    
#     table = [i.text for i in driver.find_elements(By.CLASS_NAME, 're__project-attr')]
#     keys, values = table[0::2], table[1::2]
#     for k, v in zip(keys, values): 
#         record[k] = v 
    
    
#     return record

def process(news_type, part, iter = None): 
    lst_data = []
    
    if iter == None: 
        print('No data in crawling process!')
        return
    
    for id_page in range(1, 2):  #limit page  
    # for id_page in range(1, iter):    
        driver = create_driver()
        url = f'https://batdongsan.com.vn/{part}/p{id_page}'
        print(f'Crawling on: ==> {url}')
        driver.get(url)
        lst_url = collect_item(driver, part)
        driver.quit()
        
        for url in lst_url: 
            bot = create_driver()
            bot.get(url)
            record = crawl_data(bot, news_type)
            lst_data.append(record)
            bot.quit()
            break # debug
        break # debug
    return lst_data

## crawling 
name_file = '../data/batdongsan_data.json'
exist_data = [] 
try:
    with open(name_file, "r", encoding="utf-8") as file:
        for line in file:
            try:
                record = json.loads(line)
                exist_data.append(record)
            except json.decoder.JSONDecodeError as e:
                pass 
except FileNotFoundError:
    pass

types_news = {'Nhà đất bán' : 'nha-dat-ban', 'Nhà đất cho thuê' : 'nha-dat-cho-thue'}
# types_news = {'Nhà đất bán' : 'nha-dat-ban', 'Nhà đất cho thuê' : 'nha-dat-cho-thue', 'Dự án' : 'du-an-bat-dong-san'}

for type, part in types_news.items(): 
    print(f'Crawling with {type} type')
    
    number_of_pages = count_page(f'https://batdongsan.com.vn/{part}/p1')
    print(f'Have {number_of_pages} pages on website')
    
    exist_data += process(type, part, number_of_pages)


with open(name_file, "w", encoding="utf-8") as json_file:
    json.dump(exist_data, json_file, ensure_ascii=False, indent=4)