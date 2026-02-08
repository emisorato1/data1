# 1. Iniciar contenedor
docker-compose -f docker-compose.yml up -d
# 2. Crear la base de datos y tablas
docker exec -i rag-postgres psql -U admin -d rag < init.sql
# 3. Verificar que las tablas se hayan creado correctamente
docker exec -it rag-postgres psql -U admin -d rag -c "\dt"
# 4. Conectarse a la base de datos
docker exec -it rag-postgres psql -U admin -d rag   


