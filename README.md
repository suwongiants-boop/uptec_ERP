# Uptec Document ERP MVP

Uptec's document-centric ERP MVP is designed to manage customers, opportunities, technical assets, references, partners, and reusable document blocks in one system so proposal decks, company overviews, and project documents can be generated from approved data.

## Scope in this scaffold

- Django project skeleton
- Core CRM models
- Knowledge asset models
- Document template and generation job models
- Django admin configuration
- Basic dashboard view

## Recommended stack

- Python 3.12+
- Django 5.x
- PostgreSQL for production
- SQLite for local MVP development
- Celery + Redis for asynchronous document generation
- `docxtpl` and `python-pptx` for document output

## Local setup

1. Create a virtual environment.
2. Install dependencies from `requirements.txt`.
3. Run migrations.
4. Create a superuser.
5. Start the Django development server.

## Initial modules

- `core`: dashboard and shared utilities
- `crm`: customers, contacts, opportunities
- `knowledge`: technologies, references, patents, certifications, partners
- `documents`: templates, blocks, generated documents, generation jobs

## Next build steps

1. Add forms and workflow screens for opportunity-driven document generation.
2. Implement a block-based context assembler for PPTX/DOCX output.
3. Add approval flow and status transitions.
4. Integrate AI generation using only approved content blocks.

## Demo data

After migrations, you can load sample data with:

```powershell
python manage.py seed_mvp_data
```

This creates:

- a demo admin account
- a sample customer and opportunity
- a technology, reference, patent, and certification
- a proposal template with approved blocks
- a generated proposal draft

## GitHub sync for document versions

Every time a generated document is created or regenerated, the ERP stores a version snapshot under:

```text
document_versions/document-<id>/v###
```

The current default GitHub target is:

```text
https://github.com/suwongiants-boop/uptec_ERP
```

To complete automatic GitHub sync, the local project path must satisfy both conditions:

1. Git must be installed on the machine.
2. This project folder must be a real clone or initialized git repository linked to the remote.

Relevant settings in `uptek_erp/settings.py`:

```python
GITHUB_SYNC_REPO_PATH = BASE_DIR
GITHUB_SYNC_REMOTE_URL = "https://github.com/suwongiants-boop/uptec_ERP"
GITHUB_SYNC_PUSH = True
GITHUB_SYNC_GIT_EXECUTABLE = ""
```

If Git is missing or the folder is not a git repository yet, the ERP still records the version snapshot and shows a `Pending Setup` sync status in the document detail page.
