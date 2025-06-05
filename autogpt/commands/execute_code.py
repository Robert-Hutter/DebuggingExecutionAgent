"""Commands to execute code"""

COMMAND_CATEGORY = "execute_code"
COMMAND_CATEGORY_TITLE = "Execute Code"

import os
import subprocess
from pathlib import Path

import docker
from docker.errors import DockerException, ImageNotFound
from docker.models.containers import Container as DockerContainer
from autogpt.commands.docker_helpers_static import execute_command_in_container, read_file_from_container, remove_progress_bars, textify_output, extract_test_sections
from autogpt.agents.agent import Agent
from autogpt.command_decorator import command
from autogpt.config import Config
from autogpt.logs import logger

from .decorators import sanitize_path_arg

ALLOWLIST_CONTROL = "allowlist"
DENYLIST_CONTROL = "denylist"


@command(
    "execute_python_code",
    "Creates a Python file and executes it",
    {
        "code": {
            "type": "string",
            "description": "The Python code to run",
            "required": True,
        },
        "name": {
            "type": "string",
            "description": "A name to be given to the python file",
            "required": True,
        },
    },
)
def execute_python_code(code: str, name: str, agent: Agent) -> str:
    """Create and execute a Python file in a Docker container and return the STDOUT of the
    executed code. If there is any data that needs to be captured use a print statement

    Args:
        code (str): The Python code to run
        name (str): A name to be given to the Python file

    Returns:
        str: The STDOUT captured from the code when it ran
    """
    ai_name = agent.ai_config.ai_name
    code_dir = agent.workspace.get_path(Path(ai_name, "executed_code"))
    os.makedirs(code_dir, exist_ok=True)

    if not name.endswith(".py"):
        name = name + ".py"

    # The `name` arg is not covered by @sanitize_path_arg,
    # so sanitization must be done here to prevent path traversal.
    file_path = agent.workspace.get_path(code_dir / name)
    if not file_path.is_relative_to(code_dir):
        return "Error: 'name' argument resulted in path traversal, operation aborted"

    try:
        with open(file_path, "w+", encoding="utf-8") as f:
            f.write(code)

        return execute_python_file(str(file_path), agent)
    except Exception as e:
        return f"Error: {str(e)}"


@command(
    "execute_python_file",
    "Executes an existing Python file",
    {
        "filename": {
            "type": "string",
            "description": "The name of te file to execute",
            "required": True,
        },
    },
)
@sanitize_path_arg("filename")
def execute_python_file(filename: str, agent: Agent) -> str:
    """Execute a Python file in a Docker container and return the output

    Args:
        filename (str): The name of the file to execute

    Returns:
        str: The output of the file
    """
    logger.info(
        f"Executing python file '{filename}' in working directory '{agent.config.workspace_path}'"
    )

    if not filename.endswith(".py"):
        return "Error: Invalid file type. Only .py files are allowed."

    file_path = Path(filename)
    if not file_path.is_file():
        # Mimic the response that you get from the command line so that it's easier to identify
        return (
            f"python: can't open file '{filename}': [Errno 2] No such file or directory"
        )

    if we_are_running_in_a_docker_container():
        logger.debug(
            f"Auto-GPT is running in a Docker container; executing {file_path} directly..."
        )
        result = subprocess.run(
            ["python", str(file_path)],
            capture_output=True,
            encoding="utf8",
            cwd=agent.config.workspace_path,
        )
        if result.returncode == 0:
            return result.stdout
        else:
            return f"Error: {result.stderr}"

    logger.debug("Auto-GPT is not running in a Docker container")
    try:
        client = docker.from_env()
        # You can replace this with the desired Python image/version
        # You can find available Python images on Docker Hub:
        # https://hub.docker.com/_/python
        image_name = "python:3-alpine"
        try:
            client.images.get(image_name)
            logger.debug(f"Image '{image_name}' found locally")
        except ImageNotFound:
            logger.info(
                f"Image '{image_name}' not found locally, pulling from Docker Hub..."
            )
            # Use the low-level API to stream the pull response
            low_level_client = docker.APIClient()
            for line in low_level_client.pull(image_name, stream=True, decode=True):
                # Print the status and progress, if available
                status = line.get("status")
                progress = line.get("progress")
                if status and progress:
                    logger.info(f"{status}: {progress}")
                elif status:
                    logger.info(status)

        logger.debug(f"Running {file_path} in a {image_name} container...")
        container: DockerContainer = client.containers.run(
            image_name,
            [
                "python",
                file_path.relative_to(agent.workspace.root).as_posix(),
            ],
            volumes={
                str(agent.config.workspace_path): {
                    "bind": "/workspace",
                    "mode": "rw",
                }
            },
            working_dir="/workspace",
            stderr=True,
            stdout=True,
            detach=True,
        )  # type: ignore

        container.wait()
        logs = container.logs().decode("utf-8")
        container.remove()

        # print(f"Execution complete. Output: {output}")
        # print(f"Logs: {logs}")

        return logs

    except DockerException as e:
        logger.warn(
            "Could not run the script in a container. If you haven't already, please install Docker https://docs.docker.com/get-docker/"
        )
        return f"Error: {str(e)}"

    except Exception as e:
        return f"Error: {str(e)}"


