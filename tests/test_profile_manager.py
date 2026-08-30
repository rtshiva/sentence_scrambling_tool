import unittest
import os
import tempfile
from core.profile_manager import ProfileManager

class TestProfileManager(unittest.TestCase):
    def setUp(self):
        self.temp_file = os.path.join(tempfile.gettempdir(), f"test_profiles_{os.getpid()}.json")
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)
        ProfileManager.set_filepath(self.temp_file)

    def tearDown(self):
        if os.path.exists(self.temp_file):
            os.remove(self.temp_file)

    def test_create_and_switch_profile(self):
        self.assertIn("Default", ProfileManager.get_profile_names())
        self.assertEqual(ProfileManager.get_active_profile_name(), "Default")

        # Create Arya
        self.assertTrue(ProfileManager.create_profile("Arya", "🦁"))
        self.assertEqual(ProfileManager.get_active_profile_name(), "Arya")
        self.assertIn("Arya", ProfileManager.get_profile_names())

        # Cannot duplicate
        self.assertFalse(ProfileManager.create_profile("Arya", "🦁"))

        # Switch back to Default
        self.assertTrue(ProfileManager.switch_profile("Default"))
        self.assertEqual(ProfileManager.get_active_profile_name(), "Default")

    def test_isolated_settings_and_memory(self):
        ProfileManager.create_profile("UserA", "🦁")
        ProfileManager.create_profile("UserB", "🚀")

        ProfileManager.switch_profile("UserA")
        s_a = ProfileManager.get_settings()
        s_a['speed_run_duration_seconds'] = 300
        ProfileManager.save_settings(s_a)
        mem_a = ProfileManager.get_active_memory_store()
        mem_a["item1"] = {"repetition_level": 3}
        ProfileManager._save()

        ProfileManager.switch_profile("UserB")
        s_b = ProfileManager.get_settings()
        mem_b = ProfileManager.get_active_memory_store()
        self.assertEqual(s_b['speed_run_duration_seconds'], 180) # Default
        self.assertNotIn("item1", mem_b)

    def test_delete_profile_safeguard(self):
        # Cannot delete last profile
        self.assertFalse(ProfileManager.delete_profile("Default"))

        ProfileManager.create_profile("TempUser", "🐼")
        self.assertTrue(ProfileManager.delete_profile("TempUser"))
        self.assertNotIn("TempUser", ProfileManager.get_profile_names())

if __name__ == '__main__':
    unittest.main()
