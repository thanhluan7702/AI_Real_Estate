from transformers import DataCollatorWithPadding, DataCollatorForTokenClassification 

class DataCollator: 
    def __init__(self, tokenizer):
        self.tokenizer=tokenizer
    
    def collator(self): 
        return DataCollatorWithPadding(tokenizer=self.tokenizer)
    
    def ner_collator(self): 
        return DataCollatorForTokenClassification(tokenizer=self.tokenizer)