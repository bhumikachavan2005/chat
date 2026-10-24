"""
Friendship Statistics & Advanced Analytics Engine
- Factual computation of chat volume, split, active days, streaks
- Response time dynamics (Vinu vs Bhuu average reply speeds)
- Conversation starters analysis (initiations after silence)
- Late-night chatting metrics (11 PM - 5 AM)
- Friendship milestones (1st, 1K, 5K, 10K, 15K messages)
- 24-Hour hourly rhythm & heatmap
- Emoji frequency leaderboard
- Vocabulary analysis with refined Marathi / Hinglish stopword filters
"""

import re
import json
from collections import Counter
from datetime import datetime
from typing import Dict, Any, List
from backend.database import get_db_connection

# Comprehensive stop words to extract meaningful topics
STOP_WORDS = {
    # English
    'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
    'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
    'did', 'will', 'would', 'shall', 'should', 'can', 'could', 'may', 'might', 'must',
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'you', 'your', 'he', 'him', 'his',
    'she', 'her', 'it', 'its', 'they', 'them', 'their', 'this', 'that', 'these', 'those',
    'what', 'which', 'who', 'whom', 'when', 'where', 'why', 'how', 'all', 'any', 'both',
    'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
    'own', 'same', 'so', 'than', 'too', 'very', 's', 't', 'just', 'don', 'now', 'ok', 'okay',
    'yes', 'yeah', 'yep', 'nope', 'yup', 'up', 'down', 'out', 'off', 'over', 'under', 'again',
    # Marathi / Hinglish transliterations & Chat abbreviations
    'ha', 'haa', 'hoo', 'ho', 'nahii', 'nhi', 'nahi', 'nnhi', 'na', 'n', 'pn', 'pan', 'k', 'ka',
    'ki', 'ky', 'kay', 'kahi', 'khi', 'kasa', 'kashi', 'kashiye', 'ahe', 'aahe', 'ahet', 'aahet',
    'aahech', 'hoti', 'hoto', 'hote', 'zal', 'zala', 'zali', 'zalay', 'ch', 'tr', 'tar', 'mg', 'mag',
    'so', 'but', 'ani', 'mla', 'mala', 'tula', 'tuza', 'tuzi', 'tuze', 'maz', 'maza', 'mazya',
    'me', 'mi', 'tu', 'te', 'ti', 'to', 'tya', 'ts', 'tsa', 'tasa', 'tas', 'as', 'asa', 'asi', 'asude',
    'kr', 'kru', 'krun', 'krtoys', 'krtoy', 'krtiye', 'kartoy', 'karnar', 'krnr', 'bol', 'sang', 'bgh',
    'bghte', 'bghnr', 'bhetel', 'bhetl', 'evdhe', 'evdh', 'pan', 'thoda', 'thik', 'br', 'hm', 'hmm',
    'hii', 'hi', 'hello', 'media', 'omitted', 'attached', 'message', 'deleted', 'edited',
    'j1', 'v4', 'yt', 'msg', 'clg', 'jr', 'tithe', 'ithe', 'kiti', 'jevlas', 'zopnr', 'lavkr',
    'kadhi', 'kdhi', 'aata', 'atta', 'nko', 'koni', 'sobt', 'ghari', 'jaude', 'sathi', 'madhi', 'mhade'
}


def calculate_streaks(active_dates: List[str]) -> Dict[str, Any]:
    """Calculate longest and current daily chatting streaks."""
    if not active_dates:
        return {"longest_streak": 0, "longest_streak_dates": "", "current_streak": 0}

    sorted_dates = sorted([datetime.strptime(d, "%Y-%m-%d") for d in set(active_dates)])
    
    longest_streak = 0
    longest_start = None
    longest_end = None
    
    current_streak = 1
    streak_start = sorted_dates[0]
    
    for i in range(1, len(sorted_dates)):
        diff = (sorted_dates[i] - sorted_dates[i-1]).days
        if diff == 1:
            current_streak += 1
        else:
            if current_streak > longest_streak:
                longest_streak = current_streak
                longest_start = streak_start
                longest_end = sorted_dates[i-1]
            current_streak = 1
            streak_start = sorted_dates[i]

    if current_streak > longest_streak:
        longest_streak = current_streak
        longest_start = streak_start
        longest_end = sorted_dates[-1]

    longest_dates_str = ""
    if longest_start and longest_end:
        longest_dates_str = f"{longest_start.strftime('%d %b %Y')} – {longest_end.strftime('%d %b %Y')}"

    return {
        "longest_streak": longest_streak,
        "longest_streak_dates": longest_dates_str,
        "current_streak": current_streak
    }


