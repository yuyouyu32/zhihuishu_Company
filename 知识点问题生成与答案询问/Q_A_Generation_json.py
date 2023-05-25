import pandas as pd
import os
import json
import requests
from tqdm import tqdm
import ast

url = "https://api.openai.com/v1/completions"
headers = {'content-type': 'application/json',
           'Authorization': 'Bearer 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'}

# 本地VPN
temp_proxy = {"https": "http://127.0.0.1:7890", "http": "http://127.0.0.1:7890"}
# 目前需要设置代理才可以访问 api 注意修改端口
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

# String pattern
KNOWLEDGE = '章：{}，知识点：{}。请结合知识点和章的包含关系（章包含知识点），用学术化语言回答“{}”的标准化命名。你的回答要具备：专业、直接、简洁、唯一、无二义性、无，、：“”等标点符号，且你的回答必须在10字之内完成。e.g.章：妊娠期疾病，知识点：高血压。chatGPT的正确回答：妊娠期高血压。chatGPT的错误回答：高血压可以重命名为妊娠期高血压。'

ATTRIBUTION = '章：{}，知识点：{}，一级属性：{}。请结合属性与知识点和章的包含关系（章包含知识点，知识点包含一级属性），用学术化语言回答“{}”的标准化命名。你的回答必须专业、简洁、无二义性、无，、：“”等标点符号，且你的回答必须在10字之内完成。e.g. 章：昆虫纲，知识点：蝇，一级属性：形态。chatGPT的正确回答：蝇的形态。chatGPT的错误回答：昆虫的形态学。'

def get_gpt_res(Q):
    temp_data = {
        'model': f"text-davinci-003",
        'prompt': Q,
        'temperature': 0.5,
        'top_p': 1,
        'max_tokens': 1024,
        'frequency_penalty': 0,
        'presence_penalty': 0
    }
    res = requests.post(url, data=json.dumps(temp_data), headers=headers, proxies=temp_proxy)
    return res.json()


def check_name(name):
    for char in {'的', '、', ':', '：'}:
        if char in name:
            A = name
            break
        else:
            A = None
    return A

def q_a_generator(row, i, df):
    if row is None:
         return ''
    elif '一级属性' not in row:
        A = check_name(row['知识点'])
        if A is None:
            string_template = KNOWLEDGE
            generated_string = string_template.format(row['章节'], row['知识点'], row['知识点'])
            df.at[i, 'GeneratedQ'] = generated_string
            A = get_gpt_res(generated_string)['choices'][0]['text'].strip()
            if A.endswith('。') or A.endswith('.'):
                A = A[:-1]
            if len(A) > 15 or ':' in A or '：' in A:
                A = row['知识点']
    else:
        A = check_name(row['一级属性'])
        if A is None:
            string_template = ATTRIBUTION
            generated_string = string_template.format(row['章节'], row['知识点'], row['一级属性'], row['一级属性'])
            df.at[i, '生成的问题'] = generated_string
            A = get_gpt_res(generated_string)['choices'][0]['text'].strip()
            if A.endswith('。') or A.endswith('.'):
                A = A[:-1]
            if len(A) > 15 or ':' in A or '：' in A:
                A = row['一级属性']
    return A

def generate_string_from_json(json_file_path, log_path):
    with open(json_file_path, 'r') as file:
            content = file.read()
            data_list = ast.literal_eval(content)
    cur_chaper_name = ''
    cur_know_name = ''
    df = pd.DataFrame()
    new_row = None
    i = -1
    for data in data_list:
        if data["title_level"] == 0:
                cur_chaper_name = data["title"].split('：')[-1]
                continue
        elif data["title_level"] == 1:
                cur_know_name = data['title'].split('：')[-1]
                new_row = {'章节': cur_chaper_name, '知识点': cur_know_name}
                i += 1
                df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
        elif data["title_level"] == 2:
                new_row = {'章节': cur_chaper_name, '知识点': cur_know_name, '一级属性': data['title'].split('：')[-1]}
                i += 1
                df = pd.concat([df, pd.DataFrame(new_row, index=[0])], ignore_index=True)
        df.at[i, '生成的问题'] = ''
        A = q_a_generator(new_row, i, df)
        with open(log_path, 'a') as file:
            file.write(A + '\n')
        df.at[i, '标准化名称'] = A
        df.to_excel('./Data/Answer.xlsx', index=False)
    return df

if __name__ == '__main__':
    # 指定 json 文件的路径
    json_file_path = './Data/Data.json'
    # 调用函数生成字符串并生成回答
    df = generate_string_from_json(json_file_path, './record.log')