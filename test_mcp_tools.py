"""测试 MCP 工具调用"""
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

async def test_weather():
    """测试天气查询"""
    try:
        from tools.weather_tool import WeatherTool
        
        tool = WeatherTool()
        print("=" * 50)
        print("天气查询工具测试")
        print("=" * 50)
        print(f"服务类型: {tool.service_type}")
        print(f"使用模拟数据: {tool.use_mock}")
        if tool.qweather_key:
            print(f"和风天气 Key: 已配置")
        if tool.openweather_key:
            print(f"OpenWeatherMap Key: 已配置")
        print()
        
        # 测试查询
        print("测试查询：北京天气")
        result = await tool.query_weather("北京")
        print(f"查询结果: {result.get('success', False)}")
        if result.get('success'):
            print(f"城市: {result.get('city', 'N/A')}")
            print(f"温度: {result.get('temperature', 'N/A')}°C")
            print(f"天气: {result.get('description', 'N/A')}")
            print(f"湿度: {result.get('humidity', 'N/A')}%")
        print(f"数据来源: {result.get('source', result.get('note', '未知'))}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

async def test_amap():
    """测试高德地图查询"""
    try:
        from tools.amap_tool import AmapTool
        
        tool = AmapTool()
        print("\n" + "=" * 50)
        print("高德地图地址查询工具测试")
        print("=" * 50)
        print(f"API Key 已配置: {not tool.use_mock}")
        print(f"使用模拟数据: {tool.use_mock}")
        print()
        
        # 测试地理编码
        print("测试地理编码：北京市朝阳区")
        result = await tool.geocode("北京市朝阳区", "北京")
        print(f"查询结果: {result.get('success', False)}")
        if result.get('location'):
            print(f"位置: {result['location']}")
        print(f"数据来源: {result.get('note', '真实API' if not tool.use_mock else '模拟数据')}")
        
    except Exception as e:
        print(f"测试失败: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """主测试函数"""
    await test_weather()
    await test_amap()
    print("\n" + "=" * 50)
    print("测试完成")
    print("=" * 50)

if __name__ == "__main__":
    asyncio.run(main())
