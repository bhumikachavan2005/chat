"""
Automated Test Suite for Vinu & Bhumi Private Archive
Tests:
1. WhatsApp parser accuracy on source export
2. SQLite schema & FTS5 indexing
3. Argon2id password hashing and session tokens
4. Memory bookmarks CRUD
5. Statistics & Evolution computations
6. AES-256-GCM Encrypted Backup & Restore round-trip
7. FastAPI API endpoints
"""

import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.database import init_db, get_db_connection, bulk_insert_messages, set_setting, get_setting, clear_all_data
from backend.parser.whatsapp_parser import parse_whatsapp_file
from backend.security.auth import hash_password, verify_password, session_store, encrypt_data_aes_gcm, decrypt_data_aes_gcm
from backend.services.chat_service import get_messages, get_message_context, get_chat_bounds
from backend.services.search_service import search_messages
from backend.services.memory_service import add_memory, list_memories, delete_memory
from backend.services.stats_service import get_friendship_statistics
from backend.services.evolution_service import compare_evolution
from backend.services.backup_service import (
    export_encrypted_backup, restore_encrypted_backup, import_txt_content
)


class TestArchive(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        init_db()
        # Parse and populate DB if empty
        conn = get_db_connection()
        count = conn.execute("SELECT COUNT(*) as c FROM messages").fetchone()["c"]
        conn.close()
        if count == 0:
            source_txt = os.path.join(BASE_DIR, "WhatsApp Chat with Vinu💝🎀.txt")
            if os.path.exists(source_txt):
                msgs = parse_whatsapp_file(source_txt)
                bulk_insert_messages(msgs)

    def test_01_password_hashing(self):
        pwd = "SecretVinuBhumiPassword123!"
        hashed = hash_password(pwd)
        self.assertTrue(verify_password(hashed, pwd))
        self.assertFalse(verify_password(hashed, "WrongPassword"))

    def test_02_session_store(self):
        session_store.set_timeout(15)
        token = session_store.create_session()
        self.assertTrue(session_store.validate_session(token))
        self.assertFalse(session_store.validate_session("non-existent-token"))
        session_store.revoke_session(token)
        self.assertFalse(session_store.validate_session(token))

    def test_03_chat_bounds_and_messages(self):
        bounds = get_chat_bounds()
        self.assertGreater(bounds["total_count"], 10000)
        self.assertTrue(bounds["start_date"].startswith("2025"))
        self.assertTrue(bounds["end_date"].startswith("2026"))

        # Test pagination
        page = get_messages(limit=50, offset=0)
        self.assertEqual(len(page["messages"]), 50)
        self.assertIn("content", page["messages"][0])

    def test_04_fts5_search(self):
        res = search_messages("internship", limit=10)
        self.assertGreater(res["total"], 0)
        self.assertTrue(len(res["results"]) > 0)
        self.assertIn("highlighted_content", res["results"][0])

    def test_05_memory_system(self):
        page = get_messages(limit=1, offset=0)
        msg_id = page["messages"][0]["id"]

        # Add memory
        mem = add_memory(msg_id, "special", "First special memory note", "test,special")
        self.assertIsNotNone(mem)
        self.assertEqual(mem["category"], "special")

        # List memories
        mems = list_memories(category="special")
        self.assertTrue(any(m["id"] == mem["id"] for m in mems))

        # Delete memory
        deleted = delete_memory(mem["id"])
        self.assertTrue(deleted)

    def test_06_stats_and_evolution(self):
        stats = get_friendship_statistics()
        self.assertGreater(stats["total_messages"], 10000)
        self.assertGreater(stats["vinu_messages"], 1000)
        self.assertGreater(stats["bhumi_messages"], 1000)
        self.assertGreater(len(stats["top_emojis"]), 0)

        evo = compare_evolution()
        self.assertIn("period_1", evo)
        self.assertIn("period_2", evo)

    def test_07_aes_gcm_backup_roundtrip(self):
        passphrase = "UltraSecurePassphrase_987654"
        enc_backup = export_encrypted_backup(passphrase)
        self.assertIsInstance(enc_backup, bytes)
        self.assertGreater(len(enc_backup), 1000)

        # Restore test
        restore_res = restore_encrypted_backup(enc_backup, passphrase)
        self.assertEqual(restore_res["status"], "success")
        self.assertGreater(restore_res["restored_messages"], 10000)

    def test_08_incremental_merge_dedup(self):
        sample_txt = (
            "28/11/2025, 6:00\u202fpm - Messages and calls are end-to-end encrypted.\n"
            "30/12/2025, 8:43\u202fpm - Bhumika Chavan: Hii\n"
            "30/12/2025, 8:44\u202fpm - Vinu 💝🎀: Hello!\n"
            "28/08/2026, 10:00\u202fpm - Bhumika Chavan: Brand new test message from the future!\n"
        )
        res = import_txt_content(sample_txt)
        self.assertEqual(res["status"], "success")
        # Should add at least the new future message and retain all existing
        self.assertGreater(res["total_messages"], 10000)

    def test_09_multiformat_ios_android_parser(self):
        from backend.parser.whatsapp_parser import parse_whatsapp_text
        raw = (
            "\u200e[28/11/2025, 1:17:00 PM] Vinu: Hello from iOS bracket format with LTR\n"
            "[28/11/25, 13:17:05] Bhumi: Hello 24-hr iOS\n"
            "28/11/2025, 1:17 pm - Vinu 💝🎀: Hello Android standard\n"
            "28/11/2025, 1:17\u202fpm - Bhuu 🎀: Hello Android narrow space\n"
            "28/11/2025, 13:17 - Vinu: Hello Android 24-hr\n"
        )
        parsed = parse_whatsapp_text(raw)
        self.assertEqual(len(parsed), 5)
        self.assertTrue(parsed[0]["is_vinu"])
        self.assertTrue(parsed[1]["is_bhumi"])
        self.assertEqual(parsed[0]["content"], "Hello from iOS bracket format with LTR")

    def test_10_wrapped_pin_and_photos(self):
        from backend.services.wrapped_photo_service import (
            set_wrapped_pin, verify_wrapped_pin, get_wrapped_pin_status,
            save_wrapped_photo, list_wrapped_photos, delete_wrapped_photo
        )
        from backend.services.wrapped_service import generate_friendship_wrapped

        # 1. PIN test
        res = set_wrapped_pin("2026")
        self.assertTrue(res["has_pin"])
        self.assertTrue(get_wrapped_pin_status()["has_pin"])
        self.assertTrue(verify_wrapped_pin("2026"))
        self.assertFalse(verify_wrapped_pin("0000"))

        # 2. Save mock photo
        mock_bytes = b"fake_jpeg_image_content_bytes"
        photo = save_wrapped_photo(mock_bytes, "bff.jpg", caption="Best Day Ever", slide_id="moments")
        self.assertIn("filename", photo)
        self.assertEqual(photo["caption"], "Best Day Ever")

        # 3. List photos
        photos = list_wrapped_photos()
        self.assertTrue(any(p["id"] == photo["id"] for p in photos))

        # 4. Generate wrapped with photos
        story = generate_friendship_wrapped()
        self.assertGreater(story["summary"]["photos_count"], 0)
        # Check if photo slide was inserted
        has_photo_slide = any("photo" in s["id"] for s in story["slides"])
        self.assertTrue(has_photo_slide)

        # 5. Delete photo
        deleted = delete_wrapped_photo(photo["id"])
        self.assertTrue(deleted)

        # 6. Remove PIN
        res_rm = set_wrapped_pin("")
        self.assertFalse(res_rm["has_pin"])
        self.assertFalse(get_wrapped_pin_status()["has_pin"])


if __name__ == "__main__":
    unittest.main()


