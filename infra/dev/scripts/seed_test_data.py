#!/usr/bin/env python3
"""
Script de Seed de Datos de Prueba para Enterprise AI Platform

Este script carga documentos de prueba (públicos y privados) en la base de datos
vectorial para poder probar el sistema RAG completo.

Uso:
    python seed_test_data.py

Requisitos:
    - PostgreSQL con pgvector corriendo
    - OpenAI API Key configurada
    - pip install psycopg2-binary openai python-dotenv
"""

import os
import sys
from datetime import datetime

try:
    import psycopg2
    from psycopg2.extras import Json
    from openai import OpenAI
except ImportError:
    print("Error: Dependencias no instaladas.")
    print("Ejecuta: pip install psycopg2-binary openai python-dotenv")
    sys.exit(1)

# Configuración desde variables de entorno
DB_HOST = os.getenv("PGVECTOR_HOST", "localhost")
DB_PORT = os.getenv("PGVECTOR_PORT", "5432")
DB_NAME = os.getenv("PGVECTOR_DATABASE", "eai_platform")
DB_USER = os.getenv("PGVECTOR_USER", "eai_user")
DB_PASSWORD = os.getenv("PGVECTOR_PASSWORD", "eai_dev_password")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "text-embedding-3-small")

# ============================================================================
# DOCUMENTOS DE PRUEBA
# ============================================================================

# Documentos PÚBLICOS (sobre cocina y alimentación)
PUBLIC_DOCUMENTS = [
    {
        "title": "Receta de Paella Valenciana",
        "content": """
La paella valenciana es uno de los platos más emblemáticos de la gastronomía española.
Originaria de Valencia, esta receta tradicional combina arroz con pollo, conejo, 
judías verdes (bajoqueta y ferraura), garrofón, tomate, aceite de oliva, azafrán y romero.

Ingredientes para 4 personas:
- 400g de arroz bomba
- 300g de pollo troceado
- 200g de conejo troceado
- 100g de judías verdes
- 100g de garrofón
- 1 tomate rallado
- Azafrán al gusto
- 1 litro de caldo de pollo
- Aceite de oliva virgen extra
- Sal y romero

Preparación:
1. Calentar aceite en la paellera y dorar la carne
2. Añadir las verduras y sofreír
3. Incorporar el tomate y cocinar hasta que oscurezca
4. Añadir el agua/caldo y dejar hervir 20 minutos
5. Agregar el arroz y el azafrán, cocinar 18-20 minutos
6. Dejar reposar 5 minutos antes de servir

La paella debe tener el característico "socarrat" en el fondo, una capa crujiente 
de arroz que es muy apreciada por los valencianos.
        """,
        "source": "Libro de Cocina Tradicional Española",
    },
    {
        "title": "Técnicas de Corte en Cocina Profesional",
        "content": """
Las técnicas de corte son fundamentales en la cocina profesional. Un buen corte 
no solo mejora la presentación, sino que también asegura una cocción uniforme.

Principales tipos de corte:

JULIANA: Tiras finas de aproximadamente 5cm x 2mm. Ideal para verduras en salteados.

BRUNOISE: Cubos pequeños de 2-3mm. Se usa para bases de salsas y decoración.

CHIFFONADE: Corte en tiras muy finas para hojas verdes como albahaca o espinacas.

MIREPOIX: Cubos medianos de 1cm para bases aromáticas (zanahoria, cebolla, apio).

CONCASSÉ: Tomate pelado, sin semillas y cortado en cubos.

TORNEADO: Corte decorativo en forma de barril para patatas y zanahorias.

Consejos para un buen corte:
- Mantener los cuchillos bien afilados
- Usar tabla de corte estable
- Aplicar la técnica de "garra" para proteger los dedos
- Practicar regularmente para mejorar velocidad y precisión
        """,
        "source": "Manual de Técnicas Culinarias",
    },
    {
        "title": "Historia del Chocolate",
        "content": """
El chocolate tiene una historia fascinante que se remonta a las civilizaciones 
mesoamericanas. Los mayas y aztecas consideraban el cacao como un regalo de los dioses.

Orígenes:
Los olmecas fueron probablemente los primeros en cultivar cacao hace más de 3000 años.
Los mayas preparaban una bebida amarga llamada "xocolatl" mezclada con chile y especias.
Para los aztecas, los granos de cacao eran tan valiosos que se usaban como moneda.

Llegada a Europa:
Hernán Cortés llevó el cacao a España en 1528. Los españoles añadieron azúcar y 
vainilla, creando una bebida más dulce que se popularizó en las cortes europeas.

El chocolate moderno:
- 1828: Van Houten inventa el proceso de prensado del cacao
- 1847: Joseph Fry crea la primera tableta de chocolate
- 1875: Daniel Peter y Henri Nestlé desarrollan el chocolate con leche
- 1879: Rodolphe Lindt inventa el conchado

Hoy el chocolate es uno de los alimentos más consumidos del mundo, con Suiza, 
Bélgica y Francia liderando la producción de chocolate gourmet.
        """,
        "source": "Enciclopedia Gastronómica",
    },
]

