import os
import sys
import json
import subprocess
from openai import OpenAI

with open("openai_token.txt") as tt:
    token = tt.read()
client = OpenAI(api_key = token)
if client.api_key is None:
    print("Please set OPENAI_API_KEY in your environment.")
    sys.exit(1)

MAX_RETRIES = 10
IMAGE_NAME = None
CONTEXT_DIR = None

SYSTEM_MSG = {"role": "system", "content": "You are a software engineer, well versed in setting up and running tests of different projects. You analyze attempts made by some automated tool, extract the successfull parts and reorganize them into successful scripts that build a container of the target project and run the test suite."}

# ——— Prompts ———
INITIAL_PROMPT = """
You are given an LLM agent's execution trajectory (sequence of actions the LLM taken and their results) in JSON format. Each entry has 'thoughts' and 'command'.
Your task:

1. Extract the **successful Dockerfile** that built a functioning container. If the successful Dockerfile does not call `install_and_test.sh` at the end then adjust the successful Dockerfile to call that script (and any other necessary commands such as copying the script and making it in executable mode); otherwise it is not valid.
2. Extract the **sequence of shell commands** that installs dependencies, sets up the build, and runs tests.
   - Save that sequence as the contents of a file named `install_and_test.sh`.
   - This script **must** be invoked by the Dockerfile.

**Output** **strict JSON VALIDE DICTIONARY** (no markdown, no extra keys, no missing characters):
```json
  "install_script": "<FULL contents of install_and_test.sh which should be called inside the dockerfile at the end>"
  "dockerfile": "<FULL contents of Dockerfile that also executes install_and_test.sh>",
  

```

**Note**: If the Dockerfile you generate does **not** call `install_and_test.sh`, it will be considered invalid and rejected.

All newlines must be preserved in the JSON strings.
Here is the transcript of sequence of executed commands and their output:

```
{transcript}
```

[DO NOT FORGET: **MANDATORY** to call the generated `install_and_test.sh` at the end of your Dockerfile.]
"""

UPDATE_PROMPT_TEMPLATE = """
The last attempt to build & test using your Dockerfile and install_and_test.sh has **failed**.
Here are the build/run logs:

```
{error_log}
```

Please update **both** files so that the build+test **succeeds**, following the same format (JSON with keys `dockerfile` and `install_script`).
"""

def call_llm(messages):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.0,
    )
    return resp.choices[0].message.content

def write_files(spec: dict):
    df_path = os.path.join(CONTEXT_DIR, "Dockerfile")
    sh_path = os.path.join(CONTEXT_DIR, "install_and_test.sh")
    with open(df_path, "w") as df:
        df.write(spec["dockerfile"])
    with open(sh_path, "w") as sh:
        sh.write(spec["install_script"])
    os.chmod(sh_path, 0o755)

def build_and_run() -> (bool, str):
    b = subprocess.run(
        ["docker", "build", "-t", IMAGE_NAME, CONTEXT_DIR],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    if b.returncode != 0:
        return False, b.stdout
    r = subprocess.run(
        ["docker", "run", "--rm", IMAGE_NAME],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True
    )
    return (r.returncode == 0, r.stdout)

def main():
    if len(sys.argv) != 3:
        print("Usage: auto_build.py path/to/transcript.json image_name")
        sys.exit(1)

    transcript_path = sys.argv[1]
    image_name = sys.argv[2]

    global IMAGE_NAME, CONTEXT_DIR
    IMAGE_NAME = image_name
    CONTEXT_DIR = image_name

    os.makedirs(CONTEXT_DIR, exist_ok=True)
    transcript = open(transcript_path).read()

    messages = [SYSTEM_MSG]
    messages.append({"role": "user", "content": INITIAL_PROMPT.format(transcript=transcript)})

    for attempt in range(1, MAX_RETRIES + 1):
        print(f"\n=== Attempt {attempt} ===")
        raw = call_llm(messages)
        messages.append({"role": "assistant", "content": raw})

        try:
            spec = raw.replace("```json", "").replace("```", "")
            spec = json.loads(spec)
            
        except Exception as e:
            print("❌ LLM output was not valid JSON:\n", spec, e)
            sys.exit(1)

        write_files(spec)
        ok, log = build_and_run()
        if ok:
            print("✅ Build & tests passed!\n")
            print(log)
            return

        print("❌ Build/Test failed, logs follow…")
        print(log)
        if len(log) > 20000:
            log = log[:10000] + "...(output shortened)..." + log[-10000:]
        feedback = UPDATE_PROMPT_TEMPLATE.format(error_log=log, transcript=transcript)
        messages.append({"role": "user", "content": feedback})

    print(f"\nAll {MAX_RETRIES} attempts failed.")
    sys.exit(1)

if __name__ == "__main__":
    main()
