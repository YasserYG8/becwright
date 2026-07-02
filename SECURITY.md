# Security Policy

## Supported versions

becwright ships fixes on the latest release only. Please make sure you are on
the most recent version before reporting.

| Version | Supported |
| ------- | --------- |
| latest `1.x` | ✅ |
| older releases | ❌ |

## Reporting a vulnerability

**Please do not open a public issue for security problems.**

Report privately through GitHub:

1. Go to the repository's **Security** tab.
2. Click **Report a vulnerability** (GitHub Private Vulnerability Reporting).
3. Describe the issue, the impact, and a reproduction if you have one.

You can expect an acknowledgement within **72 hours** and a triage update within
a week. Once a fix is available we will coordinate a release and credit you in
the changelog unless you prefer to stay anonymous.

## Security model — what to keep in mind

becwright runs **checks** (shell commands) on every commit, and a BEC bundle can
carry a check's code. Two properties are load-bearing:

- **`becwright import` / `add` show the check's code and ask for confirmation**
  before installing it. Importing a BEC is importing code that will run on every
  commit — treat an untrusted bundle like any untrusted script.
- The engine itself has **no `eval`/`exec`** and depends only on `pyyaml`; this
  is enforced on becwright's own repo by its own BECs (dogfooding).

If you find a way to make becwright run code without the confirmation gate, or to
bypass a blocking rule, that is a vulnerability — please report it.