# Documentos PRIVADOS (información técnica/académica)
PRIVATE_DOCUMENTS = [
    {
        "title": "Manual de Mantenimiento de Motores Diesel",
        "content": """
MANUAL TÉCNICO DE MANTENIMIENTO PREVENTIVO - MOTORES DIESEL INDUSTRIALES

1. INTRODUCCIÓN
Este manual describe los procedimientos de mantenimiento preventivo para motores 
diesel de aplicación industrial, con potencias entre 50 y 500 HP.

2. PROGRAMA DE MANTENIMIENTO

Cada 250 horas de operación:
- Verificar nivel de aceite del motor
- Revisar filtro de aire (limpiar o reemplazar)
- Inspeccionar mangueras y conexiones
- Verificar tensión de correas

Cada 500 horas de operación:
- Cambio de aceite y filtro
- Reemplazar filtro de combustible
- Verificar sistema de enfriamiento
- Inspeccionar inyectores

Cada 1000 horas de operación:
- Ajuste de válvulas
- Verificar compresión de cilindros
- Inspección del turbocompresor
- Análisis de aceite usado

3. ESPECIFICACIONES DE ACEITE
Usar aceite API CI-4 o superior. Viscosidad recomendada: 15W-40 para climas 
templados, 10W-30 para climas fríos.

4. SOLUCIÓN DE PROBLEMAS COMUNES
- Motor no arranca: Verificar combustible, batería, precalentadores
- Humo negro excesivo: Revisar filtro de aire, inyectores
- Sobrecalentamiento: Verificar nivel de refrigerante, termostato, radiador
        """,
        "source": "Manual Técnico Industrial - Confidencial",
    },
    {
        "title": "Fundamentos de Programación Orientada a Objetos",
        "content": """
PROGRAMACIÓN ORIENTADA A OBJETOS (POO) - CONCEPTOS FUNDAMENTALES

La Programación Orientada a Objetos es un paradigma de programación que organiza 
el código en "objetos" que contienen datos y comportamiento.

PILARES DE LA POO:

1. ENCAPSULAMIENTO
Ocultar los detalles internos de un objeto y exponer solo lo necesario.
- Atributos privados
- Métodos públicos (getters/setters)
- Protección de datos

2. HERENCIA
Permite crear nuevas clases basadas en clases existentes.
- Clase padre (superclase)
- Clase hija (subclase)
- Reutilización de código
- Jerarquías de clases

3. POLIMORFISMO
Capacidad de objetos de diferentes clases de responder al mismo mensaje.
- Sobrecarga de métodos
- Sobreescritura de métodos
- Interfaces

4. ABSTRACCIÓN
Representar conceptos esenciales sin incluir detalles de implementación.
- Clases abstractas
- Interfaces
- Modelos simplificados

EJEMPLO EN PYTHON:
```python
class Animal:
    def __init__(self, nombre):
        self._nombre = nombre
    
    def hablar(self):
        raise NotImplementedError

class Perro(Animal):
    def hablar(self):
        return f"{self._nombre} dice: Guau!"
```

La POO facilita el mantenimiento, la reutilización y la escalabilidad del código.
        """,
        "source": "Libro Universitario de Programación",
    },
    {
        "title": "Análisis de Circuitos Eléctricos",
        "content": """
ANÁLISIS DE CIRCUITOS ELÉCTRICOS - LEYES FUNDAMENTALES

1. LEY DE OHM
La corriente que circula por un conductor es directamente proporcional a la 
tensión e inversamente proporcional a la resistencia.

V = I × R

Donde:
- V = Voltaje (Voltios)
- I = Corriente (Amperios)
- R = Resistencia (Ohmios)

2. LEYES DE KIRCHHOFF

Ley de Corrientes (LCK):
La suma algebraica de las corrientes en un nodo es igual a cero.
∑I = 0

Ley de Voltajes (LVK):
La suma algebraica de los voltajes en un lazo cerrado es igual a cero.
∑V = 0

3. POTENCIA ELÉCTRICA
P = V × I = I² × R = V² / R

Unidad: Watts (W)

4. CIRCUITOS EN SERIE
- La corriente es la misma en todos los elementos
- Rt = R1 + R2 + R3 + ...
- Vt = V1 + V2 + V3 + ...

5. CIRCUITOS EN PARALELO
- El voltaje es el mismo en todos los elementos
- 1/Rt = 1/R1 + 1/R2 + 1/R3 + ...
- It = I1 + I2 + I3 + ...

Estas leyes son fundamentales para el análisis y diseño de cualquier circuito 
eléctrico, desde simples hasta sistemas complejos.
        """,
        "source": "Manual de Ingeniería Eléctrica",
    },
]


