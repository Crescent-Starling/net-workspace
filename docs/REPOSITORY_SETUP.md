# Repository Setup

## Local Repository

This project should live in its own Git repository and should not share the old mixed workspace history.

Recommended repository name:

`net-workspace`

## GitHub Creation Options

### Option A: Create via GitHub web UI

1. Open GitHub.
2. Click `New repository`.
3. Repository name: `net-workspace`
4. Description: `AI-native recruitment intelligence workspace with crawler, templates, agents, and personal workspaces.`
5. Choose `Private` first unless you want it public.
6. Do not initialize with README, `.gitignore`, or license because local files already exist.
7. Create repository.

### Option B: Create via GitHub CLI

If `gh` is installed and authenticated:

```bash
gh repo create net-workspace --private --source=. --remote=origin --push
```

## After GitHub Repository Is Created

Run from the project root:

```bash
git remote add origin https://github.com/Crescent-Starling/net-workspace.git
git branch -M main
git add .
git commit -m "chore: initialize clean project skeleton"
git push -u origin main
```

## Suggested Branch Strategy

- `main`: stable release branch
- `develop`: integration branch
- `feature/*`: regular features
- `docs/*`: documentation work
- `agent/*`: experimental AI or workflow branches

## Commit Style

Use Conventional Commits:

- `feat:`
- `fix:`
- `refactor:`
- `docs:`
- `test:`
- `chore:`
