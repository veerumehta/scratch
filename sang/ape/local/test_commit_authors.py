"""Tests for commit_authors.py and the attribution check's use of it.

Author: Virendra Mehta <virendra.mehta@jazzx.ai>

    python -m pytest scripts/local/test_commit_authors.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check_attribution as attribution  # noqa: E402
import commit_authors as authors  # noqa: E402

OURS, THEIRS = "veeru", "contributor@example.test"


def git(repo: Path, *args: str, email: str = OURS) -> None:
    env = {"GIT_AUTHOR_NAME": "n", "GIT_AUTHOR_EMAIL": email, "GIT_COMMITTER_NAME": "n",
           "GIT_COMMITTER_EMAIL": email, "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin"}
    subprocess.run(["git", *args], cwd=repo, env=env, check=True, capture_output=True)


def add(repo: Path, name: str, text: str, *, email: str) -> None:
    (repo / name).write_text(text)
    git(repo, "add", name)
    git(repo, "commit", "-m", f"add {name}", email=email)


def repo_with_two_authors(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q", "-b", "main")
    add(tmp_path, "base.py", "x = 1\n", email=OURS)
    git(tmp_path, "checkout", "-q", "-b", "work")
    add(tmp_path, "theirs.py", "y = 2\n", email=THEIRS)
    add(tmp_path, "ours.py", "z = 3\n", email=OURS)
    return tmp_path


def test_a_file_added_by_another_author_is_listed_with_that_author(tmp_path):
    repo = repo_with_two_authors(tmp_path)
    assert authors.foreign_added("main", own_emails={OURS}, cwd=repo) == {"theirs.py": THEIRS}


def test_a_foreign_file_we_only_renamed_is_still_theirs(tmp_path):
    repo = repo_with_two_authors(tmp_path)
    git(repo, "mv", "theirs.py", "moved.py")
    git(repo, "commit", "-m", "move it", email=OURS)
    assert authors.foreign_added("main", own_emails={OURS}, cwd=repo) == {"moved.py": THEIRS}


def test_the_check_skips_and_lists_a_foreign_file_but_still_fails_one_of_ours(tmp_path, capsys, monkeypatch):
    repo = repo_with_two_authors(tmp_path)
    monkeypatch.chdir(repo)
    monkeypatch.setattr(authors, "own_emails", lambda: {OURS})

    assert attribution.check([Path("theirs.py")], base="main") == 0
    out = capsys.readouterr().out
    assert "skipped" in out and "theirs.py" in out and THEIRS in out

    assert attribution.check([Path("ours.py")], base="main") == 1
    assert "MISSING attribution  ours.py" in capsys.readouterr().out
