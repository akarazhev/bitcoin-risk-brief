import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COPY = ROOT / "frontend" / "src" / "methodologyCopy.ts"


def _constant(name: str) -> str:
    match = re.search(rf"export const {name} = ([^\n]+)", COPY.read_text(encoding="utf-8"))
    assert match is not None, f"{name} must be exported from methodologyCopy.ts"
    return match.group(1).strip().rstrip(";").strip("'\"")


class MethodologyGuideTests(unittest.TestCase):
    def test_the_guide_states_the_boundaries_the_backend_uses(self) -> None:
        from app.risk import HIGH_RISK_THRESHOLD, LOW_RISK_THRESHOLD, METHODOLOGY_VERSION

        self.assertEqual(float(_constant("BAND_LOW")), LOW_RISK_THRESHOLD)
        self.assertEqual(float(_constant("BAND_HIGH")), HIGH_RISK_THRESHOLD)
        self.assertEqual(_constant("METHODOLOGY_VERSION"), METHODOLOGY_VERSION)

    def test_the_english_guide_shows_the_boundaries_it_declares(self) -> None:
        # The constants can be right while the prose says something else. Assert the reader sees them.
        text = COPY.read_text(encoding="utf-8")
        self.assertIn("0.30", text)
        self.assertIn("0.70", text)
        self.assertIn("crypto-scout-canonical-v1.1", text)

    def test_the_guide_does_not_overstate_the_freshness_contract(self) -> None:
        # frontend/public/llms.txt was corrected for this exact misconception and is guarded by
        # test_agent_surface.py. The guide must not reintroduce it. These phrases are English, so
        # scanning the whole file is both sufficient and safe: a translation cannot contain them.
        english = " ".join(COPY.read_text(encoding="utf-8").split()).lower()
        for overstatement in (
            "503 rather than a stale figure",
            "stamped on every response",
            "travels with every response",
            "version on every response",
        ):
            self.assertNotIn(
                overstatement,
                english,
                "only /api/readiness answers 503 for stale data; the data endpoints keep serving "
                "stored rows, and the methodology version is not on every response",
            )
        self.assertIn("readiness", english)

    def test_the_guide_does_not_republish_the_model_weights(self) -> None:
        text = COPY.read_text(encoding="utf-8")
        # Only the three weights are safe to forbid as substrings. 0.30 and 0.70 are also the band
        # boundaries the guide must state, and 0.25 appears in the worked example, so a broader
        # substring ban would fail against correct copy.
        for weight in ("0.60", "0.15"):
            self.assertNotIn(
                weight,
                text,
                "model weights belong to the documentation-site reference, not the guide",
            )
