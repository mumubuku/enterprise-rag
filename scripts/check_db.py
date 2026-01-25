import psycopg2
from psycopg2 import sql
import os
from dotenv import load_dotenv

load_dotenv('.env.local')

DB_HOST = os.getenv('DB_HOST')
DB_PORT = os.getenv('DB_PORT')
DB_USER = os.getenv('DB_USER')
DB_PASSWORD = os.getenv('DB_PASSWORD')
DB_NAME = os.getenv('DB_NAME')

try:
    conn = psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME
    )
    conn.autocommit = True
    cursor = conn.cursor()

    print(f"成功连接到数据库: {DB_NAME}")
    print("=" * 80)

    cursor.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)
    tables = cursor.fetchall()

    print(f"\n数据库中共有 {len(tables)} 张表:\n")
    for table in tables:
        table_name = table[0]
        print(f"表名: {table_name}")
        print("-" * 80)

        cursor.execute("""
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = %s
            ORDER BY ordinal_position;
        """, (table_name,))

        columns = cursor.fetchall()
        print(f"{'字段名':<30} {'数据类型':<20} {'可空':<10} {'默认值'}")
        print("-" * 80)
        for col in columns:
            col_name, data_type, is_nullable, col_default = col
            nullable = "YES" if is_nullable == "YES" else "NO"
            default_val = str(col_default) if col_default else ""
            print(f"{col_name:<30} {data_type:<20} {nullable:<10} {default_val}")

        print()

    cursor.close()
    conn.close()
    print("数据库连接已关闭")

except Exception as e:
    print(f"连接数据库失败: {e}")