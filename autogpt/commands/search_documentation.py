import os
import requests
from googlesearch import search
import openai
import json

def google_search(query, num_results=5, pause=2.0):
    """
    Perform Google search using the 'googlesearch-python' package
    and return the top `num_results` URLs.
    """
    results = []
    try:
        for i, url in enumerate(search(query,
                                      num_results=num_results,
                                      lang="en")):
            print(f"{i+1}. {url}")
            results.append(url)
            if len(results) >= num_results:
                break
    except Exception as e:
        print("Error during search:", e)
    return results

from bs4 import BeautifulSoup

def clean_html(html_content):
    """Clean HTML content using BeautifulSoup by removing unnecessary tags."""
    # Parse the HTML content with BeautifulSoup
    soup = BeautifulSoup(html_content, 'html.parser')

    # Remove script, style, and other unnecessary elements
    for tag in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'form']):
        tag.decompose()  # Completely remove the tag and its content

    # Get the text from the remaining content
    cleaned_text = soup.get_text(separator=' ', strip=True)

    # Remove excessive newlines or whitespace
    cleaned_text = ' '.join(cleaned_text.split())

    return cleaned_text

def fetch_webpage(url):
    """Fetch webpage content and clean the HTML to extract the main text."""
    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise exception if there's an error

        # Clean the HTML content to extract main text
        raw_html = response.text
        cleaned_content = clean_html(raw_html)

        return cleaned_content
    except requests.RequestException as e:
        print(f"Error fetching {url}: {e}")
        return None


import subprocess
def analyze_content_with_llm(content, prompt):
    with open("openai_token.txt") as opt:
        token = opt.read()
    try:
        # Prepare the messages data in JSON format
        messages = [
            {"role": "user", "content": prompt + "\n\nWebpage Content:\n" + content[:12000]}  # Limiting content length
        ]

        # Prepare the request data for the /chat/completions endpoint
        data = {
            "model": "gpt-4o-mini",
            "messages": messages
        }

        # Convert the data to a JSON string
        data_json = json.dumps(data)

        # Prepare the curl command
        curl_command = [
            "curl", "https://api.openai.com/v1/chat/completions",
            "-H", "Content-Type: application/json",
            "-H", "Authorization: Bearer {}".format(token),  # Replace with your API key
            "-d", data_json
        ]

        # Execute the curl command and capture the response
        result = subprocess.run(curl_command, capture_output=True, text=True)

        # Check if the request was successful
        if result.returncode == 0:
            # Parse the JSON response
            response_data = json.loads(result.stdout)
            return response_data['choices'][0]['message']['content'].strip()
        else:
            print(f"Error with curl request: {result.stderr}")
            return None

    except Exception as e:
        print(f"Error analyzing content with GPT-3.5 (via curl): {e}")
        return None

def save_search_results(project_id, search_query, results):
    """Save the search query and extracted information to a file."""
    folder_path = f'search_logs/{project_id}'
    os.makedirs(folder_path, exist_ok=True)  # Create the directory if it doesn't exist
    file_path = os.path.join(folder_path, f'{search_query.replace(" ", "_")}.json')

    # Write the data to a JSON file
    with open(file_path, 'w') as f:
        json.dump(results, f, indent=4)

def search_install_doc(project_id):
    search_query = "{} build install from source".format(project_id)
    prompt = "Extract instructions relevant to install or building the project '{}' on a Debian/Ubuntu Linux system from source code (extract a list of steps/requirements in a structered way and also the commands that needs to be installed). If the web page does not provide such information then just answer with the special string: 'NOT RELEVANT'.".format(project_id)
    # Step 1: Perform Google search
    print(f"Searching Google for: {search_query}")
    urls = google_search(search_query)
    print(urls)
    # Step 2: Retrieve and analyze each web page
    results = []
    for url in set(urls):
        print(f"Fetching content from: {url}")
        content = fetch_webpage(url)
        if content:
            print(f"Analyzing content from: {url}")
            analysis = analyze_content_with_llm(content, prompt)
            results.append({
                    'url': url,
                    'analysis': analysis
                })
    
    # Step 3: Save the search query and analysis results to a folder
    print(f"Saving results to folder: search_logs/{project_id}")
    save_search_results(project_id, search_query, results)

    return results
if __name__ == "__main__":
    # Example usage:
    project_id = "scipy"
    search_install_doc(project_id)
