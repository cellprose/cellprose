"""Git diff driver and pre-commit hook, exercised against a real temporary repository."""
import subprocess
from pathlib import Path

import openpyxl
import pytest

from cellprose import gitflow
from cellprose.cli import main


def make_xlsx(path: Path, value=1):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Data"
    ws.append(["Item", "Qty"])
    ws.append(["Bolt", value])
    wb.save(path)


def git(repo, *args):
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout


@pytest.fixture
def repo(tmp_path, monkeypatch):
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.email", "t@example.com")
    git(tmp_path, "config", "user.name", "t")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_textconv_omits_source_and_is_stable(tmp_path):
    a = tmp_path / "tmpA.xlsx"
    make_xlsx(a)
    text = gitflow.textconv(a)
    assert "source:" not in text and "tmpA" not in text
    assert "\n2|Bolt|1\n" in text.replace(" ", "")
    assert text == gitflow.textconv(a)


def test_sidecar_name():
    assert gitflow.sidecar(Path("a/b/book.xlsx")) == Path("a/b/book" + gitflow.EXT)


def test_setup_is_idempotent(repo):
    gitflow.setup(repo)
    gitflow.setup(repo)
    assert (repo / ".gitattributes").read_text().count(gitflow.ATTRIBUTES_LINE) == 1
    assert git(repo, "config", "diff.cellprose.textconv").strip() == "cellprose textconv"
    hook = repo / ".git" / "hooks" / "pre-commit"
    assert hook.read_text().count(gitflow.HOOK_MARK) == 1


def test_git_diff_uses_driver(repo, monkeypatch):
    gitflow.setup(repo, hook=False)
    # the textconv command is `cellprose textconv`; point it at this interpreter's CLI
    import sys
    git(repo, "config", "diff.cellprose.textconv", f"{sys.executable} -m cellprose.cli textconv")
    make_xlsx(repo / "b.xlsx", 1)
    git(repo, "add", "."); git(repo, "commit", "-qm", "one")
    make_xlsx(repo / "b.xlsx", 2)
    diff = git(repo, "diff")
    assert "-2|Bolt|1" in diff.replace(" ", "") and "+2|Bolt|2" in diff.replace(" ", "")
    assert "Binary files" not in diff


def test_precommit_adds_updates_and_removes_sidecar(repo):
    make_xlsx(repo / "b.xlsx", 1)
    git(repo, "add", "b.xlsx")
    assert gitflow.precommit() == 0
    side = "b" + gitflow.EXT
    assert side in git(repo, "diff", "--cached", "--name-only").split()
    assert "source: b.xlsx" in (repo / side).read_text()
    git(repo, "commit", "-qm", "add")

    make_xlsx(repo / "b.xlsx", 2)
    git(repo, "add", "b.xlsx")
    gitflow.precommit()
    assert "\n2|Bolt|2\n" in (repo / side).read_text().replace(" ", "")
    git(repo, "commit", "-qm", "edit")

    git(repo, "rm", "-q", "b.xlsx")
    gitflow.precommit()
    assert side not in git(repo, "ls-files")


def test_precommit_encodes_staged_not_working_copy(repo):
    make_xlsx(repo / "b.xlsx", 1)
    git(repo, "add", "b.xlsx")
    make_xlsx(repo / "b.xlsx", 99)  # unstaged change
    gitflow.precommit()
    assert "99" not in (repo / ("b" + gitflow.EXT)).read_text()


def test_precommit_ignores_other_files_and_reports_bad_workbook(repo, capsys):
    (repo / "notes.txt").write_text("x")
    (repo / "bad.xlsx").write_text("not a zip")
    git(repo, "add", ".")
    assert gitflow.precommit() == 1
    assert "bad.xlsx" in capsys.readouterr().err
    assert not (repo / ("bad" + gitflow.EXT)).exists()


def test_cli_textconv(tmp_path, capsys):
    make_xlsx(tmp_path / "c.xlsx")
    assert main(["textconv", str(tmp_path / "c.xlsx")]) == 0
    assert "Sheet: Data" in capsys.readouterr().out
