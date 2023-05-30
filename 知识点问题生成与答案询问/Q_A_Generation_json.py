import pandas as pd
import os
import json
import requests
from tqdm import tqdm
import ast

# url = "https://api.openai.com/v1/completions"
# headers = {'content-type': 'application/json',
#            'Authorization': 'Bearer xxx'}

# # 本地VPN
# temp_proxy = {"https": "http://127.0.0.1:7890", "http": "http://127.0.0.1:7890"}
# # 目前需要设置代理才可以访问 api 注意修改端口
# os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
# os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

# String pattern
KNOWLEDGE = '章：{}，知识点：{}。请结合知识点和章的包含关系（章包含知识点），用学术化语言回答“{}”的标准化命名。你的回答要具备：专业、直接、简洁、唯一、无二义性、无，、：“”等标点符号，且你的回答必须在10字之内完成。e.g.章：妊娠期疾病，知识点：高血压。正确答案：妊娠期高血压。错误答案：高血压可以重命名为妊娠期高血压。'

ATTRIBUTION_1 = '章：{}，知识点：{}，一级属性：{}。请结合属性与知识点和章的包含关系（章包含知识点，知识点包含一级属性），用学术化语言回答“{}”的标准化命名。你的回答必须专业、简洁、无二义性、无，、：“”等标点符号，且你的回答必须在10字之内完成。e.g. 章：昆虫纲，知识点：蝇，一级属性：形态。正确答案：蝇的形态。错误答案：昆虫的形态学。'

ATTRIBUTION_2 = '章：{}，知识点：{}，一级属性：{}，二级属性：{}。请结合属性与知识点和章的包含关系（章包含知识点，知识点包含一级属性，一级属性包含二级属性），用学术化语言回答“{}”的标准化命名。你的回答必须专业、简洁、无二义性、无，、：“”等标点符号，且你的回答必须在10字之内完成。e.g. 章：昆虫纲，知识点：蝇，一级属性：形态，二级属性：成虫。正确答案：蝇的成虫的形态。错误答案：昆虫的形态。'

# def get_gpt_res(Q):
#     temp_data = {
#         'model': f"text-davinci-003",
#         'prompt': Q,
#         'temperature': 0.5,
#         'top_p': 1,
#         'max_tokens': 1024,
#         'frequency_penalty': 0,
#         'presence_penalty': 0
#     }
#     res = requests.post(url, data=json.dumps(temp_data), headers=headers, proxies=temp_proxy).json()
#     return res['choices'][0]['text'].strip()

def get_gpt_res(text):
    headers = {
        "Content-Type": 'application/json'
    }
    param ={
        "serviceCode": "SI_KG_PRODUCE",
        "text": text
    }
    ret = requests.post("https://ai-platform-cloud-proxy.zhihuishu.com/ability/gpt/completions", data=json.dumps(param), headers=headers)
    return ret.json()['data'].strip()

def check_name(name):
    for char in {'的', '、', ':', '：'}:
        if char in name:
            A = name
            break
        else:
            A = None
    return A

def delet_useless_word(string):
    string = string.replace('[附]', '')
    string = string.replace('【附】', '')
    # 查找关键词并获取其后面的部分
    if "标准化命名为" in string:
        keyword = "标准化命名为"
    elif "重命名为" in string:
        keyword = "重命名为"
    elif "称为" in string:
        keyword = "称为"
    else:
        keyword = None
    if keyword:
        return string.split(keyword)[1]
    else:
        return string

def q_a_generator(row):
    source = 2
    if row is None:
        return '', 2
    elif '一级属性' not in row:
        A = check_name(row['知识点'])
        if A is None:
            string_template = KNOWLEDGE
            generated_string = string_template.format(row['章节'], row['知识点'], row['知识点'])
            A = delet_useless_word(get_gpt_res(generated_string))
            if A.endswith('。') or A.endswith('.'):
                A = A[:-1]
            if len(A) > 15 or ':' in A or '：' in A:
                A = row['知识点']
            else:
                source = 1
    elif '二级属性' not in row:
        A = check_name(row['一级属性'])
        if A is None:
            string_template = ATTRIBUTION_1
            generated_string = string_template.format(row['章节'], row['知识点'], row['一级属性'], row['一级属性'])
            A = delet_useless_word(get_gpt_res(generated_string))
            if A.endswith('。') or A.endswith('.'):
                A = A[:-1]
            if len(A) > 15 or ':' in A or '：' in A:
                A = row['一级属性']
            else:
                source = 1
    else:
        A = check_name(row['二级属性'])
        if A is None:
            string_template = ATTRIBUTION_2
            generated_string = string_template.format(row['章节'], row['知识点'], row['一级属性'], row['二级属性'], row['二级属性'])
            A = delet_useless_word(get_gpt_res(generated_string))
            if A.endswith('。') or A.endswith('.'):
                A = A[:-1]
            if len(A) > 15 or ':' in A or '：' in A:
                A = row['二级属性']
            else:
                source = 1
    return A, source

def generate_name_from_json(json_file_path, over_write=False):
    with open(json_file_path, 'r') as file:
        content = file.read()
        data = ast.literal_eval(content)
    cur_chaper_name = ''
    cur_know_name = ''
    cur_attr_1 = ''
    for item in tqdm(data['data']):
        if over_write and 'aliaName' in item:
            continue
        if item["level"] == 1:
            cur_chaper_name = item["knowledgeName"]
            item['aliaName'] = []
            continue
        elif item["level"] == 2:
            if not cur_chaper_name: 
                item['aliaName'] = []
                continue
            cur_know_name = item['knowledgeName'] 
            new_row = {'章节': cur_chaper_name, '知识点': cur_know_name}    
        elif item["level"] == 3:
            if not cur_chaper_name or not cur_know_name: 
                item['aliaName'] = []
                continue
            cur_attr_1 = item['knowledgeName']
            new_row = {'章节': cur_chaper_name, '知识点': cur_know_name, '一级属性': cur_attr_1}
        elif item["level"] == 4:
            if not cur_chaper_name or not cur_know_name or not cur_attr_1:
                item['aliaName'] = []
                continue
            new_row = {'章节': cur_chaper_name, '知识点': cur_know_name, '一级属性': cur_attr_1, '二级属性': item['title']}
        else:
            item['aliaName'] = []
            continue
        A, source = q_a_generator(new_row)
        temp_dict = {'Id': item['knowledgeId'], 'sort': 1, 'content': A, 'source': source}
        item['aliaName'] = [temp_dict]
        with open(json_file_path, "w") as json_file:
            json.dump(data, json_file, ensure_ascii=False)
    return data

if __name__ == '__main__':
    # 指定 json 文件的路径
    json_file_path = './Data/response.json'
    # 调用函数生成字符串并生成回答
    new_data = generate_name_from_json(json_file_path, over_write=False)
