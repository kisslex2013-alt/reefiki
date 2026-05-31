import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class PublicSnapshotGuardTests(unittest.TestCase):
    def test_all_real_projects_are_listed_as_private(self):
        projects_root = ROOT / "projects"
        actual_projects = sorted(
            path.name for path in projects_root.iterdir() if path.is_dir() and path.name != "_template"
        )
        config_path = ROOT / "scripts" / "public-snapshot.private-projects.txt"
        configured = sorted(
            line.strip()
            for line in config_path.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        )
        self.assertEqual(actual_projects, configured)


if __name__ == "__main__":
    unittest.main()
