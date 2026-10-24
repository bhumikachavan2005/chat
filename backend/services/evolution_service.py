"""
Friendship Evolution Service
- Period comparison engine (e.g. 2025 vs 2026 or custom date bounds)
- Measures changes in frequency, balance, vocabulary, active hours, and emojis
"""

import json
import re
from collections import Counter
from typing import Dict, Any, Optional
from backend.database import get_db_connection
from backend.services.stats_service import STOP_WORDS


def get_period_stats(start_date: str, end_date: str) -> Dict[str, Any]:
    """Calculate aggregated metrics for a specific date window."""
    conn = get_db_connection()

    total_msgs = conn.execute("""
        SELECT COUNT(*) as c FROM messages 
        WHERE iso_date >= ? AND iso_date <= ?
    """, (start_date, end_date)).fetchone()["c"]

    if total_msgs == 0:
        conn.close()
        return {
            "period": f"{start_date} to {end_date}",
            "total_messages": 0,
            "active_days": 0,
            "vinu_count": 0,
            "bhumi_count": 0,
            "vinu_pct": 0,
            "bhumi_pct": 0,
            "avg_words": 0,
            "top_emojis": [],
            "top_words": [],
            "hourly": [0] * 24
        }

    vinu_msgs = conn.execute("""
        SELECT COUNT(*) as c FROM messages 
        WHERE iso_date >= ? AND iso_date <= ? AND is_vinu = 1
    """, (start_date, end_date)).fetchone()["c"]

    bhuu_msgs = conn.execute("""
        SELECT COUNT(*) as c FROM messages 
        WHERE iso_date >= ? AND iso_date <= ? AND (is_bhumi = 1 OR sender_clean LIKE '%Bhuu%')
    """, (start_date, end_date)).fetchone()["c"]

    active_days = conn.execute("""
        SELECT COUNT(DISTINCT iso_date) as c FROM messages 
        WHERE iso_date >= ? AND iso_date <= ?
    """, (start_date, end_date)).fetchone()["c"]

    avg_words_row = conn.execute("""
        SELECT AVG(word_count) as avg_w FROM messages
        WHERE iso_date >= ? AND iso_date <= ? AND message_type = 'text'
    """, (start_date, end_date)).fetchone()

    # Emojis in period
    emoji_rows = conn.execute("""
        SELECT emojis_json FROM messages 
        WHERE iso_date >= ? AND iso_date <= ? AND emoji_count > 0
    """, (start_date, end_date)).fetchall()
    
    emoji_counts = Counter()
    for er in emoji_rows:
        if er["emojis_json"]:
            try:
                for em in json.loads(er["emojis_json"]):
                    emoji_counts[em] += 1
            except Exception:
                pass

    # Words in period
    text_rows = conn.execute("""
        SELECT content FROM messages 
        WHERE iso_date >= ? AND iso_date <= ? AND message_type = 'text' AND is_system = 0
    """, (start_date, end_date)).fetchall()

    word_counts = Counter()
    for r in text_rows:
        words = re.findall(r'\b[a-zA-Z\u0900-\u097F]{2,}\b', r["content"].lower())
        for w in words:
            if w not in STOP_WORDS and len(w) > 1 and not w.isdigit():
                word_counts[w] += 1

    # Hourly distribution
    time_rows = conn.execute("""
        SELECT iso_datetime FROM messages 
        WHERE iso_date >= ? AND iso_date <= ?
    """, (start_date, end_date)).fetchall()

    hourly = [0] * 24
    for tr in time_rows:
        if tr["iso_datetime"] and "T" in tr["iso_datetime"]:
            try:
                h = int(tr["iso_datetime"].split("T")[1].split(":")[0])
                hourly[h] += 1
            except Exception:
                pass

    conn.close()

    return {
        "period": f"{start_date} to {end_date}",
        "total_messages": total_msgs,
        "active_days": active_days,
        "msgs_per_day": round(total_msgs / active_days, 1) if active_days else 0,
        "vinu_count": vinu_msgs,
        "bhuu_count": bhuu_msgs,
        "bhumi_count": bhuu_msgs,
        "vinu_pct": round((vinu_msgs / total_msgs * 100), 1) if total_msgs else 0,
        "bhuu_pct": round((bhuu_msgs / total_msgs * 100), 1) if total_msgs else 0,
        "bhumi_pct": round((bhuu_msgs / total_msgs * 100), 1) if total_msgs else 0,
        "avg_words": round(avg_words_row["avg_w"], 1) if avg_words_row and avg_words_row["avg_w"] else 0,
        "top_emojis": [{"emoji": em, "count": c} for em, c in emoji_counts.most_common(10)],
        "top_words": [{"word": w, "count": c} for w, c in word_counts.most_common(15)],
        "hourly": hourly
    }


def compare_evolution(
    p1_start: Optional[str] = None,
    p1_end: Optional[str] = None,
    p2_start: Optional[str] = None,
    p2_end: Optional[str] = None
) -> Dict[str, Any]:
    """Compare two periods (defaults to 2025 vs 2026)."""
    # Defaults: 2025 vs 2026
    if not p1_start:
        p1_start = "2025-01-01"
    if not p1_end:
        p1_end = "2025-12-31"
    if not p2_start:
        p2_start = "2026-01-01"
    if not p2_end:
        p2_end = "2026-12-31"

    p1 = get_period_stats(p1_start, p1_end)
    p2 = get_period_stats(p2_start, p2_end)

    p1["label"] = "2025 (Initial Connection)" if p1_start.startswith("2025") and p1_end.startswith("2025") else f"{p1_start} to {p1_end}"
    p2["label"] = "2026 (Active Era)" if p2_start.startswith("2026") and p2_end.startswith("2026") else f"{p2_start} to {p2_end}"

    # Calculate differences
    diff_total = p2["total_messages"] - p1["total_messages"]
    diff_daily = round(p2["msgs_per_day"] - p1["msgs_per_day"], 1)
    diff_vinu_pct = round(p2["vinu_pct"] - p1["vinu_pct"], 1)

    return {
        "period_1": p1,
        "period_2": p2,
        "comparison": {
            "message_growth": diff_total,
            "daily_velocity_change": diff_daily,
            "vinu_balance_shift": diff_vinu_pct,
            "summary": f"In {p2['label']}, conversation frequency shifted by {diff_daily:+} msgs/day compared to {p1['label']}."
        }
    }
