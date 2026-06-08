from openai import OpenAI

def call_zhipu(prompt: str, api_key: str) -> str:
    """调用智谱AI API（OpenAI兼容接口）"""
    client = OpenAI(
        api_key=api_key,
        base_url="https://open.bigmodel.cn/api/paas/v4/"
    )
    response = client.chat.completions.create(
        model="glm-4-flash",   # 速度快、便宜，批改效果也很好
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return response.choices[0].message.content