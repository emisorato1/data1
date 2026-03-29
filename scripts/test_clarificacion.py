import asyncio
from src.application.graphs.rag_graph import build_rag_graph

async def main():
    graph = build_rag_graph()
    queries = ["Quiero cambiar mi tarjeta", "g"]
    
    for q in queries:
        print(f"\n{'='*50}\nConsulta: '{q}'\n")
        state = await graph.ainvoke(
            {"query": q, "messages": []},
            {"configurable": {"thread_id": "test_ambiguous_1"}}
        )
        print("Respuesta:")
        print(state.get("response", "[Error: Sin respuesta]"))
        print(f"\nNeeds clarification: {state.get('needs_clarification')}")

if __name__ == "__main__":
    asyncio.run(main())
