"""The conformance kit (conformance/) passes against the reference implementation, matches the golden fixtures, and can fail."""
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent
KIT = ROOT / "conformance"
CASES = KIT / "cases"
GOLDEN = ROOT / "tests" / "golden" / "spec"
CHECK = [sys.executable, str(KIT / "check.py")]
ENCODER = f"{sys.executable} {KIT / 'reference' / 'encode.py'}"
DECODER = f"{sys.executable} {KIT / 'reference' / 'decode.py'}"


def check(*args):
    return subprocess.run([*CHECK, *args], capture_output=True, text=True, encoding="utf-8")


def test_kit_is_well_formed():
    r = check("--validate")
    assert r.returncode == 0, r.stdout


def test_reference_implementation_passes_the_whole_kit():
    r = check("--encoder", ENCODER, "--decoder", DECODER)
    assert r.returncode == 0, r.stdout
    assert "FAIL" not in r.stdout


def test_expected_files_are_what_the_reference_implementation_writes():
    r = subprocess.run([sys.executable, str(KIT / "reference" / "regenerate.py"), "--check"], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr


def test_spec_fixtures_are_cases_in_the_kit():
    for golden in sorted(GOLDEN.glob("*.sheet.md")):
        assert (CASES / golden.name[: -len(".sheet.md")] / "expected.sheet.md").read_bytes() == golden.read_bytes(), golden.name


def test_every_spec_section_with_a_normative_rule_is_exercised():
    covered = " ".join(json.loads(p.read_text(encoding="utf-8"))["spec"] for p in CASES.glob("*/case.json"))
    for section in ("§2", "§3", "§4", "§5.1", "§5.3", "§6.1", "§6.2", "§7", "§8", "§9", "§12"):
        assert section in covered, section


@pytest.mark.parametrize("breakage", [
    "sys.stdout.write(sys.stdin.read())",                      # prints nothing useful
    "print('---')",
])
def test_checker_fails_a_wrong_encoder(breakage):
    r = check("--encoder", f'{sys.executable} -c "{breakage}"', "--only", "01")
    assert r.returncode == 1 and "FAIL" in r.stdout


def test_checker_fails_a_decoder_that_accepts_a_file_it_must_reject():
    r = check("--decoder", f"{sys.executable} -c \"print('{{\\\"sheets\\\": []}}')\"", "--only", "15")
    assert r.returncode == 1 and "must be rejected" in r.stdout


def test_checker_fails_a_decoder_that_gets_one_cell_wrong(tmp_path):
    good = KIT / "cases" / "01_minimal" / "decoded.json"
    doc = json.loads(good.read_text(encoding="utf-8"))
    doc["sheets"][0]["cells"]["B2"]["v"] = 121
    fake = tmp_path / "fake.json"
    fake.write_text(json.dumps(doc), encoding="utf-8")
    r = check("--decoder", f'{sys.executable} -c "import sys;print(open(r\'{fake}\').read())"', "--only", "01")
    assert r.returncode == 1 and "differs" in r.stdout


def test_checker_distinguishes_boolean_from_number(tmp_path):
    doc = json.loads((KIT / "cases" / "18_read_cells" / "decoded.json").read_text(encoding="utf-8"))
    doc["sheets"][0]["cells"]["B4"]["v"] = 1          # TRUE decoded as the number 1
    fake = tmp_path / "fake.json"
    fake.write_text(json.dumps(doc), encoding="utf-8")
    r = check("--decoder", f'{sys.executable} -c "import sys;print(open(r\'{fake}\').read())"', "--only", "18")
    assert r.returncode == 1


def test_loose_error_constants_keep_their_type():
    """Regression found by the kit: a typed error in a loose cell was written as text (`'#N/A`)."""
    text = (CASES / "12_loose_cells" / "expected.sheet.md").read_text(encoding="utf-8")
    assert "\nM1: #N/A\n" in text
