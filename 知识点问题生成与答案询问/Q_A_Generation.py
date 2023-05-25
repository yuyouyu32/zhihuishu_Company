import pandas as pd
import os
import json
import requests
import time
from tqdm import tqdm

url = "https://api.openai.com/v1/completions"
headers = {'content-type': 'application/json',
           'Authorization': 'Bearer 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'}

# 本地VPN
temp_proxy = {"https": "http://127.0.0.1:7890", "http": "http://127.0.0.1:7890"}
# 目前需要设置代理才可以访问 api 注意修改端口
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"



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


def generate_string_from_csv(csv_file_path, log_path):
    # 读取 CSV 文件并将其转换为 DataFrame
    df = pd.read_csv(csv_file_path)
    df.fillna('_', inplace=True)
    # 遍历 DataFrame 的每一行
    for index, row in tqdm(df.iterrows(), total=len(df)):
        # 获取需要替换的列的值
        # cource_name = row['课程名称']
        chapter_name = row['章名称']
        knowledge_name = row['知识点名称']
        # attribute_name = row['一级属性']
        # print(attribute_name)
        if knowledge_name == '_':
            A = ''
        else:
            for char in {'的', '、', ':', '：'}:
                if char in knowledge_name:
                    A = knowledge_name
                    break
                else:
                    A = None
        if A is None:
            # 构建字符串模板
            string_template = '章：{}，知识点：{}。请结合知识点和章的包含关系（章包含知识点），用学术化语言回答“{}”的标准化命名。你的回答要具备：专业、直接、简洁、唯一、无二义性、无，、：“”等标点符号，且你的回答必须在10字之内完成。e.g.章：妊娠期疾病，知识点：高血压。chatGPT的正确回答：妊娠期高血压。chatGPT的错误回答：高血压可以重命名为妊娠期高血压。'

            generated_string = string_template.format(chapter_name, knowledge_name, knowledge_name)
            df.at[index, 'GeneratedQ'] = generated_string
            A = get_gpt_res(generated_string)['choices'][0]['text'].strip()
            if A.endswith('。') or A.endswith('.'):
                A = A[:-1]
            if len(A) > 15 or ':' in A or '：' in A:
                A = knowledge_name
        df.at[index, 'GPT_answer'] = A
        with open(log_path, 'a') as file:
            file.write(A + '\n')
        df.to_excel('./Data/知识点Answer.xlsx')
    return df

if __name__ == '__main__':
    # 指定 CSV 文件的路径
    csv_file_path = './Data/知识点.csv'

    # 调用函数生成字符串并生成回答
    df = generate_string_from_csv(csv_file_path, './record.log')
    # df.to_excel('./Data/知识点Answer.xlsx')