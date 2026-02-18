import json
import os
import requests

# -----------------------------
# Config
# -----------------------------
SARIF_FILE = "mobsf.sarif"
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
REPO = os.getenv("GITHUB_REPOSITORY")

if not GITHUB_TOKEN or not REPO:
    raise Exception("Missing GITHUB_TOKEN or GITHUB_REPOSITORY")

API_URL = f"https://api.github.com/repos/{REPO}"

headers = {
    "Authorization": f"Bearer {GITHUB_TOKEN}",
    "Accept": "application/vnd.github+json"
}

# -----------------------------
# GitHub Helpers
# -----------------------------
def get_default_branch():
    r = requests.get(API_URL, headers=headers)
    r.raise_for_status()
    return r.json()["default_branch"]


def branch_exists(branch_name):
    r = requests.get(
        f"{API_URL}/git/ref/heads/{branch_name}",
        headers=headers
    )
    return r.status_code == 200


def create_branch_if_not_exists(branch_name, base_branch):
    if branch_exists(branch_name):
        print("Branch already exists.")
        return

    ref_data = requests.get(
        f"{API_URL}/git/ref/heads/{base_branch}",
        headers=headers
    ).json()

    sha = ref_data["object"]["sha"]

    response = requests.post(
        f"{API_URL}/git/refs",
        headers=headers,
        json={
            "ref": f"refs/heads/{branch_name}",
            "sha": sha
        }
    )

    if response.status_code != 201:
        raise Exception(f"Failed to create branch: {response.text}")

    print("Branch created.")


def get_existing_pr(branch_name):
    owner = REPO.split("/")[0]
    r = requests.get(
        f"{API_URL}/pulls?head={owner}:{branch_name}&state=open",
        headers=headers
    )
    r.raise_for_status()
    prs = r.json()

    if prs:
        return prs[0]["number"]

    return None


def create_or_get_pr(branch_name, base_branch):
    existing_pr = get_existing_pr(branch_name)
    if existing_pr:
        print("PR already exists.")
        return existing_pr

    response = requests.post(
        f"{API_URL}/pulls",
        headers=headers,
        json={
            "title": "🔐 MobSF Security Findings",
            "head": branch_name,
            "base": base_branch,
            "body": "Automated MobSF findings. Copilot will suggest fixes below."
        }
    )

    pr = response.json()

    if "number" not in pr:
        raise Exception(f"PR creation failed: {pr}")

    print("PR created.")
    return pr["number"]


def comment_on_pr(pr_number, body):
    response = requests.post(
        f"{API_URL}/issues/{pr_number}/comments",
        headers=headers,
        json={"body": body}
    )

    if response.status_code != 201:
        raise Exception(f"Failed to comment on PR: {response.text}")


# -----------------------------
# Main
# -----------------------------
def main():
    if not os.path.exists(SARIF_FILE):
        print("No SARIF file found.")
        return

    base_branch = get_default_branch()
    branch_name = "mobsf-security-fix"

    create_branch_if_not_exists(branch_name, base_branch)
    pr_number = create_or_get_pr(branch_name, base_branch)

    with open(SARIF_FILE, "r", encoding="utf-8") as f:
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

    print("MobSF PR created/updated and Copilot tagged.")


if __name__ == "__main__":
    main()
