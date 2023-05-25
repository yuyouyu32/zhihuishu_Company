
import requests
import json
import os

# 目前需要设置代理才可以访问 api
os.environ["HTTP_PROXY"] = "http://127.0.0.1:7890"
os.environ["HTTPS_PROXY"] = "http://127.0.0.1:7890"

def gpt(text):
    headers = {
        "Content-Type": 'application/json'
    }
    param ={
        "serviceCode": "SI_KG_PRODUCE",
        "text": text
    }
    ret = requests.post("https://ai-platform-cloud-proxy.zhihuishu.com/ability/gpt/completions", data=json.dumps(param), headers=headers)
    return ret.json()


print(gpt("请对胃病的症状做50字左右的描述") )
