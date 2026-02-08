# Frontends

Aplicaciones frontend desarrolladas en TypeScript/JavaScript con React. Contiene **rag-chat**, la interfaz web principal para interactuar con el sistema RAG mediante chat conversacional, y espacio para futuros frontends como paneles de administración. Cada aplicación es independiente con su propio package.json, Dockerfile y puede desplegarse por separado. Se comunican con el backend vía API REST y WebSocket, propagando trace_id para observabilidad end-to-end.


Usamos [assistant-ui](https://github.com/Yonom/assistant-ui) como base para el frontend.

## Getting Started

First, add your langgraph API url and assistant id to `.env.local` file:

```
LANGCHAIN_API_KEY=your_langchain_api_key
LANGGRAPH_API_URL=your_langgraph_api_url
NEXT_PUBLIC_LANGGRAPH_ASSISTANT_ID=your_assistant_id_or_graph_id
```

Then, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:7000](http://localhost:7000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.