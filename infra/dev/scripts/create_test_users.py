#!/usr/bin/env python3
"""
Script para crear usuarios de prueba en Enterprise AI Platform

Este script crea usuarios de prueba directamente en la base de datos,
permitiendo asignar roles específicos (public, private, admin).

Uso:
    python create_test_users.py

Requisitos:
    - PostgreSQL corriendo
    - pip install psycopg2-binary argon2-cffi
"""

import os
import sys

try:
    import psycopg2
    from argon2 import PasswordHasher
except ImportError:
    print("Error: Dependencias no instaladas.")
    print("Ejecuta: pip install psycopg2-binary argon2-cffi")
    sys.exit(1)

# Configuración
DB_HOST = os.getenv("PGVECTOR_HOST", "localhost")
DB_PORT = os.getenv("PGVECTOR_PORT", "5432")
DB_NAME = os.getenv("PGVECTOR_DATABASE", "eai_platform")
DB_USER = os.getenv("PGVECTOR_USER", "eai_user")
DB_PASSWORD = os.getenv("PGVECTOR_PASSWORD", "eai_dev_password")

# Hasher de contraseñas (mismo que usa el API)
ph = PasswordHasher()

# Usuarios de prueba a crear
TEST_USERS = [
    {
        "email": "public@demo.local",
        "password": "password123",
        "role_name": "public",
        "description": "Usuario con acceso PÚBLICO (solo info de cocina)",
    },
    {
        "email": "private@demo.local", 
        "password": "password123",
        "role_name": "private",
        "description": "Usuario con acceso PRIVADO (toda la información)",
    },
    {
        "email": "admin@demo.local",
        "password": "password123",
        "role_name": "admin",
        "description": "Usuario administrador",
    },
]

TENANT_ID = "00000000-0000-0000-0000-000000000001"


def get_connection():
    """Crea conexión a PostgreSQL."""
    return psycopg2.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
    )


def create_user(conn, email: str, password: str, role_name: str) -> bool:
    """Crea un usuario en la base de datos."""
    cursor = conn.cursor()
    
    # Verificar si el usuario ya existe
    cursor.execute("select id from users where email = %s", (email,))
    if cursor.fetchone():
        cursor.close()
        return False  # Ya existe
    
    # Obtener el role_id
    cursor.execute("select id from roles where name = %s", (role_name,))
    role_row = cursor.fetchone()
    if not role_row:
        cursor.close()
        raise ValueError(f"Rol '{role_name}' no encontrado")
    role_id = role_row[0]
    
    # Hash de la contraseña
    password_hash = ph.hash(password)
    
    # Insertar usuario
    cursor.execute(
        """
        insert into users (email, password_hash, tenant_id, role_id, is_active)
        values (%s, %s, %s, %s, true)
        """,
        (email, password_hash, TENANT_ID, role_id)
    )
    
    conn.commit()
    cursor.close()
    return True


def main():
    print("=" * 60)
    print("Enterprise AI Platform - Crear Usuarios de Prueba")
    print("=" * 60)
    
    print(f"\n📊 Configuración:")
    print(f"   - Host: {DB_HOST}:{DB_PORT}")
    print(f"   - Database: {DB_NAME}")
    
    print("\n🔌 Conectando a PostgreSQL...")
    try:
        conn = get_connection()
        print("✓ Conexión exitosa")
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        print("\nAsegúrate de que PostgreSQL esté corriendo:")
        print("  docker-compose up -d postgres")
        sys.exit(1)
    
    print("\n👥 Creando usuarios de prueba...\n")
    
    for user in TEST_USERS:
        email = user["email"]
        password = user["password"]
        role_name = user["role_name"]
        desc = user["description"]
        
        print(f"  📧 {email} (rol: {role_name})")
        print(f"     {desc}")
        
        try:
            created = create_user(conn, email, password, role_name)
            if created:
                print(f"     ✓ Creado exitosamente")
            else:
                print(f"     ⚠ Ya existe (OK)")
        except Exception as e:
            print(f"     ❌ Error: {e}")
        
        print()
    
    conn.close()
    
    print("=" * 60)
    print("✅ Proceso completado!")
    print("=" * 60)
    print("\n🔐 Credenciales de prueba:")
    print("   ┌─────────────────────────┬──────────────┬─────────────┐")
    print("   │ Email                   │ Password     │ Acceso      │")
    print("   ├─────────────────────────┼──────────────┼─────────────┤")
    print("   │ public@demo.local       │ password123  │ Público     │")
    print("   │ private@demo.local      │ password123  │ Privado     │")
    print("   │ admin@demo.local        │ password123  │ Admin       │")
    print("   └─────────────────────────┴──────────────┴─────────────┘")
    print("\n💡 El usuario 'public' solo puede ver información de cocina.")
    print("   El usuario 'private' puede ver toda la información.")


if __name__ == "__main__":
    main()