@command(
    "repetition_detected",
    "Warn the LLM that a six‐command repetition was detected and request a fresh next step.",
    {
        "repetition_window": {
            "type": "string",
            "description": "A single string representing the last six commands that triggered repetition.",
            "required": True,
        },
    },
)
def repetition_detected(repetition_window: str, agent: Agent) -> str:
    """
    Called whenever the agent detects that the last six commands are looping
    (e.g. A A A A A A, A B A B A B, or A B C A B C).

    repetition_window is provided as one concatenated string of those six commands.
    """
    return (
        "Repetition detected: the last six commands form a cycle with no apparent progress.\n\n"
        "Here is the concatenated string of the last 6 commands (in order):\n"
        f"{repetition_window}\n\n"
        "Please analyze everything you know about the task so far, break out of this loop, "
        "and suggest exactly one new command (with its arguments) that will move the task forward.\n\n"
        "Important:\n"
        "  • The `thoughts` field should explain why these commands were looping and how the new "
        "command breaks the pattern.\n"
    )


def validate_command(command: str, config: Config) -> bool:
    """Validate a command to ensure it is allowed

    Args:
        command (str): The command to validate
        config (Config): The config to use to validate the command

    Returns:
        bool: True if the command is allowed, False otherwise
    """
    if not command:
        return False
    return True
    command_name = command.split()[0]

    if config.shell_command_control == ALLOWLIST_CONTROL:
        return command_name in config.shell_allowlist
    else:
        return command_name not in config.shell_denylist


import time
import subprocess
import timeout_decorator

from .docker_helpers_static import (
    execute_command_in_container_screen,
    read_file_from_container,
    remove_progress_bars,
    textify_output,
)
WAIT_TIME = 300  # seconds
SCREEN_SESSION = "my_screen_session"

def _preprocess_command(command: str) -> str:
    command = command.replace(" || exit 0", "")
    if command.startswith("bash "):
        return command[len("bash "):]
    return command

def _validate_and_block_interactive(command: str, agent: Agent) -> str | None:
    if "nano " in command:
        return "Error: interactive commands like nano are not allowed."
    if command.startswith("docker "):
        return (
            "Error: docker commands are not allowed. You can create a docker image an container by simply writing a dockerfile using the 'write_to_file' tool. This would automatically trigger the building of the image, start a container and gives you access to it."
        )
    if not validate_command(command, agent.config):
        return "Error: This Shell Command is not allowed."
    if command == "ls -R":
        return "Error: ls -R is too verbose and is disallowed."
    return None

import shlex
import re

