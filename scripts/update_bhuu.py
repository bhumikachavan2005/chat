import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.database import get_db_connection, init_db
from backend.parser.whatsapp_parser import parse_whatsapp_file
from backend.database import bulk_insert_messages

conn = get_db_connection()
conn.execute("UPDATE messages SET sender_clean = 'Bhuu 🎀' WHERE is_bhumi = 1 OR sender_raw LIKE '%Bhumika%' OR sender_raw LIKE '%Bhumi%'")
conn.commit()

bhuu_count = conn.execute("SELECT COUNT(id) as c FROM messages WHERE sender_clean = 'Bhuu 🎀'").fetchone()["c"]
vinu_count = conn.execute("SELECT COUNT(id) as c FROM messages WHERE sender_clean = 'Vinu 💝🎀'").fetchone()["c"]
total = conn.execute("SELECT COUNT(id) as c FROM messages").fetchone()["c"]
conn.close()

print(f"Total: {total:,} | Vinu: {vinu_count:,} | Bhuu: {bhuu_count:,}")
