# Local Lens

Photo-based civic reporting built with Python, Streamlit and Supabase. Residents
turn a photograph into an editable, structured issue report; reviewers can browse
reports, map locations and use a council dashboard to prioritise follow-up.

[Live beta](https://localens.streamlit.app/) · [Application entry point](app.py) ·
[Image-analysis service](src/services/ai_service.py)

## Interface preview

![Local Lens landing screen](https://raw.githubusercontent.com/t3hj/portfolio-website/main/assets/projects/local%20lens%20dashboard.png)

Existing portfolio capture, retained as an interface illustration rather than a live data view.

## What is implemented

- Email/password accounts through Supabase Auth and signed-in report submission.
- Claude image analysis when an Anthropic key is configured, or local Ollama
  analysis when enabled. Manual reporting remains available when AI is optional.
- Editable title, category, severity, details, location and recommended action.
- EXIF coordinates, optional text geocoding, report filters and map views.
- Identical-image hashes and short-term repeat-submission checks.
- Priority scoring, council insights and report status workflows.
- Optional SMTP notifications and local JSON metadata exports.

AI suggestions require human review. The repository is a prototype, not evidence
of an integration with a council's production systems.

## Architecture

| Layer | Implementation |
| --- | --- |
| Interface | Streamlit tabs and components in `src/ui/` |
| Application logic | Upload, AI, priority, notification and backup services in `src/services/` |
| Data | Supabase PostgreSQL, Auth and Storage |
| Image analysis | Claude first when configured; otherwise enabled Ollama; otherwise manual input |
| Location | Image metadata and optional geocoding helpers in `src/utils/` |

The current repository is a Python/Streamlit application. Do not describe this
checkout as a React/Next.js implementation.

## Local development

Use Python 3.12 and a virtual environment. Run commands from the repository root:

```sh
git clone https://github.com/t3hj/Local-Lens.git
cd Local-Lens
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

On Windows PowerShell, activate with `.\.venv\Scripts\Activate.ps1` instead.
The requirements file includes historical dependencies; a clean install and
hosted-service integration still need verification before deployment.

Create `.streamlit/secrets.toml` (ignored by Git):

```toml
SUPABASE_URL = "https://your-project.supabase.co"
SUPABASE_KEY = "your-anon-key"
SUPABASE_BUCKET = "report-images"
SUPABASE_TABLE = "reports"
COUNCIL_ADMIN_PASSWORD = "replace-with-a-unique-local-password"

# Optional cloud image analysis; keep this server-side.
ANTHROPIC_API_KEY = ""
ENABLE_OLLAMA = "false"
OLLAMA_URL = "http://localhost:11434"
OLLAMA_MODEL = "llava"
REQUIRE_AI = "false"
REQUIRE_GEOLOCATION = "false"
ENABLE_GEOCODING = "true"
```

```sh
python -m streamlit run app.py
```

An empty Anthropic key disables that provider. `REQUIRE_AI` blocks submissions
when analysis is unavailable; `REQUIRE_GEOLOCATION` requires coordinates.
See [settings](config/settings.py) for optional SMTP configuration. Leave SMTP
credentials unset during local review to avoid sending emails.

### Database setup is not yet self-contained

A working development Supabase project needs the report table, storage bucket,
Auth settings and appropriate RLS/storage policies. Core report fields include
`id`, `filename`, `cloud_storage_url`, `upload_date`, `version`, `title`,
`category`, `severity`, `additional_details`, `recommended_action`, `location`,
`latitude`, `longitude`, `reporter_id` and `image_hash`. This list is not a complete
migration for every feature; inspect the upload service for status/voting paths.

**Do not run `src/database/migrations/001_initial_schema.sql` in Supabase.** It is
legacy SQLite-style SQL for an earlier image-storage design and does not create
the current PostgreSQL report schema. A reviewed, reproducible migration is an
outstanding task. Use synthetic reports in a separate development project.

## Security and data boundaries

- Supabase clients are scoped to a Streamlit visitor session because Auth calls
  mutate client state. Never cache an authenticated client across visitors.
- Set a council password before enabling council views. A shared password is a
  prototype boundary, not a replacement for database-enforced staff roles.
- Prefer an anon key with explicit RLS. A service-role key bypasses RLS; do not
  use one as a shortcut to repair table permissions. The current notification
  helper's admin email lookup needs a privileged credential and should be
  separated from the visitor client before production use.
- Backups are **unencrypted JSON metadata exports**, not image backups. Protect
  their filesystem location and do not commit or share report exports.
- Images and coordinates can identify people or locations. Use consented or
  synthetic examples in demos, and verify bucket visibility and retention rules.

## Verification

Install pytest separately for development:

```sh
python -m pip install pytest
python -m pytest tests/test_session_boundaries.py -q
python -m compileall -q app.py config src
```

The boundary tests use fake services and do not access Supabase or send email.
They are regression checks, not proof of live RLS or account isolation in a
configured deployment.

The historical `tests/test_storage/` suite is currently incompatible with its
implementation: it imports `Versioning` while the module defines
`VersioningManager`, and constructs `CloudStorage` without its required bucket.
A full `python -m pytest` run therefore does not pass. These old tests do not
cover the active Supabase upload/report workflow.

The `docker/` files also describe an older topology, including placeholder
storage and SQLite services and an incompatible build context. Use the Python
setup above until that configuration is replaced and tested.

## Next engineering priorities

1. Export and review the current schema and least-privilege policies for a clean setup.
2. Replace the shared council password with explicit staff authorisation.
3. Separate privileged notification lookups from resident-facing data access.
4. Replace legacy storage tests with mocked report-flow tests and disposable-project integration tests.
5. Reduce and lock runtime dependencies, then rebuild the container configuration.
