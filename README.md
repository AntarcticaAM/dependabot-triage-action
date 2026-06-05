# dependabot-triage-action

Composite GitHub Action that automates dependabot PR triage across AntarcticaAM repositories.

When dependabot opens a PR, this action:

1. Detects security advisories (GHSA IDs and severity headers) in the PR body
2. Adds `security 🔒`, `urgent ⏰`, and `cve 🛡️` labels on security PRs
3. Assigns reviewers (security PRs get a second reviewer)
4. Posts a `@codex review` comment requesting an AI-assisted code review
5. Posts a security alert comment with SLA and advisory IDs on security PRs
6. Adds the PR to an org-level GitHub project for tracking
7. Creates a Linear issue in the Security Vulnerability Remediation project
8. Writes an idempotency marker so re-opened PRs are not re-triaged

## Usage

```yaml
# .github/workflows/dependabot-triage.yml
name: Dependabot PR triage

on:
  pull_request_target:
    branches: [main]   # or [master]
    types: [opened]
  workflow_dispatch:
    inputs:
      pr_number:
        description: PR number to (re-)triage
        required: true
      dry_run:
        description: Log what would happen without mutating anything
        required: false
        default: 'true'
      force:
        description: Bypass the already-triaged idempotency check
        required: false
        default: 'false'

concurrency:
  group: dependabot-triage-${{ github.event.pull_request.number || inputs.pr_number }}
  cancel-in-progress: false

jobs:
  triage:
    if: github.event_name == 'workflow_dispatch' || github.actor == 'dependabot[bot]'
    runs-on: ubuntu-latest
    timeout-minutes: 10
    permissions:
      pull-requests: write
      issues: write
    steps:
      - uses: AntarcticaAM/dependabot-triage-action@v1
        with:
          github-token:           ${{ secrets.GITHUB_TOKEN }}
          gh-project-token:       ${{ secrets.GH_PROJECT_TOKEN }}
          linear-api-key:         ${{ secrets.COPILOT_MCP_LINEAR_API_KEY }}
          pr-number:              ${{ github.event.pull_request.number || inputs.pr_number }}
          dry-run:                ${{ (github.event_name == 'workflow_dispatch' && inputs.dry_run) || 'false' }}
          force:                  ${{ (github.event_name == 'workflow_dispatch' && inputs.force) || 'false' }}
          github-project-number:  '51'
```

## Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `github-token` | yes | — | `GITHUB_TOKEN` for PR comments, labels, and reviewer assignment |
| `gh-project-token` | no | `''` | PAT with `project` scope for org-level GitHub Projects writes |
| `linear-api-key` | no | `''` | Linear personal API key; step skipped if absent |
| `pr-number` | yes | — | PR number to triage |
| `dry-run` | no | `false` | Log what would happen without mutating anything |
| `force` | no | `false` | Bypass the idempotency marker check |
| `github-project-number` | no | `''` | Org-level GitHub project number; step skipped if empty |
| `primary-reviewer` | no | `LiamDeaconAntarcticaAM` | Reviewer assigned to every dependabot PR |
| `security-reviewer` | no | `edwardconnect` | Second reviewer added on security PRs only |
| `security-alert-mention` | no | `LiamDeaconAntarcticaAM` | Username @-mentioned in security alert comments |
| `linear-team-id` | no | ANT team UUID | Linear team for issue creation |
| `linear-project-id` | no | Security Vulnerability Remediation UUID | Linear project for issues |
| `linear-inreview-state-id` | no | In Review UUID | Applied to security PRs |
| `linear-todo-state-id` | no | Todo UUID | Applied to routine PRs |
| `linear-assignee-id` | no | Liam UUID | Assignee for created Linear issues |

## Smoke testing

Use `workflow_dispatch` with `dry_run=true` to validate detection logic without
mutating any labels, comments, projects, or Linear:

```bash
gh workflow run dependabot-triage.yml \
  --repo AntarcticaAM/ice-age-mono \
  --field pr_number=2271 \
  --field dry_run=true
```

## Security

This action is designed for `pull_request_target` workflows. It does **not**
check out PR code and treats all PR-controlled data (title, body) as untrusted
data. See the inline comments in `action.yml` for the full security rationale.

## Consumers

- [ice-age-mono](https://github.com/AntarcticaAM/ice-age-mono) — `.github/workflows/dependabot-triage.yml`
- [python-mono](https://github.com/AntarcticaAM/python-mono) — `.github/workflows/dependabot-triage.yml`
- [aam-data-platform](https://github.com/AntarcticaAM/aam-data-platform) — `.github/workflows/dependabot-triage.yml`
