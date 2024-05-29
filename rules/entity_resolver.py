import re
from rules.load_yaml import patterns_dictionary

def rule_resolver(text:str = None, type:str=None): 
    '''
        text: is input sentence 
        type: specific entity for extract
    '''
    
    if type == None: 
        raise TypeError("Entity type is a required attribute")
    
    if type == 'LOAI_BDS': 
        text = ' '.join(text.split()[:30])
    
    if text == None: 
        raise ValueError("Text not null")
    
    patterns = patterns_dictionary[type]  
    for type, pattern in patterns.items(): 
        for p in pattern: 
            _match = re.search(p, text)
            
            if _match: 
                return type
    return 

def dia_chi_resolver(string): 
    # quan huyen
    quan_huyen = re.search('(hải châu|cẩm lệ|thanh khê|liên chiểu|ngũ hành sơn|sơn trà|hòa vang|hoàng sa)', string)
    if quan_huyen: 
        quan_huyen = quan_huyen.group()
        if quan_huyen in ('hoàng sa', 'hòa vang'):
            quan_huyen = 'huyện ' + quan_huyen
        else: 
            quan_huyen = 'quận ' + quan_huyen
    
    # phuong
    lst_phuong = [
            'Hải Châu 1', 'Hải Châu 2', 'Thạch Thang', 'Thanh Bình', 'Thuận Phước',
            'Bình Thuận', 'Hoà Thuận', 'Nam Dương', 'Phước Ninh', 'Bình Hiên',
            'Hoà Cường', 'Khuê Trung', 'An Khê', 'Thanh Lộc Đán', 'Xuân Hà', 'Tam Thuận',
            'Chính Gián', 'Thạc Gián', 'Tân Chính', 'Vĩnh Trung', 'An Hải Tây',
            'An Hải Bắc', 'An Hải Đông', 'Nại Hiên Đông', 'Mân Thái', 'Phước Mỹ',
            'Thọ Quang', 'Bắc Mỹ An', 'Hòa Quý', 'Hòa Hải', 'Mỹ An', 'Hòa Khê'
        ]
    lst_phuong = [l.lower() for l in lst_phuong]
    phuong_pattern = '|'.join(lst_phuong)
    
    phuong = re.search(phuong_pattern, string)
    if phuong: 
        phuong = 'phường ' + phuong.group()
    
    # duong 
    duong =  re.search('(kiệt|đường) (\w+\s){2,3}\w+', string)
    if duong: 
        duong = duong.group()
        duong = re.sub(r'(quận|phường|đà nẵng|huyện|tp|q |thành|thành phố|kiệt|kiet|duong|đường)', '', duong).strip().lower()

    return {
        'QUAN/HUYEN' : quan_huyen,
        'PHUONG' : phuong,
        'DUONG' : duong
    }
    
def dien_tich_resolver(value): 
    '''
    dt 534,9m2 => 534.9
    '''
    return re.search("\d+(\.|\,)?(\d+)?", value).group().replace(',', '.')

def bien_resolver(value): 
    value = value.replace("bãi tắm", "biển")
    if re.search('view( nhìn| hướng| trực diện)?( ra)? biển', value): 
        return 'view biển'

    elif re.search('(ven|dọc|mặt|mặt tiền|cạnh)( bờ)? biển', value):
        return 'ven biển'

    # distance
    elif re.search('\d+\s?(m|km)', value):
        value = re.search('\d+\s?(m|km)', value).group()
        if 'km' in value: 
            return "cách biển " + str(int(value.strip('km').strip())*1000) + 'm'
        else: 
            return "cách biển " + value.strip('m').strip() + 'm'
        
    # time 
    elif re.search('\d+(\.)?(\d+)?\s?(phút|p)?', value):
        value = re.search('\d+(\.)?(\d+)?\s?(phút|p)?', value).group()
        minutes = re.search('\d+(\.)?(\d+)?', value).group() 
        return "cách biển " + str(minutes) + ' phút'
    return value

def kich_thuoc_resolver(value): 
    
    value = value.replace(',', '.').replace(' . ', ' ').replace('*', 'x')
    value = re.sub(r"(\d+)m(\d+)", r"\1.\2", value) # replace 4m4 x 5m5 ==> 4.4 x 5.5
    rong, dai = None, None
    
    # ngang x rong
    value_search = re.search('\d+(\.\d+)?m?(\s| x |x)?\s?\d+(\.\d+)?m?', value)
    if value_search: 
        if 'x' in value: 
            value_search = value_search.group().split('x')
        else: 
            value_search = value_search.group().split()
            
        value_sort = sorted([float(value.strip().strip('m')) for value in value_search]) # dai > rong
        return {
            'CHIEU_DAI' : value_sort[1],
            'CHIEU_RONG' : value_sort[0]
        }
    
    # ngang 
    value_search = re.search('(rộng|ngang) \d+(\.\d+)?m?', value)
    if value_search: 
        rong = re.search('\d+(\.\d+)?', value_search.group()).group()
        
    # dai
    value_search = re.search('(dài|dai) \d+(\.\d+)?m?', value) 
    if value_search: 
        dai = re.search('\d+(\.\d+)?', value_search.group()).group()
        
    return {
        'CHIEU_DAI' : dai,
        'CHIEU_RONG' : rong
    } # fix to other case
    
