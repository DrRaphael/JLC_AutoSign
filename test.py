import os

token_list = os.getenv('TOKEN_LIST', 'NOT_SET')
print(f"TOKEN_LIST = {token_list}")   # 若输出 NOT_SET，则说明环境变量不存在