"""
Friendship Timeline Service
- Hierarchical Year and Month tree
- Message counts, active days, and memory markers per month
- First message ID mapping for 1-click jumping
"""

from typing import List, Dict, Any
from backend.database import get_db_connection

MONTH_NAMES = [
    "", "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]


def get_timeline_tree() -> List[Dict[str, Any]]:
    """Build a nested Year -> Month timeline structure."""
    conn = get_db_connection()

    # Query monthly aggregation
    rows = conn.execute("""
        SELECT 
            substr(m.iso_date, 1, 4) as year,
            substr(m.iso_date, 6, 2) as month_num,
            substr(m.iso_date, 1, 7) as year_month,
            COUNT(m.id) as total_messages,
            SUM(m.is_vinu) as vinu_messages,
            SUM(m.is_bhumi) as bhumi_messages,
            COUNT(DISTINCT m.iso_date) as active_days,
            MIN(m.id) as first_message_id,
            MAX(m.id) as last_message_id,
            COUNT(mem.id) as memory_count
        FROM messages m
        LEFT JOIN memories mem ON m.id = mem.message_id
        WHERE m.iso_date IS NOT NULL AND m.iso_date != ''
        GROUP BY year_month
        ORDER BY year_month ASC
    """).fetchall()
    conn.close()

    years_map: Dict[str, Dict[str, Any]] = {}

    for r in rows:
        year = r["year"]
        month_idx = int(r["month_num"])
        month_name = MONTH_NAMES[month_idx] if 1 <= month_idx <= 12 else r["month_num"]

        if year not in years_map:
            years_map[year] = {
                "year": year,
                "total_messages": 0,
                "active_days": 0,
                "memory_count": 0,
                "months": []
            }

        month_data = {
            "year_month": r["year_month"],
            "month_num": r["month_num"],
            "month_name": month_name,
            "total_messages": r["total_messages"],
            "vinu_messages": r["vinu_messages"] or 0,
            "bhumi_messages": r["bhumi_messages"] or 0,
            "active_days": r["active_days"],
            "memory_count": r["memory_count"],
            "first_message_id": r["first_message_id"],
            "last_message_id": r["last_message_id"]
        }

        years_map[year]["total_messages"] += r["total_messages"]
        years_map[year]["active_days"] += r["active_days"]
        years_map[year]["memory_count"] += r["memory_count"]
        years_map[year]["months"].append(month_data)

    return list(years_map.values())
