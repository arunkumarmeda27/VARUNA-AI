# VARUNA-AI — GitHub Contribution Guide

## SIH26080: Regime-Aware AI Post-Processing of Monsoon Rainfall Forecasts

This document explains how the VARUNA-AI team should use GitHub while developing the project.

The goal is to keep the repository organized, prevent accidental changes to the main project, and make collaboration easy for all six members.

---

# 1. Golden Rule

## Do not work directly on `main`.

Use this workflow:

```text
Clone Repository
      ↓
Create Your Branch
      ↓
Work on Your Task
      ↓
Test Your Changes
      ↓
Commit
      ↓
Push Branch
      ↓
Create Pull Request
      ↓
Review
      ↓
Merge into main
```

---

# 2. Team Branches

Each member should have a branch related to their responsibility.

```text
main

feature/data-pipeline
feature/regime-model
feature/rainfall-correction
feature/verification
feature/backend
feature/geospatial-ui
```

## Recommended Ownership

| Member | Branch | Responsibility |
|---|---|---|
| Member 1 | `feature/data-pipeline` | Meteorological data and preprocessing |
| Member 2 | `feature/regime-model` | Weather regime classification |
| Member 3 | `feature/rainfall-correction` | Rainfall bias correction |
| Member 4 | `feature/verification` | Probability, uncertainty and verification |
| Member 5 | `feature/backend` | Django, Firebase Auth, APIs and database |
| Member 6 | `feature/geospatial-ui` | Geospatial processing, maps and UI |

Members may create smaller branches when a task is large, but changes should remain logically grouped.

---

# 3. First-Time Setup

## Step 1 — Install Git

Install Git from:

```text
https://git-scm.com/downloads
```

Verify:

```bash
git --version
```

---

## Step 2 — Configure Git

Run once:

```bash
git config --global user.name "Your Name"
git config --global user.email "your-github-email@example.com"
```

Use the GitHub account email associated with the project.

Verify:

```bash
git config --global --list
```

---

# 4. Clone the Repository

Clone the repository provided by the project owner:

```bash
git clone <REPOSITORY-URL>
```

Example:

```bash
git clone https://github.com/USERNAME/varuna-ai.git
```

Enter the project:

```bash
cd varuna-ai
```

Check the current branch:

```bash
git branch
```

---

# 5. Before Starting Work

Always update your local `main`.

```bash
git checkout main
git pull origin main
```

Then move to your working branch.

Example:

```bash
git checkout feature/regime-model
```

Update it with the newest `main`:

```bash
git merge main
```

Now start your work.

---

# 6. Create a New Branch

If the branch does not already exist:

```bash
git checkout -b feature/your-task
```

Examples:

```bash
git checkout -b feature/regime-model
```

```bash
git checkout -b feature/rainfall-correction
```

```bash
git checkout -b feature/verification
```

---

# 7. Work on Your Task

Work only on the files related to your assigned responsibility.

Example:

### Member 1

```text
weather_data/
preprocessing/
features/
```

### Member 2

```text
regimes/
```

### Member 3

```text
correction/
```

### Member 4

```text
probability/
uncertainty/
verification/
```

### Member 5

```text
backend/
authentication/
tasks/
```

### Member 6

```text
geospatial/
dashboard/
```

Avoid changing another member's module without coordination.

---

# 8. Check Your Changes

Before committing:

```bash
git status
```

Review the changed files.

For detailed changes:

```bash
git diff
```

Check for:

- Accidental files
- Temporary files
- Debug code
- Passwords or API keys
- Large unnecessary datasets
- Generated files that should not be committed

---

# 9. Never Commit Secrets

Never commit:

```text
API keys
Passwords
Firebase private credentials
Database passwords
Secret tokens
Environment secrets
```

Use environment variables and a `.env` file where appropriate.

The `.env` file should be excluded through `.gitignore`.

Example:

```text
.env
*.key
*.pem
```

Never upload service-account private keys to GitHub.

---

# 10. Test Before Commit

Every member should test their work before pushing.

Examples:

```bash
pytest
```

For application checks:

```bash
python manage.py check
```

Use the tests relevant to your module.

Do not submit code that has not been tested.

---

# 11. Add Changes

After testing:

```bash
git add .
```

Before committing, check what will be committed:

```bash
git status
```

If everything is correct:

```bash
git commit -m "Add weather regime classifier"
```

---

# 12. Commit Message Rules

Commit messages should explain the change.

## Good

```text
Add weather regime classifier
```

```text
Implement rainfall bias correction baseline
```

```text
Add forecast verification metrics
```

```text
Integrate Firebase authentication
```

```text
Add district rainfall map
```

## Avoid

```text
update
```

```text
changes
```

