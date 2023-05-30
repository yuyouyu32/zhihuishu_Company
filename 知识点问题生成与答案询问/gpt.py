
import requests
import json

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