def _run_local(command: str, agent: Agent) -> str:
    # ------------------------------------------------------------
    # 1) Original blacklist checks (with the same return messages)
    # ------------------------------------------------------------
    if command.startswith("docker "):
        return (
            "Docker commands are not allowed directly. "
            "Please create a Dockerfile instead—it will handle building the image "
            "and starting the container for you."
        )
    if command.startswith("bash "):
        return (
            "Running a bash script is disallowed at this stage. "
            "Write a Dockerfile first. Once the Dockerfile is built and the container is running, "
            "you can issue commands one at a time to debug and isolate issues."
        )
    if command.startswith("sudo "):
        return "‘sudo’ is not needed. You already have the required permissions—please omit ‘sudo.’"
    if command.startswith("rm "):
        return (
            "Removing files (using ‘rm’) is not permitted right now. "
            "First, create a Dockerfile to manage file modifications inside the container."
        )
    if "SETUP_AND_INSTALL.sh" in command:
        return (
            "Executing setup/install scripts is not allowed at this point. "
            "Please create a Dockerfile first. When you build that Dockerfile, "
            "it will run any installation steps in a controlled way."
        )
    # ------------------------------------------------------------
    # 2) Disallow pipes, redirections, backgrounding, etc.
    # ------------------------------------------------------------
    if re.search(r'[|&;`$><]', command):
        return (
            "Piping, redirection, or chaining multiple commands is not allowed. "
            "Submit one simple command at a time (e.g., ‘ls’, ‘cat file.txt’, ‘grep pattern file’)."
        )

    # ------------------------------------------------------------
    # 3) Tokenize to catch malformed quotes or syntax
    # ------------------------------------------------------------
    try:
        parts = shlex.split(command)
    except ValueError:
        return "Invalid shell syntax—please check your quotes and try again."

    if not parts:
        return "No command provided. Please enter a valid command."

    cmd = parts[0]

    # ------------------------------------------------------------
    # 4) Whitelist only safe commands
    # ------------------------------------------------------------
    ALLOWED_COMMANDS = {
        "tree",
        "ls",
        "cat",
        "head",
        "tail",
        "more",
        "less",
        "grep",
        "find",
    }

    if cmd not in ALLOWED_COMMANDS:
        return (
            f"‘{cmd}’ is not permitted. "
            f"Allowed commands at this point are: {', '.join(sorted(ALLOWED_COMMANDS))}. You would have access to more commands once you have written a Dockerfile which would automatically instantiate a docker container in which you can run more commands."
        )

    # ------------------------------------------------------------
    # 5) Per-command flag checks (e.g., block ‘find -exec’)
    # ------------------------------------------------------------
    if cmd == "find":
        if "-exec" in parts or "-ok" in parts:
            return "Using ‘-exec’ or ‘-ok’ with ‘find’ is disallowed. Stick to simple file searches."

    # ------------------------------------------------------------
    # 6) All checks passed—run the command
    # ------------------------------------------------------------
    return agent.interact_with_shell(command)



def _run_in_container_deprecated(command: str, agent: Agent) -> str:
    # send the command into screen, then read back / handle stuck
    screen_cmd = f"screen -S {SCREEN_SESSION} -X stuff '{command} 2>&1 | tee /tmp/cmd_result\n'"
    execute_command_in_container_screen(agent.container, screen_cmd)

    output = read_file_from_container(agent.container, "/tmp/cmd_result")
    output = textify_output(output)

    if len(output) > 10000:
        output = remove_progress_bars(output)

    return output


import uuid
import time

# Inside your module, near the top:
SCREEN_SESSION = "my_screen_session"
LOG_DIR        = "/tmp"  # must exist inside container

def _run_in_container_deprecated_2(command: str, agent: Agent) -> str:
    """
    Send `command` into the running screen session and capture only
    that command’s output via a per‐command logfile.
    """
    # 1) Generate a unique logfile name
    run_id  = uuid.uuid4().hex
    logfile = f"{LOG_DIR}/{SCREEN_SESSION}_{run_id}.log"

    # 2) Tell screen to use that logfile, and start logging
    execute_command_in_container_screen(
        agent.container,
        f"screen -S {SCREEN_SESSION} -X logfile {logfile}"
    )
    execute_command_in_container_screen(
        agent.container,
        f"screen -S {SCREEN_SESSION} -X log on"
    )

    # 3) Send the actual command
    execute_command_in_container_screen(
        agent.container,
        f"screen -S {SCREEN_SESSION} -X stuff '{command}\\n'"
    )

    # 4) Give the process a moment to produce output
    time.sleep(0.2)

    # 5) Turn logging off so future commands start fresh
    execute_command_in_container_screen(
        agent.container,
        f"screen -S {SCREEN_SESSION} -X log off"
    )

    # 6) Read back exactly that logfile
    raw = read_file_from_container(agent.container, logfile)
    clean = textify_output(raw)

    # 7) (Optional) strip out progress bars if very large
    if len(clean) > 2000:
        clean = remove_progress_bars(clean)

    return clean

