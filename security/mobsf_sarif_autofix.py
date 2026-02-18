import json
import os
import base64
import requests

# -----------------------------
# Config
# -----------------------------
SARIF_FILE = "mobsf.sarif"
REPORT_FILE = "security/mobsf_findings_report.md"

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


def create_branch(branch_name, base_branch):
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


def create_or_update_file(branch, content):
    encoded = base64.b64encode(content.encode()).decode()

    # Check if file exists
    r = requests.get(
        f"{API_URL}/contents/{REPORT_FILE}?ref={branch}",
        headers=headers
    )

    sha = None
    if r.status_code == 200:
        sha = r.json()["sha"]

    data = {
        "message": "Update MobSF security findings report",
        "content": encoded,
        "branch": branch
    }

    if sha:
        data["sha"] = sha

    response = requests.put(
        f"{API_URL}/contents/{REPORT_FILE}",
        headers=headers,
        json=data
    )

    if response.status_code not in [200, 201]:
        raise Exception(f"Failed to commit file: {response.text}")

    print("Security report committed.")


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


def create_pr(branch_name, base_branch):
    response = requests.post(
        f"{API_URL}/pulls",
        headers=headers,
        json={
            "title": "🔐 MobSF Security Findings",
            "head": branch_name,
            "base": base_branch,
            "body": "Automated MobSF findings report. Copilot suggestions below."
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

    if not branch_exists(branch_name):
        create_branch(branch_name, base_branch)
    else:
        print("Branch already exists.")

    # Build report content
    report_content = "# MobSF Security Findings\n\n"

    with open(SARIF_FILE, "r", encoding="utf-8") as f:
        sarif = json.load(f)

    findings = []

    for run in sarif.get("runs", []):
        for result in run.get("results", []):
            issue = result["message"]["text"]

            location = result.get("locations", [{}])[0].get("physicalLocation", {})
            artifact = location.get("artifactLocation", {})
            region = location.get("region", {})

            file_path = artifact.get("uri", "N/A")
            start = region.get("startLine", "N/A")

            findings.append((issue, file_path, start))

            report_content += f"## {issue}\n"
            report_content += f"- File: {file_path}:{start}\n\n"

    if not findings:
        print("No findings found.")
        return

    # Commit report file (this creates actual diff)
    create_or_update_file(branch_name, report_content)

    # Create or reuse PR
    pr_number = get_existing_pr(branch_name)
    if not pr_number:
        pr_number = create_pr(branch_name, base_branch)
    else:
        print("PR already exists.")

    # Tag Copilot once
    comment_body = "@github-copilot please review this MobSF security report and suggest secure Android remediations for each finding."

    comment_on_pr(pr_number, comment_body)

    print("MobSF PR ready and Copilot tagged.")


if __name__ == "__main__":
    main()
