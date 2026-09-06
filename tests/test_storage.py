import unittest
import os
import tempfile
import json
from unittest.mock import patch
from core.storage import StorageBackend, JsonFileStorage
from core.profile_manager import ProfileManager

class TestStorage(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_data.json")

    def tearDown(self):
        for ext in ("", ".tmp", ".bak"):
            p = self.test_file + ext
            if os.path.exists(p):
                try: os.remove(p)
                except Exception: pass
        if os.path.exists(self.test_dir):
            try: os.rmdir(self.test_dir)
            except Exception: pass

    def test_storage_backend_interface(self):
        backend = StorageBackend()
        with self.assertRaises(NotImplementedError):
            backend.load(self.test_file)
        with self.assertRaises(NotImplementedError):
            backend.save(self.test_file, {})

    def test_json_file_storage_save_and_load(self):
        storage = JsonFileStorage()
        data = {"key": "value", "items": [1, 2, 3]}

        success = storage.save(self.test_file, data)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.test_file))
        self.assertTrue(os.path.exists(self.test_file + ".bak"))

        loaded = storage.load(self.test_file)
        self.assertEqual(loaded, data)

    def test_json_file_storage_load_backup_recovery(self):
        storage = JsonFileStorage()
        data = {"recovered": True}
        storage.save(self.test_file, data)

        # Corrupt the primary file
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("{invalid_json")

        loaded = storage.load(self.test_file)
        self.assertEqual(loaded, data)

    def test_json_file_storage_load_nonexistent(self):
        storage = JsonFileStorage()
        self.assertIsNone(storage.load(os.path.join(self.test_dir, "nonexistent.json")))

    def test_json_file_storage_fallback_direct_write(self):
        storage = JsonFileStorage()
        data = {"fallback": True}

        # Mock os.replace to raise an exception, triggering fallback to direct write
        with patch("os.replace", side_effect=OSError("Atomic replace failed")):
            success = storage.save(self.test_file, data)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(self.test_file))
            loaded = storage.load(self.test_file)
            self.assertEqual(loaded, data)

    def test_profile_manager_storage_injection(self):
        class MockStorage(StorageBackend):
            def __init__(self):
                self.saved_data = None
            def load(self, filepath):
                return {"active_profile": "MockUser", "profiles": {"MockUser": {"avatar": "🤖", "settings": {}, "memory": {}, "tracker": {}}}}
            def save(self, filepath, data):
                self.saved_data = data
                return True

        original_storage = ProfileManager.get_storage()
        try:
            mock = MockStorage()
            ProfileManager.set_storage(mock)
            self.assertEqual(ProfileManager.get_active_profile_name(), "MockUser")
            self.assertIn("MockUser", ProfileManager.get_profile_names())
        finally:
            ProfileManager.set_storage(original_storage)


if __name__ == '__main__':
    unittest.main()
