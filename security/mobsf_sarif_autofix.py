import json
import os
import subprocess
from openai import OpenAI, RateLimitError, AuthenticationError

SARIF_FILE = "mobsf.sarif"
SUGGESTIONS_FILE = "mobsf_fix_suggestions.md"
# -----------------------------
# STEP 4: Safety check
# -----------------------------
if not os.path.exists(SARIF_FILE):
    print("[!] mobsf.sarif not found – skipping LLM autofix")
    sys.exit(0)

client = OpenAI(api_key=os.getenv("FINDINGS_COPILOT"))

def load_sarif():
    with open(SARIF_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def normalize_path(file_path):
    if not file_path:
        return None

    # Handle file:// URIs
    if file_path.startswith("file://"):
        file_path = file_path.replace("file://", "")

    # Skip current directory or empty paths
    if file_path in [".", "./"]:
        return None

    return file_path

def get_source_snippet(file_path, start_line, end_line):
    file_path = normalize_path(file_path)

    if not file_path:
        print("[!] Invalid or empty file path, skipping")
        return None

    if not os.path.exists(file_path):
        print(f"[!] File not found on disk, skipping: {file_path}")
        return None

    if os.path.isdir(file_path):
        print(f"[!] Path is a directory, skipping: {file_path}")
        return None

    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    return "".join(lines[start_line - 1 : end_line])

def ask_llm_to_fix(issue, code):
    prompt = f"""
You are a secure Android developer.

Vulnerability:
{issue}

Fix the following code securely.
Return ONLY the fixed code.

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

    except RateLimitError:
        print("[!] OpenAI quota exceeded – skipping this finding")
        return None

    except AuthenticationError:
        print("[!] OpenAI authentication failed – skipping this finding")
        return None
        
def write_suggestion(file_path, start, end, issue, original, suggestion):
    with open(SUGGESTIONS_FILE, "a", encoding="utf-8") as f:
        f.write(f"\n## 📄 {file_path}:{start}-{end}\n")
        f.write(f"**Issue:** {issue}\n\n")

        f.write("### 🔴 Vulnerable Code\n")
        f.write("```java\n")
        f.write(original.strip() + "\n")
        f.write("```\n\n")

        f.write("### ✅ Suggested Fix\n")
        f.write("```java\n")
        f.write(suggestion.strip() + "\n")
        f.write("```\n\n")

def apply_fix(file_path, start_line, end_line, fixed_code):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    lines[start_line-1:end_line] = fixed_code.splitlines(keepends=True)

    with open(file_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

def git_commit():
    subprocess.run(["git", "config", "user.name", "mobsf-llm-bot"])
    subprocess.run(["git", "config", "user.email", "mobsf@autofix.bot"])
    subprocess.run(["git", "add", "."])
    subprocess.run(["git", "commit", "-m", "fix: MobSF security issue (LLM autofix)"], check=False)
    subprocess.run(["git", "push"], check=False)

def main():
    sarif = load_sarif()

    for run in sarif.get("runs", []):
        for result in run.get("results", []):
            message = result["message"]["text"]
            location = result["locations"][0]["physicalLocation"]
            file_path = location["artifactLocation"]["uri"]
            region = location["region"]

            start = region.get("startLine", 1)
            end = region.get("endLine", start + 5)

            print(f"[+] Fixing {file_path}:{start}-{end}")

            code = get_source_snippet(file_path, start, end)
            if not code:
                print("[!] No source code available, skipping this finding")
                continue
            
            fixed = ask_llm_to_fix(message, code)
            if not fixed:
                print("[!] No suggestion generated, continuing")
            write_suggestion(file_path, start, end, message, code, fixed)
            print("[+] Fix suggestion recorded")
            
    git_commit()

if __name__ == "__main__":
    main()
