"""
Create a Linear issue for a dependabot PR.

Environment variables (all set by the composite action step):
  LINEAR_API_KEY          Linear personal API key
  IS_SECURITY             'true' if the PR is security-related
  SEVERITY                Critical | High | Moderate | Low | none
  SLA                     Human-readable SLA string
  LINEAR_TEAM_ID          Linear team UUID
  LINEAR_PROJECT_ID       Linear project UUID
  LINEAR_INREVIEW_STATE   Linear "In Review" state UUID (used for security PRs)
  LINEAR_TODO_STATE       Linear "Todo" state UUID (used for routine PRs)
  LINEAR_ASSIGNEE_ID      Linear assignee UUID
  PR_TITLE_FILE           Path to file containing the PR title
  PR_URL_FILE             Path to file containing the PR URL
"""

import json
import os
import urllib.error
import urllib.request

is_security = os.environ.get("IS_SECURITY") == "true"
severity    = os.environ.get("SEVERITY", "none")
sla         = os.environ.get("SLA", "")

pr_title_file = os.environ.get("PR_TITLE_FILE", "/tmp/pr_title.txt")
pr_url_file   = os.environ.get("PR_URL_FILE",   "/tmp/pr_url.txt")

with open(pr_title_file) as f:
    pr_title = f.read().strip()
with open(pr_url_file) as f:
    pr_url = f.read().strip()

if is_security:
    description = (
        f"## Dependabot PR\n\n{pr_url}\n\n"
        f"## Severity\n\n{severity}\n\n"
        f"## SLA\n\n{sla}\n"
    )
else:
    description = (
        f"## Dependabot PR\n\n{pr_url}\n\n"
        f"## Type\n\nRoutine dependency update\n"
    )

variables = {
    "input": {
        "teamId":      os.environ["LINEAR_TEAM_ID"],
        "title":       f"Review dependency update: {pr_title}",
        "description": description,
        "stateId":     (os.environ["LINEAR_INREVIEW_STATE"] if is_security
                        else os.environ["LINEAR_TODO_STATE"]),
        "priority":    1 if is_security else 3,  # 1 Urgent / 3 Medium
        "projectId":   os.environ["LINEAR_PROJECT_ID"],
        "assigneeId":  os.environ["LINEAR_ASSIGNEE_ID"],
    }
}

payload = json.dumps({
    "query": (
        "mutation IssueCreate($input: IssueCreateInput!) "
        "{ issueCreate(input: $input) { success issue { identifier url } } }"
    ),
    "variables": variables,
}).encode()

req = urllib.request.Request(
    "https://api.linear.app/graphql",
    data=payload,
    headers={
        "Authorization": os.environ["LINEAR_API_KEY"],
        "Content-Type":  "application/json",
    },
)
try:
    with urllib.request.urlopen(req, timeout=15) as resp:
        result = json.loads(resp.read())
        issue = result.get("data", {}).get("issueCreate", {}).get("issue", {})
        if issue:
            print(f"Linear issue created: {issue['identifier']} {issue['url']}")
        else:
            print(f"::warning::Unexpected Linear response: {result}")
except urllib.error.HTTPError as exc:
    body = exc.read().decode("utf-8", errors="replace")
    print(f"::warning::Linear HTTP {exc.code}: {body}")
except urllib.error.URLError as exc:
    print(f"::warning::Linear network error: {exc.reason}")
except Exception as exc:
    print(f"::warning::Linear error: {exc}")
