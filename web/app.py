from rules.entity_resolver import (rule_resolver,
                                   dia_chi_resolver,
                                   dien_tich_resolver,
                                   bien_resolver,
                                   kich_thuoc_resolver,
                                   duong_truoc_nha_resolver,
                                   dich_vu_resolver, 
                                   gia_resolver,
                                   so_tang_resolver,
                                   vi_tri_resolver,
                                   so_phong_ngu_resolver,
                                   toilet_resolver,
                                   song_resolver)
from rules.load_yaml import attributes
from src.inference.noise_filtering.inference import predict
from src.inference.ner.inference import extract_entities

from flask import Flask, render_template, request
import warnings
warnings.filterwarnings("ignore")

resolver_funcs = {
    "GIA" : gia_resolver,
    "DIA_CHI" : dia_chi_resolver,
    "DIEN_TICH" : dien_tich_resolver,
    "VI_TRI" : vi_tri_resolver,
    "DUONG_TRUOC_NHA" : duong_truoc_nha_resolver,
    "BIEN" : bien_resolver,
    "SONG" : song_resolver,
    "PHONG_NGU" : so_phong_ngu_resolver,
    "TOILET" : toilet_resolver,
    "SO_TANG" : so_tang_resolver,
    "DICH_VU" : dich_vu_resolver,
    "KICH_THUOC" : kich_thuoc_resolver
}



app = Flask(__name__)
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        sentence = request.form['sentence']
        
        noisy_output = predict(sentence)['label']
        if noisy_output == 'noisy': 
            message = "Try again with a sentence without noise"
            return render_template('index.html', raise_warning=message)
        else: 
            # next step to NER predict
            output = extract_entities(sentence)
            
            # remove duplicate 
            ner_output = {} 
            for k, v in output.items(): 
                value = list(set(v)) # handle for a case 
                # entity resolver
                if k == 'DIA_CHI': 
                    lst_quan_huyen = []
                    lst_phuong = [] 
                    lst_duong = []
                    
                    for v in value:
                        result = resolver_funcs['DIA_CHI'](v)
                        
                        quan_huyen = result['QUAN/HUYEN']
                        phuong = result['PHUONG']
                        duong = result['DUONG']
                        
                        if quan_huyen and quan_huyen not in lst_quan_huyen: 
                            lst_quan_huyen.append(quan_huyen)
                        if phuong and phuong not in lst_phuong: 
                            lst_phuong.append(phuong)
                        if duong and duong not in lst_duong: 
                            lst_duong.append(duong)
                    
                    ner_output['QUAN/HUYEN'] = lst_quan_huyen[0]
                    ner_output['PHUONG'] = lst_phuong[0]
                    ner_output['DUONG'] = lst_duong[0]
                    
                elif k == 'KICH_THUOC': 
                    value = value[0]
                    result = resolver_funcs['KICH_THUOC'](value)
                    
                    chieu_dai = result['CHIEU_DAI']
                    chieu_rong = result['CHIEU_RONG']
                    
                    if chieu_dai:
                        ner_output['CHIEU_DAI'] = chieu_dai 
                    if chieu_rong: 
                        ner_output['CHIEU_RONG'] = chieu_rong
                    
                else: 
                    result = list(set([resolver_funcs[k](v) for v in value]))
                    if k == 'DICH_VU': 
                        ner_output[k] = ', '.join(result)
                    else:
                        ner_output[k] = result[0]
            
            ### rule module 
            for attribute in attributes: 
                result = rule_resolver(text = sentence, 
                                  type = attribute)
                if result: 
                    ner_output[attribute] = result.lower()
                       
            entities_results = [sentence]
            for key, value in ner_output.items():
                entities_results.append(f'{key} : {value}')
                        
            return render_template('index.html', message= entities_results)
    return render_template('index.html')

if __name__ == '__main__':
    app.run()