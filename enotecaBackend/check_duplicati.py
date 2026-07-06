import pymysql

conn = pymysql.connect(
    host='enoteca-mysql.mysql.database.azure.com',
    user='enotecaadmin',
    password='Abcd1234',
    database='enoteca'
)
cursor = conn.cursor()
cursor.execute("""
    SELECT nome, produttore, annata, COUNT(*) as cnt
    FROM vini
    GROUP BY nome, produttore, annata
    HAVING cnt > 1
""")
for row in cursor.fetchall():
    print(row)


cursor.execute("SELECT COUNT(*) FROM vini")
totale = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM (SELECT DISTINCT nome, produttore, annata FROM vini) as unici")
unici = cursor.fetchone()[0]

print(f"Righe totali: {totale}")
print(f"Vini unici: {unici}")
print(f"Righe duplicate da rimuovere: {totale - unici}")
conn.close()