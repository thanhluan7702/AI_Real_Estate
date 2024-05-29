import re
import random
random.seed(42)
import argparse
import pandas as pd 

import warnings
warnings.filterwarnings("ignore")


parser = argparse.ArgumentParser(description='Choose level augment')
parser.add_argument(
    '--level', 
    type = str,
    default = False, 
    help = "Chosse task" 
)
args = parser.parse_args()

########################### 
lst_alpha = [
    'a', 'ă', 'â', 
    'b', 'c', 'd', 
    'đ', 'e', 'ê', 
    'g', 'h', 'i', 
    'k', 'l', 'm', 
    'n', 'o', 'ô', 
    'ơ', 'p', 'q', 
    'r', 's', 't', 
    'u', 'ư', 'v', 
    'x', 'y', 'w'
    ]

def remove_character(sentence, p=0.2):
    '''
    module support remove char in word
    nhàd --> nhà
    '''
    words = sentence.split()
    new_words = []
    for word in words:
        if random.random() < p:
            char = word[random.randint(0, len(word)-1)]
            new_word = word.replace(char, '')
            new_words.append(new_word)
        else:
            new_words.append(word)
    return  re.sub(r'\s+', ' ', ' '.join(new_words))

def insert_character(sentence, p=0.2):
    '''
    module support add char to word
    nhà --> nhàd
    '''
    words = sentence.split()
    new_words = []
    for word in words:
        if random.random() < p:
            new_word = word + random.choice(lst_alpha)
            new_words.append(new_word)
        else:
            new_words.append(word)
    return ' '.join(new_words)

def duplicate_character(sentence, p=0.2):
    '''
    module support duplicate char
    nhà --> nhà nhà
    '''
    words = sentence.split()
    new_words = []
    for word in words:
        if random.random() < p:
            new_words.extend([word]* random.randint(2, 3))
        else:
            new_words.append(word)
    return ' '.join(new_words)

def swap_couple_word(sentence):
    '''
    module support swap index for couple words
    3 mặt tiền ==> 3 tiền mặt 
    '''
    words = sentence.split()
    index1, index2 = [random.randint(1, len(words)-1) for i in range(2)]
    
    words[index1], words[index2] = words[index2], words[index1]
    return ' '.join(words)

######################## 
class SentenceAugment: 
    # only use for train dataset
    def __init__(self, path = "src/training/noise_filtering/dataset/train_dataset.csv"):
        self.data = pd.read_csv(path)


    def value_cnt(self): 
        dct_distribution = self.data['label'].value_counts().to_dict()
        count_normal = dct_distribution['normal']
        count_noisy = dct_distribution['noisy']
        
        if count_normal > count_noisy: 
            return {
                'augmented' : 'noisy',
                'volume' : count_normal - count_noisy 
            }
 
        elif count_noisy > count_normal: 
            return {
                'augmented' : 'normal', 
                'volume' : count_noisy - count_normal
            }
            
        else: 
            return None
        
    def augment(self): 
        status = self.value_cnt()
        if status: 
            label = status['augmented']
            num = status['volume']
            
            lst_text = self.data[self.data.label == label]['text'].to_list() 
            new_lst = []
            
            for _ in range(num): 
                text_choice = random.choice(lst_text)
                
                options =   {
                    0 : remove_character(text_choice),
                    1 : insert_character(text_choice),
                    2 : duplicate_character(text_choice), 
                    3 : swap_couple_word(text_choice)
                }
                # random option 
                option = options[random.randint(0, 3)]
                new_lst.append(option)
            
            new_df = pd.DataFrame({
                'text' : new_lst,
                'label' : label
            })
            
            df = pd.concat([self.data, 
                              new_df], axis = 0).reset_index(drop=True)
            df.to_csv("src/training/noise_filtering/dataset/train_dataset_aug.csv")
        return print('Augmentation Success') 
    
if __name__ == '__main__': 
    if args.level == 'sentence':
        module = SentenceAugment()
        module.augment()