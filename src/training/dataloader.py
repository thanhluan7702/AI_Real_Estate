import pandas as pd 
from keras.utils import pad_sequences
from datasets import Dataset, DatasetDict
from src.training.labels import noisy_id2label, noisy_label2id, ner_id2label, ner_label2id

def truncate(text): 
    length=text.split()
    if len(length) > 150: # fix out of index embedding
        length=length[:150] 
    return ' '.join(length)

def seq_load(file_path): 
    df=pd.read_csv(file_path)
    df['label']=df['label'].apply(truncate)
    df['label']=df['label'].apply(lambda x: noisy_label2id[x])
    df['text']=df['text'].apply(truncate)
    return df

class SeqLoader: 
    def __init__(self,
                 tokenizer=None,
                 train_path='/dataset/train_dataset.csv',
                 test_path='/dataset/test_dataset.csv',
                 valid_path='/dataset/valid_dataset.csv',
                 task = 'noise_filtering',
                 aug = False):
        
        self.tokenizer=tokenizer
        if aug:
            self.train_path= "src/training/" + task + '/dataset/train_dataset_aug.csv' 
        else: 
            self.train_path= "src/training/" + task + train_path
            
        self.test_path= "src/training/" + task + test_path
        self.valid_path= "src/training/" + task + valid_path

        self.train_data=seq_load(self.train_path)
        self.test_data=seq_load(self.test_path)
        self.valid_data=seq_load(self.valid_path)

    def _from_pandas(self): 
        train_data=Dataset.from_pandas(self.train_data)
        test_data=Dataset.from_pandas(self.test_data)
        valid_data=Dataset.from_pandas(self.valid_data)
        return train_data, test_data, valid_data
    
    def dataset_dict(self, 
                     train_data,
                     test_data,
                     valid_data): 
        dataset=DatasetDict()
        dataset['train']=train_data
        dataset['test']=test_data
        dataset['valid']=valid_data
        
        return dataset
        
    def preprocess_function(self, examples):
        return self.tokenizer( examples["text"], 
                                padding='max_length', 
                                truncation=True, 
                                max_length=256)
    
    def build_dataset(self): 
        train_data, test_data, valid_data=self._from_pandas()
        dataset=self.dataset_dict(train_data, test_data, valid_data)
        
        return dataset.map(self.preprocess_function,
                           batched=True)
        
class NerLoader: 
    def __init__(self,
                 tokenizer=None,
                 train_path='/dataset/train_dataset.csv',
                 test_path='/dataset/test_dataset.csv',
                 valid_path='/dataset/valid_dataset.csv',
                 task = 'ner'):
        
        self.tokenizer=tokenizer
        self.train_path= "src/training/" + task + train_path
        self.test_path= "src/training/" + task + test_path
        self.valid_path= "src/training/" + task + valid_path
        
    def _from_csv(self): 
        return DatasetDict.from_csv({
                                    'train' : self.train_path, 
                                    'test' : self.test_path, 
                                    'valid' : self.valid_path
                                })
    
    def tokenize_and_align_labels(self, examples):
        tokenized_inputs = self.tokenizer(examples["text"], 
                                          padding = True)
        
        labels = []
        for i, label in enumerate(examples[f"label"]):
            label = label.split()
            word_ids = tokenized_inputs.word_ids(batch_index=i)
            previous_word_idx = None
            label_ids = []
            for word_idx in word_ids:  # Set the special tokens to -100.
                if word_idx is None:
                    label_ids.append(-100)
                elif word_idx != previous_word_idx:  # Only label the first token of a given word.
                    label_ids.append(ner_label2id[label[word_idx]])
                else:
                    label_ids.append(-100)
                previous_word_idx = word_idx
            
            labels.append(label_ids)

        tokenized_inputs["labels"] = labels
        return tokenized_inputs
    
    def build_dataset(self): 
        dataset = self._from_csv()
        return dataset.map(self.tokenize_and_align_labels, 
                           batched=True)