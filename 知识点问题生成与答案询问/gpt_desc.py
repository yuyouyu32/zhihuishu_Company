# coding=utf-8
import collections
from collections import defaultdict
import json
import re

import requests
# import openai
import pandas as pd
import os, platform

sys_platform = platform.platform().lower()
root = './data'
map_content_file = os.path.join(root, 'knowledge_map_content.csv')
map_node_attr_file = os.path.join(root, 'node_attrs.csv')
kmc_type_dict = {"map_uid": "str", "content_uid": "str", "content_third_id": "str"}
na_type_dict = {"node_id": "str", "map_uid": 'str', "tree_id": "str", "pid": "str", 'attrs': "str"}

url = "https://api.openai.com/v1/completions"
headers = {'content-type': 'application/json',
           # 自己的key
           'Authorization': 'Bearer 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'}

# 本地VPN
temp_proxy = {"https": "http://127.0.0.1:58591", "http": "http://127.0.0.1:58591"}


def write_file_line(content, res_file):
    with open(res_file, 'a+', encoding='utf-8') as file:
        file.write(content + "\n")


def write_json_line(content, res_file):
    write_file_line(json.dumps(content, ensure_ascii=False), res_file)


def get_gpt_res(temp_text):
    temp_data = {
        'model': f"text-davinci-003",
        'prompt': f"""请给出一下名词或概念的明确定义
示例：
输入：TCP
输出：传输控制协议（Transmission Control Protocol，TCP）是一种面向连接的、可靠的、基于字节流的运输层通信协议，通常由IETF的RFC 793说明。在简化的计算机网络OSI模型中，它完成运输层所指定的功能。
输入：{temp_text}
输出:
""",
        'temperature': 0.5,
        'top_p': 1,
        'max_tokens': 1024,
        'frequency_penalty': 0,
        'presence_penalty': 0
    }
    # print(temp_text)
    res = requests.post(url, data=json.dumps(temp_data), headers=headers, proxies=temp_proxy)
    # print(res.json())
    return res.json()


if __name__ == "__main__":
    print(get_gpt_res("巧克力"))
