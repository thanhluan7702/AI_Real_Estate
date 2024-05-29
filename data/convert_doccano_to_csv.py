import pandas as pd   
import json 

with open('data.jsonl', 'r') as json_file:
    json_list = list(json_file)
    
def convert(record: str): 
    record = json.loads(record)
    text = record['text']
    label = record['label']
    label.sort(key = lambda x: x[0]) 
    words = [] 
    labels = [] 

    start = 0 
    for l in label: # l is [start, end, entity]
        entity = l[-1]
        
        sub_txt = text[start: l[0]].split() # handle OTHER tag 
        words.extend(sub_txt)
        labels.extend("O" * len(sub_txt))
        
        sub_txt = text[l[0]:l[1]].split() # handle entity tag 
        words.extend(sub_txt)
        labels.extend(["B-"+entity]+["I-"+entity]*(len(sub_txt)-1))
        start = l[1]

    # handle the last entity to the end sequence
    sub_txt = text[start:].split()
    words.extend(sub_txt)
    labels.extend("O" * len(sub_txt))
    
    return ' '.join(words), ' '.join(labels)

sequences = []
labels = []

for record in json_list: 
    seq, lb = convert(record)
    sequences.append(seq)
    labels.append(lb)
    
data = pd.DataFrame({
    "text" : sequences,
    "label" : labels
})

data['check'] = data['label'].apply(lambda x: 'B-' in x)
data = data[data.check == True][['text', 'label']].reset_index(drop=True)
# data.to_csv('data.csv', index=False)