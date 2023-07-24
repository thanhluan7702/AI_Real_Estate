import json
import pandas as pd 


def read(name_file): 
    with open(f'data/{name_file}.json', 'r', encoding='utf-8') as file:
        data = json.load(file)
    pd.DataFrame(data).to_csv(f'data/{name_file}.csv', index=False)

read('alo_nha_dat_data')