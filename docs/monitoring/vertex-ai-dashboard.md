# Dashboard de Costos de Vertex AI (GCP Monitoring)

Este documento describe el dashboard de seguimiento de costos, latencia y uso de modelos Vertex AI, desplegado nativamente en GCP Monitoring como parte del proyecto `itmind-infrastructure`.

## Acceso al Dashboard e Instalación Manual

1. Ingresar a Google Cloud Console.
2. Navegar a **Monitoring** > **Dashboards**.
3. Buscar el dashboard llamado **Vertex AI Costs & Performance**.
4. **Si no existe**, podés importarlo manualmente:
   - Andá a **Dashboards** y hacé clic en **"+ Create Dashboard"**.
   - Arriba a la derecha, hacé clic en el botón **"JSON Editor"**.
   - Copiá y pegá el contenido del archivo `docs/monitoring/vertex-ai-costs-dashboard.json`.
   - Hacé clic en **Apply**.
5. (Opcional) El dashboard se encuentra administrado por Terraform en la spec `INFRA-S5-02`.

## Estructura de Métricas

El dashboard está configurado para explotar métricas nativas de Vertex AI (`aiplatform.googleapis.com/prediction/*`) divididas en las siguientes áreas:

### 1. Peticiones (Requests)
- **Métrica base:** `aiplatform.googleapis.com/prediction/online/total_requests`
- **Filtros:** Agrupado por tipo de modelo (Embedding vs Generation).
- **Propósito:** Entender el volumen de tráfico hacia las APIs de Vertex.

### 2. Consumo de Tokens
- **Métricas base:** 
  - `aiplatform.googleapis.com/prediction/online/tokens_input`
  - `aiplatform.googleapis.com/prediction/online/tokens_output`
- **Agregación:** Suma por hora y por día.
- **Propósito:** Conocer el consumo real de tokens (input y output), que es el vector principal de facturación.

### 3. Latencia
- **Métrica base:** `aiplatform.googleapis.com/prediction/online/latencies`
- **Agregación:** Percentiles `p50`, `p95` y `p99`.
- **Propósito:** Medir la experiencia del usuario y detectar degradación de servicio (especialmente importante para modelos generativos pesados).

### 4. Costo Estimado Diari
- **Métrica base:** *Métrica calculada (MQL)*.
- **Lógica:** Multiplica el total de `tokens_input` y `tokens_output` por el pricing público actual de los modelos utilizados en el proyecto (por ejemplo, Gemini 1.5 Pro/Flash y text-embedding).
- **Propósito:** Aproximar el gasto incurrido al día, ya que GCP Billing puede tener demora en reflejar costos diarios a nivel de granularidad fina por modelo.

## Sistema de Alertas

Están configuradas políticas de alertas automáticas (Alert Policies) en GCP que notifican al equipo en caso de anomalías:

1. **Alerta de Sobrecosto:**
   - **Condición:** Si el "Costo diario estimado" excede el *Threshold* de presupuesto diario configurado.
   - **Acción:** Evaluar el volumen de peticiones o un posible ataque de agotamiento de recursos.

2. **Alerta de Latencia Degradada:**
   - **Condición:** Si la latencia *p95* supera los **10 segundos** de manera sostenida.
   - **Acción:** Revisar estado de los endpoints de Vertex AI, timeouts en el backend (FastAPI), y tamaño de contexto enviado en los prompts.

## Referencias

- Spec de infraestructura (Terraform): `INFRA-S5-02`
- Documentación de GCP Monitoring para Vertex: [Google Cloud Docs](https://cloud.google.com/vertex-ai/docs/monitoring)