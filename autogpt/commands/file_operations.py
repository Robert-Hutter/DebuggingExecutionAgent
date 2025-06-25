"""Commands to perform operations on files"""

from __future__ import annotations

COMMAND_CATEGORY = "file_operations"
COMMAND_CATEGORY_TITLE = "File Operations"

import contextlib
import hashlib
import os
import re
import os.path
from pathlib import Path
from typing import Generator, Literal

import xml.etree.ElementTree as ET
import yaml

from autogpt.agents.agent import Agent
from autogpt.command_decorator import command
from autogpt.logs import logger
from autogpt.memory.vector import MemoryItem, VectorMemory
from autogpt.commands.docker_helpers_static import (
    build_image,
    start_container,
    execute_command_in_container,
    write_string_to_file,
    read_file_from_container,
    check_image_exists,
    exec_in_screen_and_get_log,
    textify_output
    )

from .decorators import sanitize_path_arg
from .file_operations_utils import read_textual_file


def xml_to_dict(element):
    """ Recursively converts XML elements to a dictionary. """
    if len(element) == 0:
        return element.text
    return {
        element.tag: {
            child.tag: xml_to_dict(child) for child in element
        }
    }

def convert_xml_to_yaml(xml_file):
    # Parse the XML file
    tree = ET.parse(xml_file)
    root = tree.getroot()
    # Convert XML to a dictionary
    xml_dict = xml_to_dict(root)
    # Convert the dictionary to a YAML string
    yaml_str = yaml.dump(xml_dict, default_flow_style=False)
    return yaml_str

Operation = Literal["write", "append", "delete"]


def text_checksum(text: str) -> str:
    """Get the hex checksum for the given text."""
    return hashlib.md5(text.encode("utf-8")).hexdigest()


def operations_from_log(
    log_path: str | Path,
) -> Generator[tuple[Operation, str, str | None], None, None]:
    """Parse the file operations log and return a tuple containing the log entries"""
    try:
        log = open(log_path, "r", encoding="utf-8")
    except FileNotFoundError:
        return

    for line in log:
        line = line.replace("File Operation Logger", "").strip()
        if not line:
            continue
        operation, tail = line.split(": ", maxsplit=1)
        operation = operation.strip()
        if operation in ("write", "append"):
            try:
                path, checksum = (x.strip() for x in tail.rsplit(" #", maxsplit=1))
            except ValueError:
                logger.warn(f"File log entry lacks checksum: '{line}'")
                path, checksum = tail.strip(), None
            yield (operation, path, checksum)
        elif operation == "delete":
            yield (operation, tail.strip(), None)

    log.close()


def file_operations_state(log_path: str | Path) -> dict[str, str]:
    """Iterates over the operations log and returns the expected state.

    Parses a log file at config.file_logger_path to construct a dictionary that maps
    each file path written or appended to its checksum. Deleted files are removed
    from the dictionary.

    Returns:
        A dictionary mapping file paths to their checksums.

    Raises:
        FileNotFoundError: If config.file_logger_path is not found.
        ValueError: If the log file content is not in the expected format.
    """
    state = {}
    for operation, path, checksum in operations_from_log(log_path):
        if operation in ("write", "append"):
            state[path] = checksum
        elif operation == "delete":
            del state[path]
    return state


@sanitize_path_arg("filename")
def is_duplicate_operation(
    operation: Operation, filename: str, agent: Agent, checksum: str | None = None
) -> bool:
    """Check if the operation has already been performed

    Args:
        operation: The operation to check for
        filename: The name of the file to check for
        agent: The agent
        checksum: The checksum of the contents to be written

    Returns:
        True if the operation has already been performed on the file
    """
    # Make the filename into a relative path if possible
    with contextlib.suppress(ValueError):
        filename = str(Path(filename).relative_to(agent.workspace.root))

    state = file_operations_state(agent.config.file_logger_path)
    if operation == "delete" and filename not in state:
        return True
    if operation == "write" and state.get(filename) == checksum:
        return True
    return False


@sanitize_path_arg("filename")
def log_operation(
    operation: Operation, filename: str, agent: Agent, checksum: str | None = None
) -> None:
    """Log the file operation to the file_logger.txt

    Args:
        operation: The operation to log
        filename: The name of the file the operation was performed on
        checksum: The checksum of the contents to be written
    """
    # Make the filename into a relative path if possible
    with contextlib.suppress(ValueError):
        filename = str(Path(filename).relative_to(agent.workspace.root))

    log_entry = f"{operation}: {filename}"
    if checksum is not None:
        log_entry += f" #{checksum}"
    logger.debug(f"Logging file operation: {log_entry}")
    append_to_file(
        agent.config.file_logger_path, f"{log_entry}\n", agent, should_log=False
    )


