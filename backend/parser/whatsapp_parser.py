"""
Robust WhatsApp Chat Export Parser
Handles:
- Multiline continuation messages
- Unicode timestamps (including narrow non-breaking space \\u202f)
- 12-hour (am/pm) and 24-hour formats
- Marathi, Hindi, English and mixed multilingual text
- Emojis, punctuation, multiline quotes
- Media attachments, edited messages, deleted messages, voice call events
- Sender normalization (Vinu 💝🎀, Bhumi 🎀, System)
"""

import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# Multi-format WhatsApp Line Header regexes (iOS, Android, Windows, Mac)
HEADER_PATTERNS = [
    # 1. iOS bracket format: [DD/MM/YYYY, HH:MM:SS AM/PM] or [DD/MM/YY, HH:MM:SS]
    re.compile(r'^\[(\d{1,4}[\/.-]\d{1,2}[\/.-]\d{1,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:[\s\u202f\u00a0]*(?:[aApP][mM]))?)\]\s*(?:-\s*)?(.*)$'),
    # 2. Android standard format: DD/MM/YYYY, HH:MM am/pm - ... or DD/MM/YYYY, HH:MM - ...
    re.compile(r'^(\d{1,4}[\/.-]\d{1,2}[\/.-]\d{1,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:[\s\u202f\u00a0]*(?:[aApP][mM]))?)\s*-\s*(.*)$'),
    # 3. Fallback with colon separator
    re.compile(r'^(\d{1,4}[\/.-]\d{1,2}[\/.-]\d{1,4}),?\s+(\d{1,2}:\d{2}(?::\d{2})?(?:[\s\u202f\u00a0]*(?:[aApP][mM]))?)\s*:\s*(.*)$')
]

# Emojis regex range
EMOJI_REGEX = re.compile(
    r'[\U00010000-\U0010ffff\u2600-\u27bf\u2300-\u23ff\u2b50\u2b55\u200d\ufe0f]',
    flags=re.UNICODE
)

SYSTEM_PATTERNS = [
    r'Messages and calls are end-to-end encrypted',
    r'created group',
    r'added',
    r'left',
    r'changed the group',
    r'security code changed',
    r'Missed voice call',
    r'Missed video call',
    r'This chat is with a business account',
    r'You were added'
]

MEDIA_PATTERNS = [
    r'<Media omitted>',
    r'\(file attached\)',
    r'<attached:\s*[^>]+>',
    r'\.vcf\b',
    r'\.opus\b',
    r'\.mp3\b',
    r'\.mp4\b',
    r'\.pdf\b',
    r'\.jpg\b',
    r'\.jpeg\b',
    r'\.png\b',
    r'\.webp\b'
]


def parse_date_time(date_str: str, time_str: str) -> Optional[datetime]:
    """Parse date and time strings into a datetime object."""
    # Normalize spaces
    clean_date = date_str.strip()
    clean_time = time_str.strip().replace('\u202f', ' ').replace('\u00a0', ' ').upper()
    # Normalize 1:17 PM / 1:17PM
    clean_time = re.sub(r'(\d+:\d+(?::\d+)?)\s*([AP]M)', r'\1 \2', clean_time)

    date_formats = [
        '%d/%m/%Y', '%d/%m/%y', '%d-%m-%Y', '%d-%m-%y', '%d.%m.%Y', '%d.%m.%y',
        '%m/%d/%Y', '%m/%d/%y', '%Y-%m-%d', '%Y/%m/%d'
    ]
    time_formats = [
        '%I:%M %p', '%I:%M:%S %p', '%H:%M', '%H:%M:%S'
    ]

    for df in date_formats:
        for tf in time_formats:
            fmt = f"{df} {tf}"
            comb = f"{clean_date} {clean_time}"
            try:
                return datetime.strptime(comb, fmt)
            except ValueError:
                continue

    # Fallback: simple split
    try:
        parts = re.split(r'[\/.-]', clean_date)
        if len(parts) == 3:
            day, month, year = int(parts[0]), int(parts[1]), int(parts[2])
            if year < 100:
                year += 2000
            return datetime(year, month, day, 12, 0, 0)
    except Exception:
        pass

    return None


def extract_emojis(text: str) -> List[str]:
    """Extract list of individual emojis from text."""
    if not text:
        return []
    return EMOJI_REGEX.findall(text)


