import asyncio, json, sys
from typing import Any

# 요청 문장은 실행할 때 인자로 바꿀 수 있다 (기본값은 교재 요청)
QUESTION = sys.argv[1] if len(sys.argv) > 1 else "BUSAN-02 창고의 SKU A-17 재고를 알려 줘"


async def main():
    from langchain_core.tools import tool
    from langchain_core.messages import ToolMessage
    from langchain_ollama import ChatOllama

    @tool
    def get_inventory(sku: str, warehouse_id: str) -> dict[str, Any]:
        """승인된 창고에서 특정 상품의 현재 가용 재고를 읽기 전용으로 조회합니다.
        sku에는 상품 SKU를, warehouse_id에는 SEOUL-01 또는 BUSAN-02만 넣습니다.
        수량을 변경하지 않습니다. INVALID_SKU이면 SKU를 확인해 달라고 물어야 합니다.
        고객이 말한 창고가 SEOUL-01 또는 BUSAN-02와 정확히 일치하지 않으면(예: "부산 3번 창고")
        비슷한 코드로 바꿔 넣지 말고, 호출하지 않은 채 허용된 창고 코드를 물어봅니다."""
        if warehouse_id not in ("SEOUL-01", "BUSAN-02"):
            return {"error": "WAREHOUSE_NOT_ALLOWED"}
        return {"sku": sku, "warehouse_id": warehouse_id,
                "available_quantity": 7, "checked_at": "2026-08-27T01:55:00+09:00"}

    llm = ChatOllama(model="qwen3.5:2b", temperature=0, reasoning=False)
    llm_with_tools = llm.bind_tools([get_inventory])

    print("== 요청 ==")
    print(QUESTION)

    r1 = await llm_with_tools.ainvoke(QUESTION)
    print("[1] 모델의 요청:", [(tc["name"], tc["args"]) for tc in r1.tool_calls])
    if not r1.tool_calls:  # 모델이 도구를 요청하지 않은 경우도 관찰 결과로 남긴다
        print("[1] 도구 요청 없음. 모델의 직접 답:", r1.content[:200])
        return

    result = get_inventory.invoke(r1.tool_calls[0]["args"])
    print("[2] 하네스의 실행 결과:", json.dumps(result, ensure_ascii=False))

    r2 = await llm_with_tools.ainvoke(
        [r1, ToolMessage(content=json.dumps(result, ensure_ascii=False),
                         tool_call_id=r1.tool_calls[0]["id"])])
    print("[3] 결과를 읽은 최종 답:", r2.content[:200])
    if r2.tool_calls:
        print("[3] 모델이 다시 요청한 도구:", [(tc["name"], tc["args"]) for tc in r2.tool_calls])


asyncio.run(main())