```text
done
```

```text
final
```

A commit should describe what changed.

---

# 13. Push Your Branch

First time:

```bash
git push -u origin feature/your-branch
```

Example:

```bash
git push -u origin feature/regime-model
```

After that:

```bash
git push
```

---

# 14. Pull Request

After pushing, open GitHub.

Go to:

```text
Pull Requests
    ↓
New Pull Request
```

Select:

```text
base:
main
```

and:

```text
compare:
your-feature-branch
```

Example:

```text
base: main
compare: feature/regime-model
```

---

# 15. Pull Request Description

Use a clear description.

Example:

```markdown
## What changed

Implemented the initial weather regime classification pipeline.

## Changes

- Added feature preparation
- Added baseline classifier
- Added XGBoost classifier
- Added inference function
- Added evaluation output

## Testing

- Model training completed
- Validation completed
- Confusion matrix generated

## Notes

No changes were made outside the regime module.
```

---

# 16. Review Process

The project owner or designated reviewer should check:

### Functionality

Does the code work?

### Scientific correctness

Are calculations and data transformations valid?

### Integration

Does the code match the agreed input/output format?

### Code quality

Is the implementation understandable?

### Security

Are secrets and credentials excluded?

### Testing

Has the change been tested?

Only after review should the Pull Request be merged.

---

# 17. After a Pull Request Is Merged

Update your local repository.

```bash
git checkout main
git pull origin main
```

Then return to your branch:

```bash
git checkout feature/your-branch
```

Update your branch:

```bash
git merge main
```

Resolve conflicts if necessary.

---

# 18. If There Is a Merge Conflict

Git may report:

```text
CONFLICT
```

Do not panic.

First:

```bash
git status
```

Git will tell you which files conflict.

Open the conflicting file and resolve the marked sections.

Then:

```bash
git add <resolved-file>
```

Commit:

```bash
git commit -m "Resolve merge conflict"
```

Then:

```bash
git push
```

If the conflict affects another member's code, communicate before changing their logic.

---

# 19. Issues for Task Management

Use GitHub Issues to assign actual work.

Examples:

```text
#1 Prepare rainfall dataset
#2 Implement regime classifier
#3 Build rainfall correction baseline
#4 Implement verification metrics
#5 Integrate Firebase Authentication
#6 Create forecast API
#7 Implement district map
```

Assign every issue to the correct member.

---

# 20. Linking Issues to Pull Requests

A Pull Request can reference its issue.

Example:

```text
Closes #2
```

When the Pull Request is merged, GitHub can close the issue.

This keeps the project history organized.

---

# 21. Labels

Recommended labels:

```text
data
machine-learning
regime
rainfall-correction
verification
backend
firebase
database
geospatial
frontend
bug
documentation
research
testing
```

Use labels consistently.

---

# 22. Project Directory Ownership

Recommended project structure:

```text
varuna-ai/
|
├── weather_data/
├── regimes/
├── correction/
├── probability/
├── uncertainty/
├── verification/
├── geospatial/
├── backend/
├── authentication/
├── dashboard/
├── tasks/
├── tests/
├── docs/
|
├── README.md
├── CONTRIBUTING.md
├── .gitignore
└── requirements/
```

---

# 23. What Each Member Should Push

## Member 1 — Data

Push:

```text
Data ingestion
Preprocessing
Alignment
Feature generation
Data documentation
```

Do not push:

```text
Large raw datasets
Private data
Secrets
```

---

## Member 2 — Regime ML

Push:

```text
Training code
Inference code
Model configuration
Evaluation code
Documentation
```

Large trained model files should use the project's agreed model-storage approach rather than being committed blindly to Git.

---

## Member 3 — Rainfall ML

Push:

```text
Baselines
Correction models
Inference code
Evaluation scripts
```

---

## Member 4 — Verification

Push:

```text
Probability logic
Uncertainty code
Verification metrics
Evaluation scripts
Scientific charts/scripts
```

Do not fabricate metrics.

---

## Member 5 — Backend

Push:

```text
Django code
API code
Database models
Firebase authentication integration
Celery tasks
Tests
```

Never push:

```text
.env
Firebase private keys
Database passwords
```

---

## Member 6 — Geospatial/UI

Push:

```text
District processing
Map layers
Charts
Templates
CSS
JavaScript
UI integration
```

Do not hard-code fake forecast values into the production interface.

---

# 24. Branch Naming

Recommended formats:

```text
feature/<name>
bugfix/<name>
research/<name>
docs/<name>
```

Examples:

```text
feature/regime-classifier
feature/rainfall-correction
feature/district-map
bugfix/time-alignment
research/model-comparison
docs/data-pipeline
```

---

# 25. Commit Frequency

