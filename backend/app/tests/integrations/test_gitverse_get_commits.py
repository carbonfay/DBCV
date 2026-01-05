import unittest
from backend.app.integrations.gitverse.get_commits import GitVerseGetCommits


class TestGitVerseGetCommits(unittest.TestCase):
    def setUp(self):
        self.integration = GitVerseGetCommits()

    def test_execute_success(self):
        config = {
            "project_id": "12345",
            "ref_name": "main"
        }
        result = self.integration.execute(config)
        self.assertTrue(result["success"])

    def test_execute_missing_project_id(self):
        config = {}  # Нет project_id
        result = self.integration.execute(config)
        self.assertFalse(result["success"])
        self.assertIn("project_id", result["error"])
