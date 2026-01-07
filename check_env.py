"""检查环境变量配置"""

import os

print("=" * 60)
print("环境变量检查")
print("=" * 60)
print()

# 检查 LLM 相关环境变量
llm_provider = os.getenv("LLM_PROVIDER", "未设置")
deepseek_key = os.getenv("DEEPSEEK_API_KEY", "未设置")
openai_key = os.getenv("OPENAI_API_KEY", "未设置")
llm_model = os.getenv("LLM_MODEL", "未设置")

print(f"LLM_PROVIDER: {llm_provider}")
print(f"LLM_MODEL: {llm_model}")
print(f"DEEPSEEK_API_KEY: {'已设置' if deepseek_key != '未设置' else '未设置'}")
print(f"OPENAI_API_KEY: {'已设置' if openai_key != '未设置' else '未设置'}")
print()

# 判断实际会使用哪个
if llm_provider.lower() == "deepseek" or (llm_provider == "未设置" and deepseek_key != "未设置"):
    print("✅ 将使用: DeepSeek API")
    if llm_provider == "未设置":
        print("   (因为 LLM_PROVIDER 未设置，默认使用 deepseek)")
elif llm_provider.lower() == "openai" or (llm_provider == "未设置" and deepseek_key == "未设置" and openai_key != "未设置"):
    print("✅ 将使用: OpenAI API")
    if llm_provider == "未设置":
        print("   (因为 LLM_PROVIDER 未设置，且只有 OPENAI_API_KEY)")
else:
    print("⚠️  无法确定，请检查配置")

print()
print("=" * 60)
