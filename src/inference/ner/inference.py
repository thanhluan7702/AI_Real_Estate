import os
os.environ["CUDA_VISIBLE_DEVICES"]='0'

import json
import argparse
import pandas as pd 
from transformers import (pipeline,
                          AutoConfig, 
                          AutoTokenizer, 
                          AutoModelForTokenClassification)

from src.training.dataloader import truncate
from src.training.labels import ner_label2id, ner_id2label

parser = argparse.ArgumentParser()
parser.add_argument(
    '--file_name', 
    type = str,
    default = 'test', 
    help = "Pretrained model" 
)

args = parser.parse_args()

pretrain = "src/training/ner/best_models/base"
tokenizer=AutoTokenizer.from_pretrained(pretrain)

model=AutoModelForTokenClassification.from_pretrained(pretrain)

config=AutoConfig.from_pretrained(pretrain)

recognizer = pipeline("ner",
                      model = model, 
                      tokenizer = tokenizer,
                      grouped_entities=True)

def extract_entities(text): # used for demo result 
    '''
    example: 
    
            {'VI_TRI': ['kiệt'],
            'PHONG_NGU': ['2 phòng ngủ'],
            'TOILET': ['2 w'],
            'BIEN': ['gần biển'],
            'DICH_VU': ['gần chợ', 'trường học']}
    '''
    result = recognizer(text)
    final_result = {} # combine entities for one type

    for r in result: 
        ent = r['entity_group']
        if ent not in final_result: 
            final_result[ent] = [r['word']]
        else: 
            final_result[ent].append(r['word'])
    return final_result

text = 'nhà kiệt có 2 phòng ngủ 2 wc full nội thất , bếp điện đôi và quạt hút mùi . gần biển gần chợ và trường học thuận tiện cho gia đình 2 thế hệ'
# print(extract_entities(text))

def inference(file_name = 'test'): # used for pseudo new data
    '''return jsonl file'''
    
    def write_jsonl(file_path, data):
        with open(file_path, 'w', encoding='utf-8') as file:
            for item in data:
                json.dump(item, file, ensure_ascii=False)
                file.write('\n')
            
    path = 'src/training/ner/'
    # data = pd.read_csv(path + 'dataset/' + file_name + '_dataset.csv')
    data = pd.read_csv(path + 'data/' + file_name + '.csv')
    texts = data['text'].to_list()
    
    results = recognizer(texts, 
                    batch_size = 64) # return batch results
    
    final_result = [] 
    for row in data.iterrows():
        _json = {
            'id' : row[0],
            'text' : row[1]['text'],
            'label' : []
        }
        
        for r in results[row[0]]: 
            _json['label'].append([r['start'], r['end'], r['entity_group']])
        
        final_result.append(_json)
    
    write_jsonl(f'{path}+{file_name}_inference.jsonl', final_result)
    return 

# inference(args.file_name)