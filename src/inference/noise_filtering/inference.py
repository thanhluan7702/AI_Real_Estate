import os
os.environ["CUDA_VISIBLE_DEVICES"]='0'

import argparse
import pandas as pd 
from transformers import (pipeline,
                          AutoConfig, 
                          AutoTokenizer, 
                          AutoModelForSequenceClassification)

from src.training.dataloader import truncate
from src.training.labels import noisy_label2id, noisy_id2label

parser = argparse.ArgumentParser()
parser.add_argument(
    '--file_name', 
    type = str,
    default = 'test', 
    help = "Pretrained model" 
)

args = parser.parse_args()

pretrain = "src/training/noise_filtering/best_models/base"

tokenizer=AutoTokenizer.from_pretrained(pretrain)
model=AutoModelForSequenceClassification.from_pretrained(pretrain,
                                                         ignore_mismatched_sizes=True)

recognizer = pipeline("sentiment-analysis",
                      model = model, 
                      tokenizer = tokenizer)

def predict(text): # used to test a sample
    return recognizer(text)[0]

text = 'nhà kiệt có 2 phòng ngủ 2 wc full nội thất , bếp điện đôi và quạt hút mùi . gần biển gần chợ và trường học thuận tiện cho gia đình 2 thế hệ'
# print(predict(text))

def inference(file_name = 'test'): # used to inference on dataframe
    path = 'src/training/noise_filtering/'
    data = pd.read_csv(path + 'dataset/' + file_name + '_dataset.csv')
    data['text'] = data['text'].apply(truncate)
    texts = data['text'].to_list()
    results = recognizer(texts, 
                        batch_size = 64,
                        truncation = True)
    data['prediction'] = [result['label'] for result in results]
    data['score'] = [result['score'] for result in results]
    data.to_csv(path + file_name + '_inference.csv', index=False)

# inference(args.file_name)