def duong_truoc_nha_resolver(value):
    value = value.replace(',', '.')
    value = re.sub(r"(\d+)m(\d+)", r"\1.\2", value)
    
    return re.search('\d+(\.\d+)?', value).group()

def dich_vu_resolver(string): 
    lst = [] 
    # school
    if re.search('(trường|đại học|tiểu học|cấp \d+|đh)', string):
        lst.append('trường học')  
    # market
    if 'chợ' in string: 
        lst.append('chợ')  
    # supermarket + mart 
    if re.search('(tttm|siêu thị|trung tâm thương mại|mart|bigc)', string): 
        lst.append('siêu thị')     
    # hospital 
    if re.search('(bv|bệnh viện|trung tâm y tế|trạm y tế)', string):
        lst.append('bệnh viện')
    # park
    if 'công viên' in string: 
        lst.append('công viên')
    # airport
    if 'sân bay' in string: 
        lst.append('sân bay')
    # station
    if re.search('(bx|bxe|bến xe)', string): 
        lst.append('bến xe')

    lst = sorted(lst)
    return ', '.join(lst) 

def gia_resolver(value): 
    value = value.replace(',', '.')
    search = re.search('\d+(\.\d+)?\s?(ty|tỷ)\s?(\d+)?', value)
    
    price = None
    if search: 
        v = search.group() 
        if 'ty' in v: 
            v = v.split('ty')
        elif 'tỷ' in v: 
            v = v.split('tỷ')
            
        stack = [i.strip() for i in v if i.strip().isdigit()]
        v = stack
        
        price = float(v[0].strip()) * 1000000000 # ty 
        
        if len(v) > 1:
            # cal trieu
            if re.search("(triệu|trieu|tr)", value) or len(v[1])>1:
                num = float(re.search('\d+', v[1]).group())
                price += num * 1000000
            else: 
                price += int(v[1]) * 100000000
        return price
    
    search = re.search('(triệu|trieu|tr|ty|tỷ)', value)
    if search is None: 
        price = float(re.search('\d+(\.\d+)?', value).group()) * 1000000000
    elif search and 'ty' not in value and 'tỷ' not in value: # trieu
        price = float(re.search('\d+(\.\d+)?', value).group()) * 1000000
    return price if price != None else value

def so_tang_resolver(value):
    value = value.replace(',', '.')
    num = 0 
    if 'gác' in value: 
        g_vl = re.search('(\d+)? gác', value).group()
        num += 0.5
        value = value.replace(g_vl, '')
    
    if 'trệt' in value: 
        g_vl = re.search("\d+ trệt", value).group()
        value = value.replace(g_vl, '')
        num += 1
    
    # find num of floor 
    count = float(re.search('\d+(\.\d+)?', value).group())
    num += count
    return num

def vi_tri_resolver(value): 
    # kiet 
    if re.search("(kiệt|hẻm|ra (mặt tiền|mt)|sau lưng (mặt tiền|mt)|kiet)", value):
        return 'kiệt'
    
    elif re.search("(mặt tiền|mt|mat tien)", value):
        return 'mặt tiền'
    
def so_phong_ngu_resolver(value):
    return re.search('\d+', value).group()

def toilet_resolver(value):
    return re.search('\d+', value).group()

def song_resolver(value): 
    
    if re.search('view( nhìn| hướng| trực diện)?( ra)? sông', value): 
        return 'view sông'

    elif re.search('(ven|dọc|mặt|mặt tiền|cạnh)( bờ)? sông', value):
        return 'ven sông'

    # distance
    elif re.search('\d+\s?(m|km)', value):
        value = re.search('\d+\s?(m|km)', value).group()
        if 'km' in value: 
            return "cách sông " + str(int(value.strip('km').strip())*1000) + 'm'
        else: 
            return "cách sông " + value.strip('m').strip() + 'm'
        
    # time 
    elif re.search('\d+(\.)?(\d+)?\s?(phút|p)?', value):
        value = re.search('\d+(\.)?(\d+)?\s?(phút|p)?', value).group()
        minutes = re.search('\d+(\.)?(\d+)?', value).group() 
        return "cách sông " + str(minutes) + ' phút'
    
    return value