Do not make one giant commit after several days.

Prefer small, meaningful commits.

Example:

```text
Add data parser
Add temporal alignment
Add feature generation
Add dataset validation
```

This makes review and debugging easier.

---

# 26. Pull Request Rules

Each Pull Request should ideally:

- Solve one logical task.
- Have a clear description.
- Include testing information.
- Avoid unrelated changes.
- Avoid generated junk files.
- Avoid secrets.
- Be small enough to review.

---

# 27. Main Branch Protection

The repository owner should protect `main`.

Recommended settings:

```text
Require Pull Request before merging
Require review
Prevent force pushes
Prevent direct uncontrolled changes
```

This ensures that the stable branch remains usable.

---

# 28. Daily Team Workflow

## Start of work

```bash
git checkout main
git pull origin main
git checkout feature/your-branch
git merge main
```

## During work

```text
Develop
Test
Review
```

## End of work

```bash
git status
git add .
git commit -m "Describe the change"
git push
```

Then update the Pull Request.

---

# 29. Complete Example

Suppose Member 2 is implementing the regime classifier.

### Step 1

```bash
git checkout main
git pull origin main
```

### Step 2

```bash
git checkout -b feature/regime-model
```

### Step 3

Develop:

```text
regimes/
├── training/
├── inference/
└── evaluation/
```

### Step 4

Test:

```bash
pytest
```

### Step 5

Check changes:

```bash
git status
git diff
```

### Step 6

Commit:

```bash
git add regimes/
git commit -m "Implement weather regime classifier"
```

### Step 7

Push:

```bash
git push -u origin feature/regime-model
```

### Step 8

Create Pull Request:

```text
feature/regime-model -> main
```

### Step 9

Team reviews.

### Step 10

Merge.

---

# 30. Integration Rule for VARUNA-AI

The repository must follow the actual system dependency:

```text
Member 1
DATA
  |
  v
Members 2, 3, 4
ML + VERIFICATION
  |
  v
Member 5
BACKEND / INTEGRATION
  |
  v
Member 6
GEO + UI
```

The code should reflect this dependency.

Do not make the UI dependent on hard-coded data while the real model pipeline is being developed.

---

# 31. First Shared Milestone

Before building a polished dashboard, the team should be able to execute:

```text
Dataset
   ↓
Regime Model
   ↓
Rainfall Correction
   ↓
Heavy Rain Probability
   ↓
Verification
   ↓
District Output
```

The result should be generated from real project data.

---

# 32. Team Communication Rule

When your change affects another member, tell them before merging.

Examples:

```text
"I changed the forecast JSON schema."
"I renamed this feature."
"I changed the district identifier."
"I changed the model output format."
```

Shared interfaces must not change silently.

---

# 33. Git Commands Cheat Sheet

## Clone

```bash
git clone <repo-url>
```

## Check status

```bash
git status
```

## Create branch

```bash
git checkout -b feature/name
```

## Switch branch

```bash
git checkout branch-name
```

## Update main

```bash
git checkout main
git pull origin main
```

## Update your branch

```bash
git merge main
```

## Stage

```bash
git add .
```

## Commit

```bash
git commit -m "Describe the change"
```

## Push

```bash
git push
```

## Pull

```bash
git pull
```

## View branches

```bash
git branch
```

## View commit history

```bash
git log --oneline
```

---

# 34. What NOT to Do

### Do not

```text
git push directly to main
```

unless the repository owner explicitly permits it.

### Do not

```text
git add .
```

without checking what files changed.

### Do not

Commit:

```text
.env
credentials
private keys
large raw datasets
temporary files
IDE files
```

### Do not

Copy another member's code into your branch without coordination.

### Do not

Force-push shared branches without agreement.

### Do not

Merge untested code just because the deadline is close.

---

# 35. Final Workflow

Every contribution should follow:

```text
1. Get the latest main
        ↓
2. Create/use your feature branch
        ↓
3. Implement your assigned task
        ↓
4. Test it
        ↓
5. Review your changes
        ↓
6. Commit with a meaningful message
        ↓
7. Push your branch
        ↓
8. Open Pull Request
        ↓
9. Review
        ↓
10. Merge
        ↓
11. Update your local branch
```

---

# 36. Final Team Rule

GitHub is the team's **source-control and collaboration system**, not a file-sharing folder.

The correct contribution model is:

> **Clone → Branch → Develop → Test → Commit → Push → Pull Request → Review → Merge**

For VARUNA-AI, the repository should always preserve a stable `main` branch while individual members develop their assigned components in separate branches.

The goal is simple:

```text
6 Developers
     ↓
1 Repository
     ↓
1 Integrated System
     ↓
VARUNA-AI
```
