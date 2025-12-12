import logging

import test
# --- Setup Logging ---
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_agent_routing():
    from app.router import IntentRouter
    router = IntentRouter()
    intent = router.classify("帮我规划下周的减脂饮食计划，每天2500大卡")
    print(intent.intent_type)  # IntentType.DIET_PLAN
    print(intent.entities)     # {'time_period': 'week', 'goal': 'weight_loss', 'calories': {...}}

def test_agent_conductor():
    # 测试 Conductor（异步）
    import asyncio
    from app.conductor import Conductor

    async def main():
        conductor = Conductor(user_id="test_user")
        result = await conductor.run("今天晚餐吃什么？")
        print(result.final_output.to_summary() if result.final_output else "无结果")

    asyncio.run(main())


if __name__ == "__main__":
    test_agent_routing()
    test_agent_conductor()