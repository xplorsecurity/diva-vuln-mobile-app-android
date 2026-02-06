import json
import os
import sys
from openai import OpenAI, RateLimitError, AuthenticationError

# -----------------------------
# Constants
# -----------------------------
SARIF_FILE = "mobsf.sarif"
SUGGESTIONS_FILE = "mobsf_fix_suggestions.md"

client = OpenAI()

# -----------------------------
# Safety check
# -----------------------------
if not os.path.exists(SARIF_FILE):
    print("[!] mobsf.sarif not found – exiting safely")
    sys.exit(0)

# -----------------------------
# Helpers
# -----------------------------
def normalize_path(file_path):
    if not file_path:
        return None

    if file_path.startswith("file://"):
        file_path = file_path.replace("file://", "")

    if file_path in [".", "./"]:
        return None

    return file_path


def get_source_snippet(file_path, start_line, end_line):
    file_path = normalize_path(file_path)

    if not file_path:
        return None

    if not os.path.exists(file_path):
        return None

    if os.path.isdir(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return "".join(lines[start_line - 1 : end_line])


def ask_llm_to_fix(issue, code):
    prompt = f"""
You are an Android security expert.

Vulnerability:
{issue}

Provide a secure remediation suggestion.
Return ONLY the corrected code snippet.

Code:
{code}
"""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content

    except (RateLimitError, AuthenticationError):
        return None


def generic_recommendation(issue):
    return f"""
This finding does not map to a specific source line.

Recommended actions:
- Review application-wide configuration and architecture.
- Follow Android secure coding best practices.
- Apply MobSF remediation guidance for the issue: {issue}
"""


def generate_recommendation(issue, file_path, start, end):
    code = get_source_snippet(file_path, start, end)

    if code:
        suggestion = ask_llm_to_fix(issue, code)
        if suggestion:
            return code, suggestion

    return "N/A (no direct source context)", generic_recommendation(issue)


def write_suggestion(file_path, start, end, issue, original, recommendation):
    with open(SUGGESTIONS_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n## 📄 {file_path or 'N/A'}:{start}-{end}\n")
        f.write(f"**Issue:** {issue}\n\n")

        f.write("### 🔴 Affected Context\n")
        f.write("```text\n")
        f.write(original.strip() + "\n")
        f.write("```\n\n")

        f.write("### ✅ Recommendation\n")
        f.write("```text\n")
        f.write(recommendation.strip() + "\n")
        f.write("```\n\n")


# -----------------------------
# Main
# -----------------------------
def main():
    with open(SARIF_FILE, "r", encoding="utf-8") as f:
        sarif = json.load(f)

    for run in sarif.get("runs", []):
        for result in run.get("results", []):
            issue = result["message"]["text"]

            location = result.get("locations", [{}])[0].get("physicalLocation", {})
            artifact = location.get("artifactLocation", {})
            region = location.get("region", {})

            file_path = artifact.get("uri")
            start = region.get("startLine", 1)
            end = region.get("endLine", start)

            print(f"[+] Processing finding: {issue}")

            original, recommendation = generate_recommendation(
                issue, file_path, start, end
            )

            write_suggestion(
                file_path,
                start,
                end,
                issue,
                original,
                recommendation
            )

    print("[+] All findings processed. Suggestions generated.")


if __name__ == "__main__":
    main()
