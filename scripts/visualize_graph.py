from src.application.graphs.rag_graph import build_rag_graph

def main():
    graph = build_rag_graph()
    mermaid_str = graph.get_graph().draw_mermaid()
    print("--- Mermaid Code ---")
    print(mermaid_str)
    
    # Intenta generar un PNG
    try:
        png_bytes = graph.get_graph().draw_mermaid_png()
        with open("rag_graph.png", "wb") as f:
            f.write(png_bytes)
        print("\n[+] saved rag_graph.png successfully!")
    except Exception as e:
        print("\n[-] Could not generate PNG. Error:", e)

if __name__ == "__main__":
    main()
