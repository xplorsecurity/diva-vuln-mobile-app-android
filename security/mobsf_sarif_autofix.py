import json
import os
import subprocess
from openai import OpenAI

SARIF_FILE = "mobsf.sarif"

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def load_sarif():
    with open(SARIF_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def get_source_snippet(file_path, start_line, end_line):
    with open(file_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
        return "".join(lines[start_line-1:end_line])

def ask_llm_to_fix(issue, code):
    prompt = f"""
You are a secure Android developer.

Vulnerability:
{issue}

Fix the following code securely.
Return ONLY the fixed code, no explanation.

Code:
{code}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    return response.choices[0].message.content

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
            fixed = ask_llm_to_fix(message, code)
            apply_fix(file_path, start, end, fixed)

    git_commit()

if __name__ == "__main__":
    main()
