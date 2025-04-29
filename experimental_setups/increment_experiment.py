import argparse
import logging
from pathlib import Path
import re
import sys

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


class ExperimentError(Exception):
    pass


def read_last_experiment(experiments_list: Path) -> int:
    """
    Read the experiments_list file, parse valid entries like 'experiment_<n>',
    and return the highest n found, or 0 if none.
    """
    if not experiments_list.exists():
        logger.info(f"{experiments_list} does not exist. Starting at 0.")
        return 0

    max_id = 0
    pattern = re.compile(r"^experiment_(\d+)$")
    for line in experiments_list.read_text().splitlines():
        match = pattern.match(line.strip())
        if match:
            try:
                idx = int(match.group(1))
                max_id = max(max_id, idx)
            except ValueError:
                logger.warning(f"Found invalid experiment index in line: {line!r}")
        else:
            logger.warning(f"Ignoring unrecognized line: {line!r}")
    return max_id


def create_experiment_dirs(base_dir: Path, exp_id: int) -> None:
    """
    Create the folder structure for a new experiment.
    Raises ExperimentError if something goes wrong.
    """
    exp_dir = base_dir / f"experiment_{exp_id}"
    subdirs = ["logs", "responses", "saved_contexts", "files"]

    if exp_dir.exists():
        raise ExperimentError(f"Experiment directory already exists: {exp_dir}")

    try:
        for sub in subdirs:
            (exp_dir / sub).mkdir(parents=True, exist_ok=False)
        logger.info(f"Created experiment directories under {exp_dir}")
    except Exception as e:
        raise ExperimentError(f"Failed to create experiment directories: {e}")


def append_experiment_record(experiments_list: Path, exp_id: int) -> None:
    """
    Append a new 'experiment_<exp_id>' line to the experiments_list file.
    """
    try:
        experiments_list.parent.mkdir(parents=True, exist_ok=True)
        with experiments_list.open("a", encoding="utf-8") as f:
            f.write(f"experiment_{exp_id}\n")
        logger.info(f"Appended 'experiment_{exp_id}' to {experiments_list}")
    except Exception as e:
        raise ExperimentError(f"Failed to update {experiments_list}: {e}")


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Create a new experiment folder under <base_dir>."
    )
    parser.add_argument(
        "--base-dir",
        type=Path,
        default=Path("experimental_setups"),
        help="Root directory for experiments (default: experimental_setups)",
    )
    parsed = parser.parse_args(args)

    experiments_list = parsed.base_dir / "experiments_list.txt"
    try:
        last = read_last_experiment(experiments_list)
        new_id = last + 1
        logger.info(f"Next experiment ID: {new_id}")
        create_experiment_dirs(parsed.base_dir, new_id)
        append_experiment_record(experiments_list, new_id)
        print(new_id)
    except ExperimentError as e:
        logger.error(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