@command(
    "read_file",
    "Read an existing file",
    {
        "file_path": {
            "type": "string",
            "description": "The path of the file to read",
            "required": True,
        }
    },
)
def read_file(file_path: str, agent: Agent) -> str:
    """Read a file and return the contents

    Args:
        filename (str): The name of the file to read

    Returns:
        str: The contents of the file
    """
    if not agent.container:
        print("READING FILE FROM OUTSIDE CONTAINER CRAZZZZZZZZZZZZZZZZZZZZZY")
        try:
            workspace = agent.workspace_path
            project_path = agent.project_path
            if file_path.lower().endswith("xml"):
                yaml_content = convert_xml_to_yaml(os.path.join(workspace, project_path, file_path))
                return \
                    "The xml file was converted to yaml format for better readability:\n{}".format(
                    yaml_content
                )
            content = read_textual_file(os.path.join(workspace, project_path, file_path), logger)
            return content
            # TODO: invalidate/update memory when file is edited
            file_memory = MemoryItem.from_text_file(content, file_path, agent.config)
            if len(file_memory.chunks) > 1:
                return file_memory.summary

            return content
        except Exception as e:
            return f"Error: {str(e)}"
    else:
        return "The read_file tool always assumes that you are in directory {}\n".format(
            os.path.join("/app", agent.project_path)
            ) + \
        "This means that the read_file tool is trying to read the file from: {}\n".format(
            os.path.join("/app", agent.project_path, file_path)
            ) + \
        "If this returns an error or this is not the path you meant, you should explicitly pass an absolute file path to the read_file tool[REMEMBER THIS DETAIL].\n" + \
        read_file_from_container(
            agent.container,
            os.path.join("/app", agent.project_path, file_path)
            )


def ingest_file(
    filename: str,
    memory: VectorMemory,
) -> None:
    """
    Ingest a file by reading its content, splitting it into chunks with a specified
    maximum length and overlap, and adding the chunks to the memory storage.

    Args:
        filename: The name of the file to ingest
        memory: An object with an add() method to store the chunks in memory
    """
    try:
        logger.info(f"Ingesting file {filename}")
        content = read_file(filename)

        # TODO: differentiate between different types of files
        file_memory = MemoryItem.from_text_file(content, filename)
        logger.debug(f"Created memory: {file_memory.dump(True)}")
        memory.add(file_memory)

        logger.info(f"Ingested {len(file_memory.e_chunks)} chunks from {filename}")
    except Exception as err:
        logger.warn(f"Error while ingesting file '{filename}': {err}")

def update_dockerfile_content(dockerfile_content: str) -> str:
    lines = dockerfile_content.splitlines()
    modified_lines = []
    in_run_command = False
    for line in lines:
        stripped_line = line.strip()      
        # Check if the line starts with 'RUN' and is not a continuation of a previous 'RUN' command
        if stripped_line.startswith("RUN ") and not in_run_command:
            in_run_command = True
            if stripped_line.endswith("\\"):
                modified_lines.append(line.rstrip())
            else:
                # Add || exit 0 with an error message
                modified_lines.append(
                    line.rstrip() + " || { echo \"Command failed with exit code $?\"; exit 0; }"
                )
                in_run_command = False
        elif in_run_command:
            # Check if the line ends with '\', which indicates continuation
            if stripped_line.endswith("\\"):
                modified_lines.append(line)
            else:
                in_run_command = False
                # Add || exit 0 with an error message
                modified_lines.append(
                    line.rstrip() + " || { echo \"Command failed with exit code $?\"; exit 0; }"
                )
        else:
            modified_lines.append(line)

    return "\n".join(modified_lines)

