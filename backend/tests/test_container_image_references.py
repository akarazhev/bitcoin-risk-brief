from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


def _is_fully_qualified(image: str) -> bool:
    if "/" not in image:
        return False
    if image.startswith("localhost/"):
        return True
    registry = image.split("/", 1)[0]
    return "." in registry or ":" in registry


class ContainerImageReferenceTests(unittest.TestCase):
    def test_dockerfiles_use_fully_qualified_base_images(self) -> None:
        dockerfiles = [
            ROOT / "backend" / "Dockerfile",
            ROOT / "collector" / "Dockerfile",
            ROOT / "frontend" / "Dockerfile",
        ]

        short_names: list[str] = []
        for dockerfile in dockerfiles:
            for line in dockerfile.read_text().splitlines():
                match = re.match(r"^FROM\s+([^\s]+)", line)
                if match and not _is_fully_qualified(match.group(1)):
                    short_names.append(f"{dockerfile.relative_to(ROOT)}: {match.group(1)}")

        self.assertEqual([], short_names)

    def test_compose_files_use_fully_qualified_images(self) -> None:
        compose_files = [
            ROOT / "podman-compose.yml",
            ROOT / "podman-compose.cloudflare.yml",
        ]

        short_names: list[str] = []
        for compose_file in compose_files:
            for line in compose_file.read_text().splitlines():
                match = re.match(r"^\s*image:\s+(.+?)\s*$", line)
                if not match:
                    continue
                image = match.group(1).strip('"').strip("'")
                default_match = re.match(r"\$\{[^:}]+:-(.+)\}", image)
                if default_match:
                    image = default_match.group(1)
                if not _is_fully_qualified(image):
                    short_names.append(f"{compose_file.relative_to(ROOT)}: {image}")

        self.assertEqual([], short_names)


if __name__ == "__main__":
    unittest.main()
