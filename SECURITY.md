# Security Policy

## Reporting a vulnerability

Please report security issues privately to the maintainer via GitHub:
open a **private** advisory at
<https://github.com/lordlucky-254/kenya-data-explorer-dashboard/security/advisories/new>
or contact [@lordlucky-254](https://github.com/lordlucky-254) directly.

Do **not** open a public issue for a suspected vulnerability.

## Scope & notes

- This is a demonstration dashboard using a synthetic dataset. It stores no
  user data, has no authentication, and makes no external API calls.
- The in-app SQL Explorer is strictly read-only: only `SELECT` / `WITH`
  statements are allowed, executed against an in-memory SQLite database with
  a SQLite authorizer that denies writes, DDL, and pragmas.
- Custom CSV uploads are validated against a strict 7-column schema before
  use; malformed files are rejected with a clear error.
- Dependencies are pinned with lower/upper bounds in `requirements.txt` and
  should be kept current. Dependabot / manual `pip install -U` updates are
  welcome via pull request.

## Supported versions

Only the latest release on `main` is supported. Please update to the newest
version before reporting an issue.