@command(
    "write_to_file",
    "Writes to a file",
    {
        "filename": {
            "type": "string",
            "description": "The name of the file to write to",
            "required": True,
        },
        "text": {
            "type": "string",
            "description": "The text to write to the file",
            "required": True,
        },
    },
    aliases=["write_file", "create_file"],
)
def write_to_file(filename: str, text: str, agent: Agent) -> str:
    """
    Robustly write text to file or container with Docker handling.

    Args:
        filename: Relative path under the workspace/project or absolute path in container.
        text: Content to write.
        agent: Execution agent with workspace, project_path, container, and helpers.

    Returns:
        Status message indicating success or detailed failure.
    """
    # Normalize filename for Dockerfile detection; preserve original for container writes
    normalized = os.path.normpath(filename)
    base = os.path.basename(normalized)
    is_dockerfile = base.lower() == 'dockerfile' or base.lower().endswith('.dockerfile')

    # Only enforce COPY prohibition in Dockerfiles
    if is_dockerfile and 'COPY ' in text:
        return (
            "Usage of 'COPY' in Dockerfile is prohibited. "
            "Clone the repository inside the image instead."
        )

    try:
        if not agent.container:
            return _write_locally(normalized, text, agent, is_dockerfile)
        else:
            return _write_in_container(filename, text, agent, is_dockerfile)

    except Exception as e:
        logger.debug("Failed to write file %s", filename)
        return f"Error writing '{filename}': {e}"


def _write_locally(filename: str, text: str, agent: Agent, is_dockerfile: bool) -> str:
    # Normalize and reject absolute paths
    if os.path.isabs(filename):
        return f"Error: absolute paths are not allowed: {filename}"
    filename = os.path.normpath(filename)

    workspace = os.path.abspath(agent.workspace_path)
    project = agent.project_path

    # Resolve full path under workspace
    if filename.startswith(project + os.sep):
        rel = filename[len(project) + 1:]
        full_path = os.path.join(workspace, rel)
    else:
        full_path = os.path.join(workspace, project, filename)
    full_path = os.path.abspath(full_path)

    # Prevent path traversal
    if not full_path.startswith(workspace + os.sep):
        return f"Error: path traversal detected: {filename}"

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(full_path), exist_ok=True)

    # Write file
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(text)

    # Record successful write
    agent.written_files.append((filename, text))
    logger.info("Wrote file %s", full_path)

    # Dockerfile-specific workflow
    if is_dockerfile:
        return _handle_dockerfile(full_path, text, agent)

    return "File written successfully."


def _handle_dockerfile(full_path: str, text: str, agent: Agent) -> str:
    lines = text.splitlines()
    run_cmds = sum(1 for line in lines if line.strip().upper().startswith('RUN '))

    if len(lines) > 30 or run_cmds > 20:
        return (
            "Dockerfile too long. Keep it minimal: base image, system packages, "
            "and runtime. Install app dependencies later in a running container."
        )

    tag = f"{agent.project_path.lower()}_image:executionagent"
    if not check_image_exists(tag):
        build_log = build_image(os.path.dirname(full_path), tag)
        if 'error' in build_log.lower():
            return (
                "Error building Docker image. Simplify your Dockerfile and try again:\n"
                f"{build_log}"
            )

    container = start_container(tag)
    if not container:
        return f"Error: failed to start container for image {tag}"

    agent.container = container
    cwd_raw = execute_command_in_container(container, "pwd")
    cwd = _sanitize_cwd(cwd_raw)
    return (
        f"Image built and container started. Working directory: {cwd}"
    )


def _sanitize_cwd(raw: str) -> str:
    # Strip control codes and whitespace
    text = raw.strip()
    # Take last line only
    last = text.splitlines()[-1]
    # Remove any prompt prefix ending with '#' or '$'
    last = re.sub(r'^.*[#\$]\s*', '', last)
    return last


def _write_in_container(
    filename: str, text: str, agent: Agent, is_dockerfile: bool
) -> str:
    # Prevent new Dockerfile in container
    if is_dockerfile:
        return (
            "Cannot write another Dockerfile after container is running. "
            "Debug inside with linux_terminal tool."
        )

    # Determine working directory inside container
    _, pwd_out, _, stuck = exec_in_screen_and_get_log(agent.container, "pwd")
    cwd = _sanitize_cwd(pwd_out) if not stuck else f"/app/{agent.project_path}"

    # Determine target path: absolute stays, relative is under cwd
    if os.path.isabs(filename):
        target = filename
    else:
        target = os.path.normpath(os.path.join(cwd, filename))

    # Write into container at target path
    result = write_string_to_file(agent.container, text, target)
    if result is None:
        agent.written_files.append((filename, text))
        base = os.path.basename(filename)
        if base.lower().endswith(('.sh', 'setup', 'install')):
            return (
                f"File written successfully to {target}"
            )
        return f"File written successfully to {target}"

    return f"Error writing in container: {result}"