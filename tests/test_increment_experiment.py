# tests/test_create_experiment.py

import pytest
from pathlib import Path
import shutil
import os
import sys


sys.path.insert(0, "/workspaces/ExecutionAgent/experimental_setups")
import increment_experiment as ce

@pytest.fixture
def tmp_root(tmp_path):
    """Make a fresh temporary directory and yield its Path."""
    return tmp_path / "exp_root"

def test_read_last_experiment_empty(tmp_root):
    # No file exists yet
    file = tmp_root / "experiments_list.txt"
    assert ce.read_last_experiment(file) == 0

def test_read_last_experiment_with_valid_lines(tmp_root):
    file = tmp_root / "experiments_list.txt"
    file.parent.mkdir(parents=True)
    file.write_text("experiment_1\nexperiment_5\nexperiment_3\n")
    assert ce.read_last_experiment(file) == 5

def test_read_last_experiment_ignores_bad_lines(tmp_root, caplog):
    file = tmp_root / "experiments_list.txt"
    file.parent.mkdir(parents=True)
    file.write_text("experiment_2\nfoo_bar\nexperiment_x\nexperiment_4\n")
    caplog.set_level("WARNING")
    result = ce.read_last_experiment(file)
    assert result == 4
    assert "Ignoring unrecognized line: 'foo_bar'" in caplog.text or \
           "Found invalid experiment index" in caplog.text

def test_create_and_append(tmp_root):
    base = tmp_root
    # First experiment
    new_id = 1
    ce.create_experiment_dirs(base, new_id)
    assert (base / f"experiment_{new_id}" / "logs").is_dir()
    # Append record
    record = base / "experiments_list.txt"
    ce.append_experiment_record(record, new_id)
    content = record.read_text().splitlines()
    assert content == ["experiment_1"]

    # Next experiment
    next_id = 2
    ce.create_experiment_dirs(base, next_id)
    ce.append_experiment_record(record, next_id)
    assert record.read_text().splitlines() == ["experiment_1", "experiment_2"]

def test_duplicate_experiment_error(tmp_root):
    base = tmp_root
    exp_id = 1
    # first time succeeds
    ce.create_experiment_dirs(base, exp_id)
    # second time should raise
    with pytest.raises(ce.ExperimentError):
        ce.create_experiment_dirs(base, exp_id)

def test_main_cli(tmp_path, monkeypatch, capsys):
    root = tmp_path / "my_exps"
    # simulate empty folder
    monkeypatch.chdir(tmp_path)
    # call main with custom base-dir
    ce.main(args=["--base-dir", str(root)])
    captured = capsys.readouterr()
    # prints the new experiment id
    assert captured.out.strip() == "1"
    # folder created
    assert (root / "experiment_1" / "logs").exists()
    # list updated
    lines = (root / "experiments_list.txt").read_text().splitlines()
    assert lines == ["experiment_1"]

def test_main_failure(tmp_root, monkeypatch):
    # Simulate permission error by creating a file where a dir should be
    bad = tmp_root / "experiment_1"
    bad.parent.mkdir(parents=True)
    bad.write_text("")  # now cannot mkdir over a file
    with pytest.raises(SystemExit) as exc:
        ce.main(args=["--base-dir", str(tmp_root)])
    assert exc.value.code == 1
