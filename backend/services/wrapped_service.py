"""
Friendship Wrapped - Secret Photos Vault Engine
- Focuses purely on personal photos of Vinu 💝 & Bhuu 🎀
- No text-only stat stories; pure private photo showcase
"""

from typing import Dict, Any, List
from backend.services.wrapped_photo_service import list_wrapped_photos


def generate_friendship_wrapped() -> Dict[str, Any]:
    """Compile the personal photo vault payload for Wrapped."""
    photos = list_wrapped_photos()

    if not photos:
        slides = [
            {
                "id": "empty_vault",
                "is_empty": True,
                "title": "Secret Photo Vault",
                "subtitle": "Vinu 💝 × Bhuu 🎀",
                "icon": "📸",
                "photo_id": None,
                "photo_url": None,
                "caption": "No photos added yet. Click 'Add Photo' to store your favorite memories here!",
                "created_at": None
            }
        ]
    else:
        slides = [
            {
                "id": f"photo_{p['id']}",
                "is_empty": False,
                "photo_id": p["id"],
                "photo_url": p["url"],
                "caption": p.get("caption") or "",
                "title": p.get("caption") or f"Memory #{idx + 1}",
                "subtitle": f"Photo {idx + 1} of {len(photos)}",
                "created_at": p.get("created_at")
            }
            for idx, p in enumerate(photos)
        ]

    return {
        "title": "Vinu 💝 × Bhuu 🎀 Secret Photos Vault",
        "total_slides": len(slides),
        "slides": slides,
        "summary": {
            "photos_count": len(photos)
        }
    }
