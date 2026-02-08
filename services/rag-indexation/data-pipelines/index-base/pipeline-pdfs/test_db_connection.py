import psycopg2
import traceback

try:
    conn = psycopg2.connect(
        host='127.0.0.1', 
        port=5432, 
        dbname='eai_platform', 
        user='eai_user', 
        password='eai_dev_password'
    )
    print('CONNECTED OK')
    conn.close()
except Exception as e:
    print(f'ERROR: {type(e).__name__}')
    print(f'MESSAGE: {str(e)}')
    traceback.print_exc()