def categorize_message(sender_raw: str, content: str, is_system: bool) -> Dict[str, Any]:
    """Identify message flags: type, edited, deleted, media, sender identity."""
    is_edited = False
    is_deleted = False
    msg_type = "text"

    # Check edited tag
    if '<This message was edited>' in content or 'This message was edited' in content:
        is_edited = True
        content = content.replace('<This message was edited>', '').strip()

    # Check deleted message
    if content.strip() in ['This message was deleted', 'You deleted this message']:
        is_deleted = True
        msg_type = "deleted"
    elif is_system:
        msg_type = "system"
    else:
        # Check media patterns
        for mp in MEDIA_PATTERNS:
            if re.search(mp, content, re.IGNORECASE):
                msg_type = "media"
                break
        if "Missed voice call" in content or "Missed video call" in content:
            msg_type = "call"

    # Sender normalization
    sender_clean = sender_raw.strip() if sender_raw else "System"
    is_vinu = False
    is_bhuu = False

    if not is_system:
        lowered_sender = sender_clean.lower()
        if "vinu" in lowered_sender:
            is_vinu = True
            sender_clean = "Vinu 💝🎀"
        elif "bhumi" in lowered_sender or "bhumika" in lowered_sender or "bhuu" in lowered_sender:
            is_bhuu = True
            sender_clean = "Bhuu 🎀"

    # Emoji, word, char stats
    emojis = extract_emojis(content)
    words = re.findall(r'\b\w+\b', content, re.UNICODE)
    char_count = len(content)

    return {
        "content": content,
        "sender_clean": sender_clean,
        "is_vinu": is_vinu,
        "is_bhumi": is_bhuu,  # Keep key backwards compatible while pointing to Bhuu
        "is_bhuu": is_bhuu,
        "is_system": is_system,
        "message_type": msg_type,
        "is_edited": is_edited,
        "is_deleted": is_deleted,
        "emoji_count": len(emojis),
        "emojis": emojis,
        "word_count": len(words),
        "char_count": char_count
    }


def parse_whatsapp_text(raw_text: str) -> List[Dict[str, Any]]:
    """
    Parse the entire raw text of any WhatsApp chat export into structured message records.
    Strips invisible unicode directional marks and supports Android/iOS formats.
    """
    lines = raw_text.splitlines()
    parsed_messages = []
    current_msg: Optional[Dict[str, Any]] = None

    for line in lines:
        clean_line = line.strip().lstrip('\u200e\u200f\ufeff\u202a\u202c\u202d')
        if not clean_line and not current_msg:
            continue

        match = None
        for pat in HEADER_PATTERNS:
            m = pat.match(clean_line)
            if m:
                match = m
                break

        if match:
            # Commit previous message if any
            if current_msg is not None:
                parsed_messages.append(current_msg)

            date_str = match.group(1).strip()
            time_str = match.group(2).strip()
            rest = match.group(3).strip()

            dt = parse_date_time(date_str, time_str)
            timestamp = int(dt.timestamp()) if dt else 0
            iso_date = dt.strftime('%Y-%m-%d') if dt else date_str
            iso_datetime = dt.isoformat() if dt else f"{date_str} {time_str}"

            # Check if this line is a sender message (contains ': ') or a system message
            is_system = False
            sender_raw = ""
            content = ""

            # Check for known system message patterns first
            for sys_pat in SYSTEM_PATTERNS:
                if re.search(sys_pat, rest, re.IGNORECASE):
                    is_system = True
                    break

            if not is_system and ': ' in rest:
                # Regular message: "Sender: Content"
                parts = rest.split(': ', 1)
                sender_raw = parts[0].strip()
                content = parts[1].strip()
            else:
                # System message or unsplit notice
                is_system = True
                sender_raw = "System"
                content = rest.strip()

            category_data = categorize_message(sender_raw, content, is_system)

            current_msg = {
                "date_str": date_str,
                "time_str": time_str,
                "iso_date": iso_date,
                "iso_datetime": iso_datetime,
                "timestamp": timestamp,
                "sender_raw": sender_raw,
                "sender_clean": category_data["sender_clean"],
                "is_vinu": category_data["is_vinu"],
                "is_bhumi": category_data["is_bhumi"],
                "is_system": category_data["is_system"],
                "content": category_data["content"],
                "message_type": category_data["message_type"],
                "is_edited": category_data["is_edited"],
                "is_deleted": category_data["is_deleted"],
                "emoji_count": category_data["emoji_count"],
                "emojis": category_data["emojis"],
                "word_count": category_data["word_count"],
                "char_count": category_data["char_count"]
            }
        else:
            # Multiline continuation for current message
            if current_msg is not None:
                current_msg["content"] += "\n" + line
                # Recalculate word, char, and emoji count
                emojis = extract_emojis(current_msg["content"])
                words = re.findall(r'\b\w+\b', current_msg["content"], re.UNICODE)
                current_msg["emoji_count"] = len(emojis)
                current_msg["emojis"] = emojis
                current_msg["word_count"] = len(words)
                current_msg["char_count"] = len(current_msg["content"])

    if current_msg is not None:
        parsed_messages.append(current_msg)

    return parsed_messages


def parse_whatsapp_file(file_path: str) -> List[Dict[str, Any]]:
    """Read and parse a WhatsApp export file from disk (UTF-8)."""
    with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
    return parse_whatsapp_text(content)

