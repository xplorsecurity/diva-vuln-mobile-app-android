import json
import os
import subprocess
import requests

# Config
GITHUB_TOKEN = os.getenv("GH_TOKEN")
COPILOT_API_URL = "https://api.github.com/copilot/chat/completions"

def ask_copilot(finding_desc, file_content):
    """Uses the GitHub Models API (2026 official path for AI automation)."""
    
    # This is the correct endpoint for programmatic AI completions in 2026
    url = "https://models.inference.ai.azure.com/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": "gpt-4o", 
        "messages": [
            {
                "role": "system", 
                "content": "You are a mobile security expert. Return ONLY the fixed source code."
            },
            {
                "role": "user", 
                "content": f"Fix this MobSF finding: {finding_desc}\n\nCode:\n{file_content}"
            }
        ],
        "temperature": 0.1
    }

    print(f"Calling GitHub Models API for remediation...")
    response = requests.post(url, headers=headers, json=payload)
    
    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content'].strip()
    elif response.status_code == 403:
        raise Exception("403 Forbidden: Ensure your GitHub Token has 'GitHub Models' access enabled in settings.")
    else:
        raise Exception(f"API Error {response.status_code}: {response.text}")
        
def run_agent():
    if not os.path.exists('mobsf_results.json'):
        print("❌ Error: mobsf_results.json missing.")
        return

    with open('mobsf_results.json', 'r') as f:
        data = json.load(f)
    
    # MobSF 2025/2026 format uses 'results' as the main key
    results = data.get('results', {})
    
    # Flatten the results (MobSF organizes by Rule ID)
    findings = []
    for rule_id, details in results.items():
        files = details.get('files', [])
        for f_info in files:
            findings.append({
                'rule_id': rule_id,
                'description': details.get('metadata', {}).get('description'),
                'file_path': f_info.get('file_path'),
                'severity': details.get('metadata', {}).get('severity')
            })

    print(f"✅ Found {len(findings)} issues in MobSF results.")

    if not findings:
        print("💡 Tip: Check if your source code is in a subfolder like /app or /src.")
        return

    # For the PoC, let's just fix the first High/Warning issue
    issue = findings[0]
    file_path = issue['file_path']
    description = issue['description']
    
    print(f"🛠️ AI Agent starting fix for: {description} in {file_path}")

    # Git Operations
    branch_name = f"fix/mobsf-{os.urandom(2).hex()}"
    subprocess.run(["git", "checkout", "-b", branch_name])

    with open(file_path, 'r') as f:
        original_code = f.read()

    # Get Fix
    try:
        new_code = ask_copilot(description, original_code)
        with open(file_path, 'w') as f:
            f.write(new_code)
            
        # Push & PR
        subprocess.run(["git", "add", file_path])
        subprocess.run(["git", "commit", "-m", f"security: fix {description}"])
        subprocess.run(["git", "push", "origin", branch_name])
        
        pr_body = f"### 🛡️ Automated Security Fix\n**Vulnerability:** {description}\n**File:** `{file_path}`"
        subprocess.run(["gh", "pr", "create", "--title", f"Fix: {description[:40]}", "--body", pr_body, "--head", branch_name])
        print(f"🚀 Success! PR created for {file_path}")
        
    except Exception as e:
        print(f"❌ Failed to generate fix: {e}")

if __name__ == "__main__":
    run_agent()
