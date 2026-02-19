name: "MobSF Scan & Copilot Fix"

on:
  workflow_dispatch: # This enables the manual button in GitHub UI

jobs:
  scan-and-fix:
    runs-on: ubuntu-latest
    permissions:
      contents: write
      pull-requests: write

    steps:
      - name: Checkout Code
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: Setup Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Configure Git
        run: |
          git config user.name "github-actions[bot]"
          git config user.email "github-actions[bot]@users.noreply.github.com"

      - name: Run MobSF Scan
        run: |
          pip install mobsfscan
          # Generating the findings file
          mobsfscan . --json --output mobsf_results.json || true

      - name: Run Copilot Agent
        env:
          # You must add this secret to your Repo Settings
          GH_TOKEN: ${{ secrets.GH_COPILOT_TOKEN }} 
        run: python .github/scripts/mobsf_copilot_fix.py
