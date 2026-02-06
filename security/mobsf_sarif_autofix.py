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
    issue_lc = issue.lower()

    # ---------- Logging ----------
    if "log" in issue_lc:
        return """
Disable or restrict logging of sensitive data.

Specific actions:
- Remove Log.d(), Log.i(), Log.v() statements from production code.
- Ensure no credentials, tokens, PII, or session data are logged.
- Use BuildConfig.DEBUG to guard debug logs.

Example:
if (BuildConfig.DEBUG) {
    Log.d("TAG", "Debug-only log");
}
"""

    # ---------- SQL Injection ----------
    if "sql" in issue_lc:
        return """
Prevent SQL Injection vulnerabilities.

Specific actions:
- Do NOT build SQL queries using string concatenation.
- Use parameterized queries or prepared statements.
- Prefer Room ORM or SQLiteDatabase.query() APIs.

Example:
db.rawQuery(
    "SELECT * FROM users WHERE id = ?",
    new String[]{userId}
);
"""

    # ---------- Insecure Data Storage ----------
    if "storage" in issue_lc or "sharedpreferences" in issue_lc:
        return """
Secure sensitive data storage.

Specific actions:
- Do NOT store sensitive data in plaintext SharedPreferences.
- Use EncryptedSharedPreferences or Android Keystore.
- Avoid storing credentials on the device when possible.

Example:
EncryptedSharedPreferences.create(
    "secure_prefs",
    masterKey,
    context,
    EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
    EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
);
"""

    # ---------- AndroidManifest Misconfig ----------
    if "manifest" in issue_lc or "exported" in issue_lc or "backup" in issue_lc:
        return """
Harden AndroidManifest.xml configuration.

Specific actions:
- Set android:exported="false" for components not meant to be public.
- Set android:allowBackup="false" if backup is not required.
- Set android:debuggable="false" for release builds.

Example:
<application
    android:allowBackup="false"
    android:debuggable="false">
</application>
"""

    # ---------- WebView ----------
    if "webview" in issue_lc:
        return """
Secure WebView usage.

Specific actions:
- Disable JavaScript if not required.
- Avoid addJavascriptInterface unless absolutely necessary.
- Enable Safe Browsing where supported.

Example:
webView.getSettings().setJavaScriptEnabled(false);
"""

    # ---------- Fallback (still specific) ----------
    return f"""
Manual review required for this finding.

Specific actions:
- Identify the components related to this issue.
- Apply least-privilege and secure-by-default principles.
- Review MobSF documentation for this rule.

Issue reference:
{issue}
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
