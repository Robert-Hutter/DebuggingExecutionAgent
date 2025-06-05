import os
import openai
from autogpt.commands.docker_helpers_static import ask_llm

def condense_history(old_history: str) -> str:
    example_old = """
    Call to tool linux_terminal with arguments {'command': 'ls'}
    The summary of the output of above command: {'summary': 'The project is scikit-learn, a machine learning library for Python. The main files include a README, a Dockerfile, and a pyproject.toml, which likely contains dependency information.', 'extracted dependencies': ['numpy', 'scipy', 'cython', 'meson', 'ninja', 'joblib', 'threadpoolctl', 'setuptools'], 'important commands': ['git clone https://github.com/scikit-learn/scikit-learn.git', 'python3 -m venv venv', '. venv/bin/activate', 'pip install numpy scipy cython meson ninja joblib threadpoolctl setuptools'], 'important files/links/hyperlinks': ['https://github.com/scikit-learn/scikit-learn', 'README.rst', 'Dockerfile', 'pyproject.toml']}
    Call to tool read_file with arguments {'file_path': 'README.rst'}
    The summary of the output of above command: {'summary': 'scikit-learn is a Python module for machine learning built on top of SciPy and is distributed under the 3-Clause BSD license. It requires specific versions of Python and several libraries to function correctly. The project is maintained by a team of volunteers and welcomes contributions.', 'extracted dependencies': ['Python (>= 3.10)', 'NumPy (>= 1.22.0)', 'SciPy (>= 1.8.0)', 'joblib (>= 1.2.0)', 'threadpoolctl (>= 3.1.0)', 'Matplotlib (>= 3.5.0)', 'scikit-image (>= 0.19.0)', 'pandas (>= 1.4.0)', 'seaborn (>= 0.9.0)', 'pytest (>= 7.1.2)', 'plotly (>= 5.14.0)'], 'important commands': ['pip install -U scikit-learn', 'git clone https://github.com/scikit-learn/scikit-learn.git', 'pytest sklearn'], 'important files/links/hyperlinks': ['https://github.com/scikit-learn/scikit-learn', 'https://pypi.org/project/scikit-learn/', 'https://scikit-learn.org/stable/install.html', 'https://scikit-learn.org/dev/developers/contributing.html', 'https://scikit-learn.org/dev/developers/index.html']}
    Call to tool write_to_file with arguments {'filename': 'Dockerfile', 'text': 'FROM python:3.10-slim\n\n# Avoid interruptive messages from tzdata\nENV TZ=Europe/Berlin\nRUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone\n\n# Install git, gcc, and other necessary build tools\nRUN apt-get update && \\\n    apt-get install -y git gcc build-essential python3-dev ninja-build meson && \\\n    apt-get clean && \\\n    rm -rf /var/lib/apt/lists/* || exit 0\n\nWORKDIR /app\n\n# Clone the repository\nRUN git clone https://github.com/scikit-learn/scikit-learn.git || exit 0\n\nWORKDIR /app/scikit-learn\n\nCMD ["bash"]'}
    The summary of the output of above command: {'summary': 'The Docker image for the scikit-learn project was built successfully, and the container has been launched with the current working directory set to /app/scikit-learn.', 'extracted dependencies': ['Python (>= 3.10)', 'NumPy (>= 1.22.0)', 'SciPy (>= 1.8.0)', 'joblib (>= 1.2.0)', 'threadpoolctl (>= 3.1.0)', 'Matplotlib (>= 3.5.0)', 'scikit-image (>= 0.19.0)', 'pandas (>= 1.4.0)', 'seaborn (>= 0.9.0)', 'pytest (>= 7.1.2)', 'plotly (>= 5.14.0)'], 'important commands': ['git clone https://github.com/scikit-learn/scikit-learn.git', 'python3 -m venv venv', '. venv/bin/activate', 'pip install numpy scipy cython meson ninja joblib threadpoolctl setuptools'], 'important files/links/hyperlinks': ['https://github.com/scikit-learn/scikit-learn', 'README.rst', 'Dockerfile', 'pyproject.toml']}
    Call to tool linux_terminal with arguments {'command': 'pip install numpy scipy cython meson ninja joblib threadpoolctl setuptools matplotlib scikit-image pandas seaborn pytest plotly'}
    The summary of the output of above command: {'summary': 'The installation of required Python packages for the scikit-learn project was successful, with all dependencies being downloaded and installed without errors.', 'extracted dependencies': ['numpy', 'scipy', 'cython', 'meson', 'ninja', 'joblib', 'threadpoolctl', 'setuptools', 'matplotlib', 'scikit-image', 'pandas', 'seaborn', 'pytest', 'plotly', 'pillow', 'python-dateutil', 'cycler', 'contourpy', 'pyparsing', 'packaging', 'kiwisolver', 'fonttools', 'tifffile', 'lazy-loader', 'networkx', 'imageio', 'pytz', 'tzdata', 'pygments', 'iniconfig', 'pluggy', 'tomli', 'exceptiongroup', 'narwhals', 'typing-extensions', 'six'], 'important commands': ['pip install numpy scipy cython meson ninja joblib threadpoolctl setuptools matplotlib scikit-image pandas seaborn pytest plotly'], 'important files/links/hyperlinks': []}
    Call to tool linux_terminal with arguments {'command': 'pytest'}
    The summary of the output of above command: {'summary': "The test execution with pytest failed due to an ImportError indicating that the scikit-learn package has not been built correctly. The error message suggests that the module 'sklearn.__check_build._check_build' is missing, which is essential for the package to function properly. The output also provides a link to the scikit-learn advanced installation guide for building from source.", 'extracted dependencies': [], 'important commands': [], 'important files/links/hyperlinks': ['https://scikit-learn.org/dev/developers/advanced_installation.html#building-from-source']}
    """

    example_new = """
- `ls` → Project contains `README.rst`, `Dockerfile`, `pyproject.toml`.
- `read_file("README.rst")` → Identified key dependencies (Python ≥3.10, NumPy, SciPy, Cython, Meson, Ninja, joblib, threadpoolctl, pytest, etc.).
- `write_to_file("Dockerfile", <initial template>)` → Dockerfile built successfully.
- `pip install ...` → All required Python packages installed.
- `meson setup build && ninja -C build install` → Build and install succeeded repeatedly.
- `pytest` → Test run still failing due to missing `_check_build`, indicating build artifacts not recognized.
"""

    system_prompt = (
        "You are a helpful assistant that transforms a detailed command history "
        "into a concise, bullet-point summary. "
        "Given an example in which the “old” verbose format is converted to a “new” condensed format, "
        "apply the same transformation to the user’s provided history."
    )

    user_prompt = f"""
Here is an example transformation:

OLD FORMAT:
{example_old}

NEW CONDENSED FORMAT:
{example_new}

Now, condense the following command history:

OLD FORMAT:
{old_history}

NEW CONDENSED FORMAT[ONLY OUTPUT THE CONDENSED FORMAT, NO EXPLANATION AROUND]:
"""
    result = ask_llm(system_prompt, user_prompt)
    return result