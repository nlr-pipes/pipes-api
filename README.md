# PIPES API

PIPES API built with FastAPI &amp; DocumentDB


**Prerequisites**:

* Docker - https://www.docker.com/get-started
* Docker Compose - https://docs.docker.com/compose/install/


## 1. Development Environment

### 1.1 Docker Compose

**Create `.mongo` and `.env`**

```bash
$ cd pipes-api
$ mkdir .mongo
$ touch .env
```

In `.env` file,

```
# Environment
PIPES_ENV=local

# MongoDB
PIPES_DOCDB_HOST=mongodb
PIPES_DOCDB_PORT=27017
PIPES_DOCDB_NAME=pipes_dev
PIPES_DOCDB_USER=pipes
PIPES_DOCDB_PASS=

# Cognito
PIPES_REGION=us-west-2
PIPES_COGNITO_USER_POOL_ID=
PIPES_COGNITO_CLIENT_ID=
PIPES_COGNITO_USERNAME=
PIPES_COGNITO_PASSWORD=
```

**Build Images**

```bash
$ docker compose build
```

**Run Containers**

```bash
$ docker compose up
```

Then visit [http://127.0.0.1:8080](http://127.0.0.1:8080)


### 1.2 Coding Styles

Create a Python virtual environment on your machine, and activate it. Then install Python packages for

```bash
$ pip install -r requirements-dev.txt
```

Then run

```bash
$ pre-commit install
```

`pre-commit` detects code problems before they enter the version control system. If any issue when committing, please
fix them, then add and commit again.

### 1.3 Automated Testing

Use `tox` to run tests,

```bash
$ tox
```


## 2. AI Coding Setup

This section provides guidance to setup AI coding agent and framework to assist the development of PIPES project.

### 2.1 Coding Assitant

There are many popular AI coding assistants, such as `Claude Code`, `GitHub Copilot`, `OpenAI Codex`,
`Gemini Coding Assistant` and so on. At NLR, we use Claude Code as coding assistant through Amazon Bedrock, please follow the steps below to setup.

**Install Claude Code**

https://code.claude.com/docs/en/quickstart

**Config the Models**
The initial models we setup are ANTHROPIC_MODEL=Sonnet4.6, ANTHROPIC_SMALL_FAST_MODEL=Haiku4.5.

Export the env variables below in your terminal session:


```text
export CLAUDE_CODE_USE_BEDROCK=1
export AWS_REGION='<aws-region>'
export ANTHROPIC_MODEL='<the-main-sonnet-model>'
export ANTHROPIC_SMALL_FAST_MODEL='<the-fast-haiku-model>'
```

These exports could be put into .bash_profile/.bashrc or .zshrc in user home dir, depending on the shell used on your machine.

**Set SSO credentials (Need to do everyday)**

Use NLR SSO login and find `pipes-llm-developer`under AWS account.

Click Access Keys and get SSO credentials, then paste into terminal session as well for exporting the AWS credentials.

Note: The SSO session would last for 8 hours, after that need to copy and paste new Access keys as credentials.

**Test Claude Code**

Start claude code by running claude command,

```bash
$ claude
```

### 2.2 Agentic Skills/Frameworks

Install agentic skills and frameworks to enhance Claude Code coding capability.

Enter claude code, and install plugins

```bash
/plugin
```

The following skills and frameworks are recommended:

* `superpowers`
* `context7`

Also, we need to install `openspec` for this project,

```bash
$ npm install -g @fission-ai/openspec@latest
```

Then navigate to the project root directory and initialize:

```bash
$ openspec init
```


## 2. Cognito Authentication

AWS Cognito has been integrated to authenticate access. Steps:

* Make sure your cognito username and password are configured in `.env`.
* Run `python scripts/get_cognito_access_token.py` to get the access token.
* Authenticate the Swagger Docs with the token for running API tests.

The access token would last for 12 hour before it expires.
After the expiration, you will need to re-run the script to get a new one.


## 3. Site Superuser
You can grant yourself as superuser at local for development.

```bash
$ docker-compose exec mongodb bash
```

Then type `mongo` to run mongo shell, and use `pipes_dev` database.

```
$ db.users.findOne({'email': <Your-Email>});

$ db.users.updateOne({'email': <Your-Email>}, {'$set': {is_superuser: true}})
```


## 4. Coding Workflow

PIPES adopts a hybrid spec-driven, test-driven development workflow using two complementary tools:

- **[OpenSpec](https://github.com/fission-ai/openspec)** — the planning layer. Structures feature proposals, spec deltas, design decisions, and task breakdowns before any code is written.
- **[Superpowers](https://github.com/obra/superpowers)** — the execution layer. A composable skill library for Claude Code that enforces TDD (RED-GREEN-REFACTOR), systematic debugging, and structured code review.

### Workflow Overview

```
Feature Request
      │
      ▼
 1. /opsx:propose       ← OpenSpec: create proposal, spec deltas, design, tasks
      │
      ▼
 2. Review & refine     ← Team reviews proposal.md, design.md, tasks.md
      │
      ▼
 3. /writing-plans      ← Superpowers: break tasks into TDD-ready steps
      │
      ▼
 4. /test-driven-development  ← Superpowers: implement each task RED→GREEN→REFACTOR
      │
      ▼
 5. /verification-before-completion  ← Superpowers: evidence-based sign-off
      │
      ▼
 6. /opsx:archive       ← OpenSpec: mark change complete, update base specs
```

### Step-by-Step Guide

**Step 1 — Propose (OpenSpec)**

Inside Claude Code, run:

```
/opsx:propose <change-name>
```

OpenSpec reads the codebase and existing specs, then generates a structured change under `openspec/changes/<change-name>/`:

```
openspec/changes/<change-name>/
├── proposal.md    # Rationale, objectives, scope
├── specs/         # Spec deltas — before/after requirement diffs
├── design.md      # Technical architecture and decisions
└── tasks.md       # Numbered implementation checklist (1.1, 1.2, 2.1 ...)
```

**Step 2 — Review**

Before writing any code, review `proposal.md`, `design.md`, and the spec deltas. Edit any of these files freely — OpenSpec is "fluid not rigid". The spec delta is the primary review artifact: it shows exactly what requirements are changing.

**Step 3 — Plan tasks (Superpowers)**

Once the proposal is agreed on, activate TDD-style planning:

```
/writing-plans
```

This breaks each item in `tasks.md` into bite-sized steps following the pattern: write failing test → verify failure → implement minimally → verify passing → commit.

**Step 4 — Implement with TDD (Superpowers)**

For each task, enforce RED-GREEN-REFACTOR:

```
/test-driven-development
```

Key rules the skill enforces:
- **RED**: Write one failing test first. Run it. Confirm it fails for the right reason.
- **GREEN**: Write the minimum code to make it pass. No extras.
- **REFACTOR**: Improve clarity while keeping all tests green.
- Any production code written before a failing test exists must be deleted entirely.

Run `tox` after each task to confirm nothing is broken.

**Step 5 — Verify (Superpowers)**

Before marking work done, run:

```
/verification-before-completion
```

This blocks "I think it works" claims and requires evidence (test output, manual checks) before closing a task.

**Step 6 — Archive (OpenSpec)**

Once all tasks are done and `tox` passes:

```
/opsx:archive
```

This moves the change to `openspec/changes/archive/` with a date prefix and updates the base specs, so future proposals have an accurate picture of the codebase.

### Quick Reference

| Situation | Tool | Command |
|---|---|---|
| Propose a new feature or fix | OpenSpec | `/opsx:propose <name>` |
| Resume in-progress work | OpenSpec | `/opsx:continue` |
| Break proposal into TDD steps | Superpowers | `/writing-plans` |
| Implement a task with TDD | Superpowers | `/test-driven-development` |
| Debug a failing test systematically | Superpowers | `/systematic-debugging` |
| Sign off on a completed task | Superpowers | `/verification-before-completion` |
| Archive a completed change | OpenSpec | `/opsx:archive` |


## 5. API Documentation

API documentation:  [http://localhost:8080/docs](http://localhost:8080/docs)
