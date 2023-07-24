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
def create_url(id_page, type_news):
    dct = {'Mua bán':'mua-ban', 'Cho thuê':'thue', 'Dự án':'du-an', 'Môi giới':'chuyen-trang-moi-gioi'} 
    url = f'https://www.nhatot.com/{dct[type_news]}-bat-dong-san?page={id_page}'
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

def crawl_data(driver, type_news): 
    record = {}
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
        k, v = info.text.split(':')
        record[k] = v

    record['Mô tả'] = driver.find_element(By.CLASS_NAME, 'styles_adBody__vGW74').text
    record['URL'] = driver.current_url

    return record


## crawling
name_file = '../data/nhatot_data.json'
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

try: 
    for type_news in ['Mua bán', 'Cho thuê', 'Dự án', 'Môi giới']: 
        for id_page in range(1, 3): #limited
            print(f'Crawling with {type_news} on {id_page} page')
            
            driver = webdriver.Chrome(executable_path=ChromeDriverManager().install(), options = opt)
            driver.get(create_url(id_page, type_news))
            
            close_advertise(driver)

            time.sleep(2)
            
            count = count_item(driver)
            print(f'Have {count} items')
            for id in range(count):
                next_item(driver)[id].click()
                time.sleep(2)
                
                wait = WebDriverWait(driver, 10)
                element_scroll = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "AdParam_adParamTitle__bU__w")))
                driver.execute_script("arguments[0].scrollIntoView(true);", element_scroll)
                
                time.sleep(3)
                exist_data.append(crawl_data(driver, type_news))
                time.sleep(3)
                
                driver.back()   
                time.sleep(3)   
                
                driver.execute_script("window.scrollTo(0, 100);")
                time.sleep(3)
            driver.quit()
except Exception as e: 
    print(e)

with open(name_file, "w", encoding="utf-8") as json_file:
    json.dump(exist_data, json_file, ensure_ascii=False, indent=4)