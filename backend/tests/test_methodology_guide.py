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
