import pymysql

with open('database.sql', 'r', encoding='utf-8') as f:
    sql = f.read()

conn = pymysql.connect(host='localhost', user='root', password='niva', db='delishnex')
cursor = conn.cursor()

# Split the statements (this is a simple split, works for basic SQL dumps)
statements = sql.split(';')
for statement in statements:
    if statement.strip():
        try:
            cursor.execute(statement)
        except Exception as e:
            print(f"Error on: {statement[:50]}... -> {e}")

conn.commit()
conn.close()
print("Database seeded successfully!")
