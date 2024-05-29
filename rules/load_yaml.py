import yaml
import glob

patterns_dictionary = {}
attributes = [] 

def load_yaml(file_name): # define function load pattern
    dct = {}
    patterns = yaml.safe_load(open(file_name, 'r', encoding='utf8'))['rules']
    for pattern in patterns: 
        type = pattern['type']
        regex = pattern['regex']
        dct[type] = regex # assign 
    return dct

for file in glob.glob("rules/patterns/*.yaml"): 
    entity = file.split('/')[-1].strip('.yaml')
    attributes.append(entity)
    
    variable_name = entity.lower() + '_pattern'
    patterns_corpus = load_yaml(file)
    patterns_dictionary[entity] = patterns_corpus

print("================== Load yaml files successfully ==================")