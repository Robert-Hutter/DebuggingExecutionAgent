import os

def replace_placeholder(file_path, placeholder, new_value):
    """
    Replace all occurrences of a placeholder in a file with a new value.
    """
    try:
        with open(file_path, 'r') as file:
            content = file.read()

        updated_content = content.replace(placeholder, new_value)

        with open(file_path, 'w') as file:
            file.write(updated_content)

        print(f"Updated {placeholder} in {file_path}")
    except Exception as e:
        print(f"Failed to update {file_path}: {e}")
        
def get_key_and_replace(files_and_placeholders):
    replacement_value = os.getenv("OPENAI_API_KEY")
    if not replacement_value:
        print("Please provide your OpenAI API-KEY.")
        replacement_value = input("OpenAI API-KEY: ").strip()
        if not replacement_value:
            print("Error: API key cannot be empty")
            exit(1)
    for file_path, placeholder in files_and_placeholders:
        replace_placeholder(file_path, placeholder, replacement_value)
    # Save the replacement value to token.txt
    with open("openai_token.txt", "w") as token_file:
        token_file.write(replacement_value)


def main():
    files_and_placeholders = [
        ("autogpt/.env", "GLOBAL-API-KEY-PLACEHOLDER"),
        ("run.sh", "GLOBAL-API-KEY-PLACEHOLDER"),
    ]
    if os.path.exists("openai_token.txt"):
        with open("openai_token.txt") as ott:
            replacement_value = ott.read()
        if replacement_value.startswith("sk-"):
            # Replace placeholders in files
            for file_path, placeholder in files_and_placeholders:
                replace_placeholder(file_path, placeholder, replacement_value)
        else:
            get_key_and_replace(files_and_placeholders)
    else:
        get_key_and_replace(files_and_placeholders)
            

if __name__ == "__main__":
    main()