def calculate_dynamics_and_response_times(all_messages: List[Any]) -> Dict[str, Any]:
    """
    Calculate:
    1. Average Response Times (in minutes) for Vinu and Bhuu during active conversations (< 60m).
    2. Conversation Starters (messages sent after > 2 hours of silence).
    3. Late-Night Messages (between 11 PM and 5 AM).
    """
    vinu_response_delays = []
    bhuu_response_delays = []

    vinu_starters = 0
    bhuu_starters = 0

    vinu_late_night = 0
    bhuu_late_night = 0

    last_ts = None
    last_sender = None

    for msg in all_messages:
        ts = msg["timestamp"]
        is_vinu = msg["is_vinu"]
        is_bhuu = msg["is_bhumi"] or ("Bhuu" in msg["sender_clean"])
        is_system = msg["is_system"]

        if is_system or ts <= 0:
            continue

        # Check Late Night (11 PM - 5 AM)
        dt = datetime.fromtimestamp(ts) if ts > 0 else None
        if dt and (dt.hour >= 23 or dt.hour < 5):
            if is_vinu:
                vinu_late_night += 1
            elif is_bhuu:
                bhuu_late_night += 1

        if last_ts is not None:
            gap = ts - last_ts
            # Conversation starter (> 2 hours gap = 7200 seconds)
            if gap >= 7200:
                if is_vinu:
                    vinu_starters += 1
                elif is_bhuu:
                    bhuu_starters += 1
            # Active reply (< 60 minutes = 3600 seconds)
            elif 0 < gap < 3600:
                if is_vinu and last_sender == "bhuu":
                    vinu_response_delays.append(gap)
                elif is_bhuu and last_sender == "vinu":
                    bhuu_response_delays.append(gap)

        last_ts = ts
        last_sender = "vinu" if is_vinu else ("bhuu" if is_bhuu else None)

    # Average response times
    vinu_avg_sec = sum(vinu_response_delays) / len(vinu_response_delays) if vinu_response_delays else 120
    bhuu_avg_sec = sum(bhuu_response_delays) / len(bhuu_response_delays) if bhuu_response_delays else 120

    def format_delay(sec):
        m = int(sec // 60)
        s = int(sec % 60)
        if m == 0:
            return f"{s}s"
        return f"{m}m {s}s"

    total_starters = vinu_starters + bhuu_starters
    vinu_starters_pct = round((vinu_starters / total_starters * 100), 1) if total_starters else 50
    bhuu_starters_pct = round((bhuu_starters / total_starters * 100), 1) if total_starters else 50

    return {
        "vinu_avg_response_formatted": format_delay(vinu_avg_sec),
        "bhuu_avg_response_formatted": format_delay(bhuu_avg_sec),
        "vinu_avg_response_seconds": round(vinu_avg_sec),
        "bhuu_avg_response_seconds": round(bhuu_avg_sec),
        "starters": {
            "vinu": vinu_starters,
            "bhuu": bhuu_starters,
            "vinu_pct": vinu_starters_pct,
            "bhuu_pct": bhuu_starters_pct
        },
        "late_night": {
            "total": vinu_late_night + bhuu_late_night,
            "vinu": vinu_late_night,
            "bhuu": bhuu_late_night
        }
    }


def get_friendship_milestones(conn) -> List[Dict[str, Any]]:
    """Retrieve key milestone messages (1st, 1K, 5K, 10K, 15K)."""
    targets = [1, 1000, 5000, 10000, 15000]
    milestones = []

    for t in targets:
        row = conn.execute("SELECT id, date_str, time_str, sender_clean, content, is_vinu, is_bhumi FROM messages WHERE id >= ? ORDER BY id ASC LIMIT 1", (t,)).fetchone()
        if row:
            milestones.append({
                "milestone": f"{t:,} Messages",
                "message_id": row["id"],
                "date_str": row["date_str"],
                "time_str": row["time_str"],
                "sender_clean": row["sender_clean"],
                "content": row["content"]
            })

    return milestones


def get_friendship_statistics() -> Dict[str, Any]:
    """Compile comprehensive factual statistics for the entire archive."""
    conn = get_db_connection()

    total_msgs = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
    if total_msgs == 0:
        conn.close()
        return {"total_messages": 0}

    vinu_msgs = conn.execute("SELECT COUNT(*) as c FROM messages WHERE is_vinu = 1").fetchone()["c"]
    bhuu_msgs = conn.execute("SELECT COUNT(*) as c FROM messages WHERE is_bhumi = 1 OR sender_clean LIKE '%Bhuu%'").fetchone()["c"]
    sys_msgs = conn.execute("SELECT COUNT(*) as c FROM messages WHERE is_system = 1").fetchone()["c"]
    media_msgs = conn.execute("SELECT COUNT(*) as c FROM messages WHERE message_type = 'media'").fetchone()["c"]
    deleted_msgs = conn.execute("SELECT COUNT(*) as c FROM messages WHERE is_deleted = 1").fetchone()["c"]
    edited_msgs = conn.execute("SELECT COUNT(*) as c FROM messages WHERE is_edited = 1").fetchone()["c"]
    calls_count = conn.execute("SELECT COUNT(*) as c FROM messages WHERE message_type = 'call'").fetchone()["c"]

    vinu_pct = round((vinu_msgs / total_msgs * 100), 1) if total_msgs else 0
    bhuu_pct = round((bhuu_msgs / total_msgs * 100), 1) if total_msgs else 0

    # Date Range & Active Days
    date_rows = conn.execute("SELECT iso_date, COUNT(*) as count FROM messages GROUP BY iso_date ORDER BY iso_date ASC").fetchall()
    active_days_count = len(date_rows)
    all_dates = [r["iso_date"] for r in date_rows if r["iso_date"]]

    start_date = all_dates[0] if all_dates else ""
    end_date = all_dates[-1] if all_dates else ""

    # Most active day
    most_active_day_row = max(date_rows, key=lambda x: x["count"]) if date_rows else None
    most_active_day = {
        "date": most_active_day_row["iso_date"] if most_active_day_row else "",
        "count": most_active_day_row["count"] if most_active_day_row else 0
    }

    # Streak Calculation
    streak_info = calculate_streaks(all_dates)

    # All messages for dynamics
    all_raw_msgs = conn.execute("SELECT id, timestamp, is_vinu, is_bhumi, is_system, sender_clean FROM messages ORDER BY id ASC").fetchall()
    dynamics = calculate_dynamics_and_response_times(all_raw_msgs)

    # Milestones
    milestones = get_friendship_milestones(conn)

    # Monthly Aggregation
    month_rows = conn.execute("""
        SELECT 
            substr(iso_date, 1, 7) as year_month,
            COUNT(*) as total,
            SUM(is_vinu) as vinu_total,
            SUM(is_bhumi) as bhuu_total
        FROM messages
        WHERE iso_date IS NOT NULL AND iso_date != ''
        GROUP BY year_month
        ORDER BY year_month ASC
    """).fetchall()

    monthly_stats = [
        {
            "month": r["year_month"],
            "total": r["total"],
            "vinu": r["vinu_total"] or 0,
            "bhuu": r["bhuu_total"] or 0,
            "bhumi": r["bhuu_total"] or 0  # backwards compatibility
        }
        for r in month_rows
    ]

    most_active_month = max(monthly_stats, key=lambda x: x["total"]) if monthly_stats else {"month": "", "total": 0}

    # Day of Week Distribution
    dow_rows = conn.execute("""
        SELECT 
            strftime('%w', iso_date) as dow,
            COUNT(*) as total,
            SUM(is_vinu) as vinu,
            SUM(is_bhumi) as bhuu
        FROM messages
        WHERE iso_date IS NOT NULL
        GROUP BY dow
        ORDER BY dow ASC
    """).fetchall()

    dow_names = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
    dow_stats = []
    for i, name in enumerate(dow_names):
        found = next((r for r in dow_rows if r["dow"] == str(i)), None)
        dow_stats.append({
            "day_index": i,
            "day_name": name,
            "total": found["total"] if found else 0,
            "vinu": found["vinu"] if (found and found["vinu"]) else 0,
            "bhuu": found["bhuu"] if (found and found["bhuu"]) else 0,
            "bhumi": found["bhuu"] if (found and found["bhuu"]) else 0
        })

    # Hourly Heatmap (0 - 23 hours)
    hour_counter_total = [0] * 24
    hour_counter_vinu = [0] * 24
    hour_counter_bhuu = [0] * 24

    all_time_rows = conn.execute("SELECT is_vinu, is_bhumi, iso_datetime, time_str, sender_clean FROM messages").fetchall()
    for tr in all_time_rows:
        h = 12
        if tr["iso_datetime"] and "T" in tr["iso_datetime"]:
            try:
                h = int(tr["iso_datetime"].split("T")[1].split(":")[0])
            except Exception:
                pass
        
        hour_counter_total[h] += 1
        if tr["is_vinu"]:
            hour_counter_vinu[h] += 1
        elif tr["is_bhumi"] or "Bhuu" in tr["sender_clean"]:
            hour_counter_bhuu[h] += 1

    hourly_stats = [
        {
            "hour": h,
            "label": f"{h:02d}:00",
            "total": hour_counter_total[h],
            "vinu": hour_counter_vinu[h],
            "bhuu": hour_counter_bhuu[h],
            "bhumi": hour_counter_bhuu[h]
        }
        for h in range(24)
    ]

    # Time period breakdown
    night_msgs = sum(hour_counter_total[0:6])
    morning_msgs = sum(hour_counter_total[6:12])
    afternoon_msgs = sum(hour_counter_total[12:18])
    evening_msgs = sum(hour_counter_total[18:24])

    # Word & Length Metrics
    length_rows = conn.execute("""
        SELECT 
            is_vinu, is_bhumi,
            AVG(word_count) as avg_words,
            AVG(char_count) as avg_chars,
            SUM(word_count) as total_words,
            SUM(char_count) as total_chars
        FROM messages
        WHERE message_type = 'text' AND is_system = 0
        GROUP BY is_vinu, is_bhumi
    """).fetchall()

    vinu_len = next((r for r in length_rows if r["is_vinu"] == 1), None)
    bhuu_len = next((r for r in length_rows if r["is_bhumi"] == 1), None)

    # Emoji Leaderboard
    emoji_rows = conn.execute("SELECT emojis_json, is_vinu, is_bhumi FROM messages WHERE emoji_count > 0").fetchall()
    emoji_total_counts = Counter()
    emoji_vinu_counts = Counter()
    emoji_bhuu_counts = Counter()

    for er in emoji_rows:
        if er["emojis_json"]:
            try:
                em_list = json.loads(er["emojis_json"])
                for em in em_list:
                    emoji_total_counts[em] += 1
                    if er["is_vinu"]:
                        emoji_vinu_counts[em] += 1
                    elif er["is_bhumi"]:
                        emoji_bhuu_counts[em] += 1
            except Exception:
                pass

    top_emojis = [
        {
            "emoji": em,
            "count": cnt,
            "vinu": emoji_vinu_counts[em],
            "bhuu": emoji_bhuu_counts[em],
            "bhumi": emoji_bhuu_counts[em]
        }
        for em, cnt in emoji_total_counts.most_common(20)
    ]

    # Word Frequency Leaderboard
    text_rows = conn.execute("SELECT content FROM messages WHERE message_type = 'text' AND is_system = 0").fetchall()
    word_counts = Counter()
    for row in text_rows:
        words = re.findall(r'\b[a-zA-Z\u0900-\u097F]{2,}\b', row["content"].lower())
        for w in words:
            if w not in STOP_WORDS and len(w) > 1 and not w.isdigit():
                word_counts[w] += 1

    top_words = [{"word": w, "count": c} for w, c in word_counts.most_common(35)]
    avg_msgs_per_day = round(total_msgs / active_days_count, 1) if active_days_count else 0

    conn.close()

    return {
        "total_messages": total_msgs,
        "vinu_messages": vinu_msgs,
        "bhuu_messages": bhuu_msgs,
        "bhumi_messages": bhuu_msgs,
        "system_messages": sys_msgs,
        "media_messages": media_msgs,
        "deleted_messages": deleted_msgs,
        "edited_messages": edited_msgs,
        "calls_count": calls_count,
        "vinu_percentage": vinu_pct,
        "bhuu_percentage": bhuu_pct,
        "bhumi_percentage": bhuu_pct,
        "active_days": active_days_count,
        "average_messages_per_day": avg_msgs_per_day,
        "start_date": start_date,
        "end_date": end_date,
        "most_active_day": most_active_day,
        "most_active_month": most_active_month,
        "streak_info": streak_info,
        "dynamics": dynamics,
        "milestones": milestones,
        "monthly_stats": monthly_stats,
        "dow_stats": dow_stats,
        "hourly_stats": hourly_stats,
        "time_periods": {
            "night": night_msgs,
            "morning": morning_msgs,
            "afternoon": afternoon_msgs,
            "evening": evening_msgs
        },
        "averages": {
            "vinu_avg_words": round(vinu_len["avg_words"], 1) if vinu_len and vinu_len["avg_words"] else 0,
            "bhuu_avg_words": round(bhuu_len["avg_words"], 1) if bhuu_len and bhuu_len["avg_words"] else 0,
            "vinu_total_words": vinu_len["total_words"] if vinu_len and vinu_len["total_words"] else 0,
            "bhuu_total_words": bhuu_len["total_words"] if bhuu_len and bhuu_len["total_words"] else 0,
        },
        "top_emojis": top_emojis,
        "top_words": top_words
    }
