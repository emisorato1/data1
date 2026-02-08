import unittest
from types import SimpleNamespace
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.agents.input_normalization import extract_message, normalize_user_role


class InputNormalizationTest(unittest.TestCase):
    def test_normalize_user_role_defaults_to_public(self):
        self.assertEqual(normalize_user_role(None), "public")
        self.assertEqual(normalize_user_role("admin"), "public")

    def test_normalize_user_role_private(self):
        self.assertEqual(normalize_user_role("private"), "private")
        self.assertEqual(normalize_user_role(" PRIVATE "), "private")

    def test_extract_message_from_direct_field(self):
        state = {"message": " hola ", "messages": []}
        self.assertEqual(extract_message(state), "hola")

    def test_extract_message_from_last_human_message(self):
        state = {
            "messages": [
                SimpleNamespace(type="ai", content="respuesta"),
                SimpleNamespace(type="human", content=" pregunta final "),
            ]
        }
        self.assertEqual(extract_message(state), "pregunta final")

    def test_extract_message_empty_when_not_present(self):
        self.assertEqual(extract_message({}), "")


if __name__ == "__main__":
    unittest.main()