#@latest
from autogpt.commands.docker_helpers_static import exec_in_screen_and_get_log
from .docker_helpers_static import create_screen_session, ACTIVE_SCREEN

WAIT_TIME     = 1      # seconds between polls
SCREEN_SESSION= ACTIVE_SCREEN["name"]

import re

def _run_in_container(command: str, agent: Agent) -> str:
    """
    Runs a command inside the container, unless it’s disallowed:
      - ‘sudo’ is unnecessary (you already have root inside).
      - ‘SETUP_AND_INSTALL.sh’ is discouraged until after build & tests.
      - ‘docker’ commands are forbidden inside the container.
    Additionally, if the user installs a new Linux package (via apt/apt-get), 
    remind them to set it as the default and verify it.
    """
    # ------------------------------------------------------------
    # 1) Reject any use of sudo
    # ------------------------------------------------------------
    if command.startswith("sudo ") or command == "sudo":
        return "‘sudo’ is not required inside the container—you already have root access."

    # ------------------------------------------------------------
    # 2) Discourage running SETUP_AND_INSTALL.sh prematurely
    # ------------------------------------------------------------
    if "SETUP_AND_INSTALL.sh" in command:
        return (
            "Running SETUP_AND_INSTALL.sh right now is not recommended. "
            "Please execute each step manually in the terminal until the project is built "
            "and the test suite has passed, after that you can end task."
        )

    # ------------------------------------------------------------
    # 3) Forbid docker commands inside the container
    # ------------------------------------------------------------
    if command.startswith("docker ") or command == "docker":
        return "Docker commands are not allowed inside the container."

    # ------------------------------------------------------------
    # 4) Detect if this is an apt/apt-get install command
    # ------------------------------------------------------------
    install_detected = False
    # Match “apt install …” or “apt-get install …” at the very start
    if re.match(r"^(apt|apt-get)\s+install\b", command):
        install_detected = True

    # ------------------------------------------------------------
    # 5) Execute the command via screen+log and capture output
    # ------------------------------------------------------------
    exit_code, output, logfile, stuck = exec_in_screen_and_get_log(agent.container, command)
    agent.current_logfile = logfile
    agent.command_stuck   = stuck

    print("++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++")
    print(output)

    # ------------------------------------------------------------
    # 6) If a new package was installed, append a reminder
    # ------------------------------------------------------------
    if install_detected:
        reminder = (
            "\nNOTE: It looks like you just installed a new package. If it provides an executable "
            "that should be set as the default, don’t forget to update alternatives (non-interactively) "
            "and verify the change. For example:\n\n"
            "  1) If you installed OpenJDK 17 (e.g. `apt install openjdk-17-jdk`), set it as default:\n"
            "       update-alternatives --set java /usr/lib/jvm/java-17-openjdk-amd64/bin/java\n"
            "     Then confirm with:\n"
            "       java -version\n\n"
            "  2) If you installed Python 3.9 (e.g. `apt install python3.9`), switch the “python3” link:\n"
            "       update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.9 1\n"
            "       update-alternatives --set python3 /usr/bin/python3.9\n"
            "     Then verify:\n"
            "       python3 --version\n\n"
            "Replace paths or package names as needed for other tools. Ensure the new version is active before proceeding."
        )
        print(reminder)
        return output + reminder

    # ------------------------------------------------------------
    # 7) Otherwise, just return the raw output
    # ------------------------------------------------------------
    return output