def get_embedding(text: str, client: OpenAI) -> list[float]:
    """Genera embedding para un texto usando OpenAI."""
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text[:8000]  # Limitar longitud
    )
    return response.data[0].embedding


def get_connection():
    """Crea conexión a PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def seed_documents(documents: list[dict], doc_type: str, client: OpenAI, conn):
    """Inserta documentos en la base de datos."""
    cursor = conn.cursor()
    
    for doc in documents:
        print(f"  Procesando: {doc['title'][:50]}...")
        
        # Generar embedding
        full_text = f"{doc['title']}\n\n{doc['content']}"
        embedding = get_embedding(full_text, client)
        
        # Metadata con el tipo de documento (public/private)
        metadata = {
            "title": doc["title"],
            "source": doc["source"],
            "description": doc_type,  # 'public' o 'private'
            "indexed_at": datetime.now().isoformat(),
        }
        
        # Insertar en la base de datos
        cursor.execute(
            """
            insert into documents (content, embedding, metadata)
            values (%s, %s, %s)
            """,
            (doc["content"].strip(), embedding, Json(metadata))
        )
    
    conn.commit()
    cursor.close()


def clear_documents(conn):
    """Elimina todos los documentos existentes."""
    cursor = conn.cursor()
    cursor.execute("delete from documents")
    conn.commit()
    cursor.close()
    print("✓ Documentos anteriores eliminados")


def main():
    print("=" * 60)
    print("Enterprise AI Platform - Seed de Datos de Prueba")
    print("=" * 60)
    
    # Verificar API Key
    if not OPENAI_API_KEY:
        print("\n❌ Error: OPENAI_API_KEY no está configurada")
        print("Configura la variable de entorno antes de ejecutar el script")
        sys.exit(1)
    
    print(f"\n📊 Configuración:")
    print(f"   - Host: {DB_HOST}:{DB_PORT}")
    print(f"   - Database: {DB_NAME}")
    print(f"   - Embedding Model: {EMBEDDING_MODEL}")
    
    # Conectar a la base de datos
    print("\n🔌 Conectando a PostgreSQL...")
    try:
        conn = get_connection()
        print("✓ Conexión exitosa")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        sys.exit(1)
    
    # Inicializar cliente OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)
    
    # Limpiar documentos existentes
    print("\n🗑️  Limpiando documentos existentes...")
    clear_documents(conn)
    
    # Insertar documentos públicos
    print(f"\n📄 Insertando {len(PUBLIC_DOCUMENTS)} documentos PÚBLICOS...")
    seed_documents(PUBLIC_DOCUMENTS, "public", client, conn)
    print(f"✓ {len(PUBLIC_DOCUMENTS)} documentos públicos insertados")
    
    # Insertar documentos privados
    print(f"\n🔒 Insertando {len(PRIVATE_DOCUMENTS)} documentos PRIVADOS...")
    seed_documents(PRIVATE_DOCUMENTS, "private", client, conn)
    print(f"✓ {len(PRIVATE_DOCUMENTS)} documentos privados insertados")
    
    # Verificar inserción
    cursor = conn.cursor()
    cursor.execute("select count(*), metadata->>'description' from documents group by metadata->>'description'")
    results = cursor.fetchall()
    cursor.close()
    
    print("\n📊 Resumen de documentos:")
    for count, doc_type in results:
        print(f"   - {doc_type}: {count} documentos")
    
    conn.close()
    
    print("\n" + "=" * 60)
    print("✅ Seed completado exitosamente!")
    print("=" * 60)
    print("\n🧪 Ahora puedes probar el sistema:")
    print("   - Usuario público (public@demo.local): Solo puede ver info de cocina")
    print("   - Usuario privado (private@demo.local): Puede ver toda la información")
    print("\n📝 Ejemplos de consultas:")
    print("   PÚBLICAS: '¿Cómo se hace la paella?', 'Técnicas de corte en cocina'")
    print("   PRIVADAS: 'Mantenimiento de motores diesel', 'Qué es POO en programación'")


if __name__ == "__main__":
    main()
