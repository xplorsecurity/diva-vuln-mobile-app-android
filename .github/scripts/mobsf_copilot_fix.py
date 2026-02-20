import json
import os
import subprocess
import requests
import time

GITHUB_TOKEN = os.getenv("GH_TOKEN")
AI_URL = "https://models.inference.ai.azure.com/chat/completions"

def get_default_branch():
    """Detects if the default branch is main or master."""
    try:
        return subprocess.check_output(["git", "symbolic-ref", "refs/remotes/origin/HEAD"], text=True).strip().split('/')[-1]
    except:
        # Fallback to checking local branches
        branches = subprocess.check_output(["git", "branch", "-a"], text=True)
        if 'remotes/origin/main' in branches: return 'main'
        return 'master'

def ask_ai(finding_desc, file_content):
    headers = {"Authorization": f"Bearer {GITHUB_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a mobile security expert. Return ONLY the entire corrected source code. No markdown, no explanations."},
            {"role": "user", "content": f"Fix this MobSF finding: {finding_desc}\n\nCODE:\n{file_content}"}
        ],
        "temperature": 0.1
    }
    response = requests.post(AI_URL, headers=headers, json=payload)
    response.raise_for_status()
    return response.json()['choices'][0]['message']['content'].strip()

def process_issue(issue, base_branch):
    file_path = issue['file_path']
    desc = issue['description']
    
    print(f"--- Processing: {file_path} ---")
    
    unique_id = os.urandom(2).hex()
    branch_name = f"ai-review/{unique_id}"
    
    # Reset to base branch and create new branch
    subprocess.run(["git", "checkout", base_branch])
    subprocess.run(["git", "checkout", "-b", branch_name])
    
    # CRITICAL: Create an empty commit so GitHub allows the PR creation
    subprocess.run(["git", "commit", "--allow-empty", "-m", f"AI Security Review for {file_path}"])
    subprocess.run(["git", "push", "origin", branch_name])
    
    with open(file_path, 'r') as f:
        original_code = f.read()
    
    try:
        fixed_code = ask_ai(desc, original_code)
        
        # Create Draft PR
        pr_title = f"🛡️ [Review Required] Fix in {os.path.basename(file_path)}"
        pr_body = f"### 🔍 AI Security Suggestion\n**Issue:** {desc}\n\nReview the suggested code change below. Click 'Commit suggestion' to apply it."
        
        pr_url = subprocess.check_output([
            "gh", "pr", "create",
            "--title", pr_title,
            "--body", pr_body,
            "--head", branch_name,
            "--base", base_branch,
            "--draft"
        ], text=True).strip()
        
        # Post the Suggested Change
        comment_body = f"🤖 **AI Proposed Fix:**\n\n```suggestion\n{fixed_code}\n```"
        subprocess.run(["gh", "pr", "comment", pr_url, "--body", comment_body])
        
        print(f"✅ Created Review PR: {pr_url}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    base = get_default_branch()
    print(f"Targeting base branch: {base}")

    if not os.path.exists('mobsf_results.json'):
        print("No MobSF results found.")
        exit(0)

    with open('mobsf_results.json') as f:
        data = json.load(f)
        results = data.get('results', {})

    findings = []
    for rule_id, details in results.items():
        for f_info in details.get('files', []):
            findings.append({'description': details.get('metadata', {}).get('description'), 'file_path': f_info.get('file_path')})

    # Limit to 2 for testing to avoid spamming the repo
    for issue in findings[:2]:
        process_issue(issue, base)
        time.sleep(2)
