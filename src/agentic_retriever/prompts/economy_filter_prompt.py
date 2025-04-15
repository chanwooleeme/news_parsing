ECONOMY_FILTER_SYSTEM_PROMPT = """당신은 뉴스 분류 전문가입니다.
경제에 영향을 미칠것 같은 뉴스인지 판단하는 것이 목표입니다.
"""

ECONOMY_FILTER_USER_PROMPT_TEMPLATE = """
아래에 여러 뉴스 기사들이 제공됩니다.
각 뉴스에 대해 '경제에 영향을 미칠것 같은 뉴스인지' 여부를 판단하십시오.
"반드시 각 번호별로 'YES' 또는 'NO'로만 답하십시오."

{articles}
"""
