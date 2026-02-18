import json
import os
import requests

SARIF_FILE = "mobsf.sarif"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")
API_URL = f"https://api.github.com/repos/{REPO}"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

def get_default_branch():
    repo = requests.get(API_URL, headers=headers).json()
    return repo["default_branch"]

def create_branch(branch_name, base_branch):
    ref_data = requests.get(
        f"{API_URL}/git/ref/heads/{base_branch}",
        headers=headers
    ).json()

    sha = ref_data["object"]["sha"]

    requests.post(
        f"{API_URL}/git/refs",
        headers=headers,
        json={
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
    )

def create_pull_request(branch_name):
    pr = requests.post(
        f"{API_URL}/pulls",
        headers=headers,
        json={
            "title": "🔐 MobSF Security Findings",
            "head": branch_name,
            "base": get_default_branch(),
            "body": "Automated MobSF findings. Copilot will suggest fixes below."
        }
    ).json()

    return pr["number"]

def comment_on_pr(pr_number, body):
    requests.post(
        f"{API_URL}/issues/{pr_number}/comments",
        headers=headers,
        json={"body": body}
    )

def main():
    if not os.path.exists(SARIF_FILE):
        print("No SARIF file found.")
        return

    branch_name = "mobsf-security-fix"
    base_branch = get_default_branch()

    create_branch(branch_name, base_branch)
    pr_number = create_pull_request(branch_name)

    with open(SARIF_FILE, "r") as f:
        sarif = json.load(f)

    for run in sarif.get("runs", []):
        for result in run.get("results", []):
            issue = result["message"]["text"]

            location = result.get("locations", [{}])[0].get("physicalLocation", {})
            artifact = location.get("artifactLocation", {})
            region = location.get("region", {})

            file_path = artifact.get("uri", "N/A")
            start = region.get("startLine", "N/A")

            comment = f"""
@github-copilot please suggest a secure remediation.

**Issue:**
{issue}

**File:**
{file_path}:{start}

Provide a secure Android fix.
"""
            comment_on_pr(pr_number, comment)

    print("MobSF PR created and Copilot tagged.")

if __name__ == "__main__":
    main()
