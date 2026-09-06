import unittest
import os
import ast
from core.text_parser import TextParser
from core.memory import MemoryManager
from core.game_engine import GameEngine
from core.storage import StorageBackend, JsonFileStorage

class TestInvariants(unittest.TestCase):
    def test_malformed_and_empty_text_handling(self):
        # Empty or whitespace strings return empty list without crash
        self.assertEqual(TextParser.parse_lesson_text(""), [])
        self.assertEqual(TextParser.parse_lesson_text("   \n  \n  "), [])
        self.assertEqual(TextParser.parse_story_to_questions(""), [])

        # Incomplete line with no chunks
        incomplete = "Just a sentence with no pipe delimiter"
        self.assertEqual(TextParser.parse_lesson_text(incomplete), [])

    def test_unicode_and_devanagari_special_characters(self):
        hindi = "राम ने रावण को मारा। उसने विभीषण को राजा बनाया।"
        items = TextParser.parse_story_to_questions(hindi, words_per_chunk=2)
        self.assertEqual(len(items), 2)
        
        # Ensure serialization preserves Unicode characters
        serialized = TextParser.serialize_lesson_text(items)
        self.assertIn("राम ने", serialized)
        self.assertIn("विभीषण को", serialized)

    def test_memory_key_consistency(self):
        # Same question with different whitespace produces identical key
        key1 = MemoryManager.get_sentence_key("नमस्ते  भारत ", ["नमस्ते", "भारत"])
        key2 = MemoryManager.get_sentence_key("नमस्ते भारत", ["नमस्ते", "भारत"])
        self.assertEqual(key1, key2)

    def test_app_context_and_card_attempt_boundary(self):
        from core.app_context import AppContext
        from core.profile_manager import ProfileManager
        import tempfile
        import os

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name
        try:
            ProfileManager.set_filepath(temp_path)
            ctx = AppContext()
            res = ctx.record_card_attempt("key123", mode="mastery", flawless=True, now_ts=1000.0)
            self.assertIn('memory', res)
            self.assertIn('milestone', res)
            self.assertEqual(res['memory'].get('repetition_level'), 1)
            self.assertTrue(res['milestone']['has_mastery'])
        finally:
            from core.profile_manager import DEFAULT_PROFILES_FILE
            ProfileManager.set_filepath(DEFAULT_PROFILES_FILE)
            ProfileManager._data = None
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_core_does_not_import_ui(self):
        core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core'))
        disallowed_modules = {
            'ui', 'tkinter', 'PyQt', 'PyQt5', 'PyQt6', 'PySide', 'PySide2', 'PySide6', 'webview', 'pywebview'
        }
        violations = []

        for root, _, files in os.walk(core_dir):
            for filename in files:
                if filename.endswith('.py'):
                    filepath = os.path.join(root, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.Import):
                            for alias in node.names:
                                pkg = alias.name.split('.')[0]
                                if pkg in disallowed_modules:
                                    violations.append(f"{filename}:{node.lineno} imports '{alias.name}'")
                        elif isinstance(node, ast.ImportFrom):
                            if node.module:
                                pkg = node.module.split('.')[0]
                                if pkg in disallowed_modules:
                                    violations.append(f"{filename}:{node.lineno} imports from '{node.module}'")

        self.assertEqual(violations, [], "Core domain files must not import UI or GUI toolkits:\n" + "\n".join(violations))

    def test_core_has_zero_bare_exception_pass(self):
        core_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'core'))
        violations = []

        for root, _, files in os.walk(core_dir):
            for filename in files:
                if filename.endswith('.py'):
                    filepath = os.path.join(root, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        tree = ast.parse(f.read(), filename=filepath)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.ExceptHandler):
                            # Check 1: Bare except: without exception type
                            if node.type is None:
                                violations.append(f"{filename}:{node.lineno} bare except clause without exception type")
                            # Check 2: Pass only or silent swallow without logging
                            is_only_pass = (
                                len(node.body) == 1 and
                                (isinstance(node.body[0], ast.Pass) or
                                 (isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and node.body[0].value.value is ...))
                            )
                            if is_only_pass:
                                violations.append(f"{filename}:{node.lineno} silent exception swallow with 'pass'")

        self.assertEqual(violations, [], "Core domain files must not contain bare except or pass-swallowed exceptions:\n" + "\n".join(violations))

    def test_storage_backend_abstraction(self):
        self.assertTrue(issubclass(JsonFileStorage, StorageBackend))
        storage = JsonFileStorage()
        self.assertIsInstance(storage, StorageBackend)
        self.assertTrue(callable(getattr(storage, 'load', None)))
        self.assertTrue(callable(getattr(storage, 'save', None)))

        # Verify base class defines the interface and raises NotImplementedError
        base_storage = StorageBackend()
        with self.assertRaises(NotImplementedError):
            base_storage.load("dummy.json")
        with self.assertRaises(NotImplementedError):
            base_storage.save("dummy.json", {})

if __name__ == '__main__':
    unittest.main()