def _handle_stuck(command: str, agent: Agent) -> str | None:
    """If a previous command is stuck, only allow WAIT, TERMINATE, or WRITE:<text>."""
    if not getattr(agent, "command_stuck", False):
        return None

    # WAIT: re-read the same logfile
    if command == "WAIT":
        raw = read_file_from_container(agent.container, agent.current_logfile)
        clean = textify_output(raw)
        # if our stuck‐message prefix is gone, it finished
        if not clean.startswith("The command you executed seems to take some time"):
            agent.command_stuck = False
            return f"Command finished. Output:\n{clean}"
        # still stuck
        with open("prompt_files/command_stuck") as f:
            stuck_prompt = f.read()
        return (
            f"Still waiting. Partial output:\n\n{clean}\n\n"
            "You can:\n"
            "  • WAIT to re-check\n"
            "  • TERMINATE to kill & reset\n"
            "  • WRITE:<text> to send input\n\n"
            + stuck_prompt
        )

    # TERMINATE: quit & recreate the screen session
    if command == "TERMINATE":
        # Send SIGTERM to whatever is running in window 0 of SCREEN_SESSION
        execute_command_in_container_screen(
            agent.container,
            f"screen -S {SCREEN_SESSION} -p 0 -X signal SIGTERM"
        )
        # (Optionally, wait a moment here to let it shut down cleanly…)
        time.sleep(5)
        #create_screen_session(agent.container)
        agent.command_stuck = False
        return "Previous command terminated; fresh screen session is ready."

    # WRITE: send input to the running session
    if command.startswith("WRITE:"):
        user_input = command.split("WRITE:", 1)[1]
        execute_command_in_container_screen(
            agent.container,
            f"screen -S {SCREEN_SESSION} -X stuff '{user_input}\\n'"
        )
        agent.command_stuck = False
        return "Sent input to the stuck process."

    # anything else → tell them how to control it
    return (
        "Error: a command is still running.\n"
        "Please use linux_terminal with special args: WAIT, TERMINATE, or WRITE:<text>."
        " WAIT to wait more for the process\n"
        " TERMINATE to kill the last command & reset\n"
        " WRITE:<text> to send input to the stuck command\n\n"
    )

@command(
    "linux_terminal",
    "Executes a Shell Command, non-interactive only",
    { "command": { "type": "string", "required": True } },
    enabled=True,
    disabled_reason=(
        "EXECUTE_LOCAL_COMMANDS must be 'True' in your config to run shell commands."
    ),
)
def execute_shell(command: str, agent: Agent) -> str:
    command = _preprocess_command(command)

    # Quick‐fail interactive / docker / validation
    if err := _validate_and_block_interactive(command, agent):
        return err

    # If container exists but a previous cmd is stuck, handle it
    if agent.container and (stuck_msg := _handle_stuck(command, agent)):
        return stuck_msg

    # Dispatch
    try:
        if not agent.container:
            raw = _run_local(command, agent)
            if type(raw) != str:
                raw = raw[0]
        else:
            raw = _run_in_container(command, agent)

        # Detect long‐running start‐up
        if raw.startswith("The command you executed seems to take some time"):
            agent.command_stuck = True
            return raw

        agent.command_stuck = False
        return f"Output in terminal after executing the command:\n{raw}"
    except Exception as e:
        print("-"*20 + "OUTPUT AS RETURNED BY SHELL" + "-"*20)
        print("-"*20 + "-"*20 + "-"*20)
        logger.error(f"Error running shell command: {e}")
        return f"Error: {e}"

@command(
    "execute_shell_popen",
    "Executes a Shell Command, non-interactive commands only",
    {
        "command_line": {
            "type": "string",
            "description": "The command line to execute",
            "required": True,
        }
    },
    lambda config: config.execute_local_commands,
    "You are not allowed to run local shell commands. To execute"
    " shell commands, EXECUTE_LOCAL_COMMANDS must be set to 'True' "
    "in your config. Do not attempt to bypass the restriction.",
)
def execute_shell_popen(command_line, agent: Agent) -> str:
    """Execute a shell command with Popen and returns an english description
    of the event and the process id

    Args:
        command_line (str): The command line to execute

    Returns:
        str: Description of the fact that the process started and its id
    """
    if not validate_command(command_line, agent.config):
        logger.info(f"Command '{command_line}' not allowed")
        return "Error: This Shell Command is not allowed."

    current_dir = os.getcwd()
    # Change dir into workspace if necessary
    if agent.config.workspace_path not in current_dir:
        os.chdir(agent.config.workspace_path)

    logger.info(
        f"Executing command '{command_line}' in working directory '{os.getcwd()}'"
    )

    do_not_show_output = subprocess.DEVNULL
    process = subprocess.Popen(
        command_line, shell=True, stdout=do_not_show_output, stderr=do_not_show_output
    )

    # Change back to whatever the prior working dir was

    os.chdir(current_dir)

    return f"Subprocess started with PID:'{str(process.pid)}'"


def we_are_running_in_a_docker_container() -> bool:
    """Check if we are running in a Docker container

    Returns:
        bool: True if we are running in a Docker container, False otherwise
    """
    return os.path.exists("/.dockerenv")
