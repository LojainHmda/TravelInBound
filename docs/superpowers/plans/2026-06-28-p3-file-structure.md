# P3 File Structure & Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Move ~80 root-level loose files to proper directories. Delete dead files (backups, test PDFs, one-off scripts). Single `start_server.py` entry point. Result: professional enterprise structure that a new developer can understand in 5 minutes.

**Architecture:** No code changes — only moves, deletes, and import path checks. All migration scripts go to `scripts/migrations/`. All deployment files go to `deploy/`. All documentation goes to `docs/`. Dead files deleted. Single entry point `start_server.py` stays; `main.py`, `_start.py`, `start_tmp.py` deleted.

**Tech Stack:** Git (mv + rm), PowerShell/Bash file operations

**Prerequisite:** P0, P1, P2 complete. Working TEST DB. Green tests.

## Global Constraints

- NEVER delete a file without first confirming it's not imported anywhere
- Run `grep -r "import <module>"` before deleting any Python file
- App must start cleanly after every batch of moves
- All moves done via `git mv` to preserve history
- `.env` never moved — stays at root (dotenv loads from project root)

---

## Target Structure

```
TravelInBound/
├── app/                          ← Flask application (unchanged)
│   ├── core/                     ← enums, auth decorators (added in P2)
│   ├── models/                   ← all models
│   ├── routes/                   ← all blueprints
│   ├── services/                 ← business logic services
│   ├── static/                   ← CSS, JS, images
│   ├── templates/                ← Jinja2 templates
│   ├── forms/                    ← WTForms
│   ├── data/                     ← static data (nationalities.py)
│   ├── api_exemptions.py
│   ├── config.py
│   ├── extensions.py
│   └── __init__.py
├── migrations/                   ← Alembic versions (added in P0)
├── tests/                        ← pytest suite (added in P0)
├── scripts/                      ← admin/utility scripts (moved from root)
│   └── migrations/               ← one-off ALTER TABLE scripts (archived)
├── deploy/                       ← ALL deployment files (moved from root)
│   ├── Dockerfile
│   ├── cloudbuild.yaml
│   ├── deploy.sh
│   ├── deploy.ps1
│   └── ...
├── docs/                         ← ALL .md docs (moved from root)
│   ├── superpowers/plans/
│   └── deployment/
├── .env                          ← never moved
├── .env.example
├── .gitignore
├── requirements.txt
├── pyproject.toml
└── start_server.py               ← single entry point
```

---

### Task 1: Move deployment files to deploy/

**Files:**
- Create dir: `deploy/`
- Move: all deploy-related files from root

- [ ] **Step 1: Create deploy/ directory**

```bash
mkdir deploy
```

- [ ] **Step 2: Move deployment files**

```bash
git mv Dockerfile deploy/Dockerfile
git mv cloudbuild.yaml deploy/cloudbuild.yaml
git mv deploy.sh deploy/deploy.sh
git mv deploy.ps1 deploy/deploy.ps1
git mv deploy-cloud-run.ps1 deploy/deploy-cloud-run.ps1
git mv deploy-cloudbuild.ps1 deploy/deploy-cloudbuild.ps1
git mv deploy-on-vm.sh deploy/deploy-on-vm.sh
git mv deploy-ubuntu.sh deploy/deploy-ubuntu.sh
git mv deploy-vm.ps1 deploy/deploy-vm.ps1
git mv deploy-vm.sh deploy/deploy-vm.sh
git mv build.ps1 deploy/build.ps1
git mv install-and-deploy.ps1 deploy/install-and-deploy.ps1
git mv grant-deploy-permissions.ps1 deploy/grant-deploy-permissions.ps1
git mv run_server.bat deploy/run_server.bat
git mv run_server.ps1 deploy/run_server.ps1
git mv check-vm-status.sh deploy/check-vm-status.sh
git mv fix-ip-access.sh deploy/fix-ip-access.sh
git mv troubleshoot-vm-access.sh deploy/troubleshoot-vm-access.sh
git mv deploy-source.zip deploy/deploy-source.zip
git mv deploy.tar.gz deploy/deploy.tar.gz
git mv verify-production.ps1 deploy/verify-production.ps1
git mv fix-production-database.ps1 deploy/fix-production-database.ps1
git mv check-memory.ps1 deploy/check-memory.ps1
git mv check_server_status.py deploy/check_server_status.py
git mv check_db_connection.py deploy/check_db_connection.py
```

- [ ] **Step 3: Verify app still starts**

```bash
.venv/Scripts/python.exe -c "from app import create_app; create_app(); print('OK')"
```
Expected: `OK`

- [ ] **Step 4: Commit**

```bash
git add deploy/
git commit -m "refactor: move all deployment files to deploy/ directory"
```

---

### Task 2: Move documentation to docs/

**Files:**
- Move: all .md files from root to `docs/`

- [ ] **Step 1: Create docs/deployment subdirectory**

```bash
mkdir -p docs/deployment
```

- [ ] **Step 2: Move markdown docs**

```bash
git mv DEPLOYMENT.md docs/deployment/DEPLOYMENT.md
git mv CLOUD_RUN_DEPLOYMENT_STEPS.md docs/deployment/CLOUD_RUN_DEPLOYMENT_STEPS.md
git mv DEPLOY_NOW.md docs/deployment/DEPLOY_NOW.md
git mv DEPLOY_VIA_CONSOLE.md docs/deployment/DEPLOY_VIA_CONSOLE.md
git mv DEPLOY_WITH_DATABASE.md docs/deployment/DEPLOY_WITH_DATABASE.md
git mv UBUNTU_DEPLOYMENT.md docs/deployment/UBUNTU_DEPLOYMENT.md
git mv VM_DEPLOYMENT.md docs/deployment/VM_DEPLOYMENT.md
git mv VM_DEPLOYMENT_GUIDE.md docs/deployment/VM_DEPLOYMENT_GUIDE.md
git mv VM_DEPLOYMENT_INSTRUCTIONS.md docs/deployment/VM_DEPLOYMENT_INSTRUCTIONS.md
git mv PRODUCTION_SETUP.md docs/deployment/PRODUCTION_SETUP.md
git mv README_DEPLOYMENT.md docs/deployment/README_DEPLOYMENT.md
git mv FIX_IP_ACCESS_WINDOWS.md docs/FIX_IP_ACCESS_WINDOWS.md
git mv FIX_VM_ACCESS.md docs/FIX_VM_ACCESS.md
git mv FIX_WINDOWS_FIREWALL.md docs/FIX_WINDOWS_FIREWALL.md
git mv WINDOWS_SERVER_FIX.md docs/WINDOWS_SERVER_FIX.md
git mv CURSOR_OOM_FIX.md docs/CURSOR_OOM_FIX.md
git mv NEXT_STEPS.md docs/NEXT_STEPS.md
git mv SERVER_STATUS.md docs/SERVER_STATUS.md
git mv START_SERVER.md docs/START_SERVER.md
git mv REQUEST_STATUS_SINGLE_SOURCE_OF_TRUTH.md docs/REQUEST_STATUS_SINGLE_SOURCE_OF_TRUTH.md
git mv SINGLE_SOURCE_OF_TRUTH_FIX.md docs/SINGLE_SOURCE_OF_TRUTH_FIX.md
git mv STATUS_CONSTANT_BUG_FIX.md docs/STATUS_CONSTANT_BUG_FIX.md
git mv UI_DESIGN_GUIDE.md docs/UI_DESIGN_GUIDE.md
git mv TravelBookPro_BRD.md docs/TravelBookPro_BRD.md
git mv ai_mapping_explanation.md docs/ai_mapping_explanation.md
git mv replit.md docs/replit.md
```

- [ ] **Step 3: Commit**

```bash
git add docs/
git commit -m "refactor: move all markdown docs to docs/ directory"
```

---

### Task 3: Move one-off migration scripts to scripts/migrations/

- [ ] **Step 1: Create scripts/migrations/**

```bash
mkdir -p scripts/migrations
```

- [ ] **Step 2: Move migration scripts (archive — not deleted, just organized)**

```bash
git mv add_arrival_notes_column.py scripts/migrations/
git mv add_arrival_notes_simple.py scripts/migrations/
git mv add_customer_type_column.py scripts/migrations/
git mv add_departure_notes_column.py scripts/migrations/
git mv add_hotel_room_distribution.py scripts/migrations/
git mv add_invoice_data_columns.py scripts/migrations/
git mv add_languages_column.py scripts/migrations/
git mv add_pax_count_to_meal.py scripts/migrations/
git mv add_sample_prepayment_line.py scripts/migrations/
git mv add_service_confirmations.py scripts/migrations/
git mv add_supplier_indexes.py scripts/migrations/
git mv add_supplier_services.py scripts/migrations/
git mv apply_meal_pax_migration.py scripts/migrations/
git mv expand_nationality_column.py scripts/migrations/
git mv fix_all_schema.py scripts/migrations/
git mv fix_dashboard_buttons.py scripts/migrations/
git mv fix_invoice_sequence.py scripts/migrations/
git mv fix_sequence.py scripts/migrations/
git mv fix_supplier_complete.py scripts/migrations/
git mv fix_supplier_prepayment_links.py scripts/migrations/
git mv fix_supplier_schema.py scripts/migrations/
git mv migrate_prepayment_lines.py scripts/migrations/
git mv migrate_sqlite_to_postgres.py scripts/migrations/
git mv run_production_migrations.py scripts/migrations/
git mv simple_migration.py scripts/migrations/
git mv update_customer_phone_constraint.py scripts/migrations/
git mv update_finance_module_schema.py scripts/migrations/
git mv update_invoice_schema.py scripts/migrations/
git mv update_payments_from_documents.py scripts/migrations/
git mv update_service_items_schema.py scripts/migrations/
git mv update_supplier_payment_schema.py scripts/migrations/
git mv update_supplier_payments.py scripts/migrations/
git mv update_supplier_prepayment_model.py scripts/migrations/
git mv update_supplier_schema.py scripts/migrations/
git mv update_user_schema.py scripts/migrations/
git mv update_dashboard.py scripts/migrations/
git mv update_dashboard_add_view_booking.py scripts/migrations/
```

- [ ] **Step 3: Move utility scripts to scripts/**

```bash
git mv init_db.py scripts/init_db.py
git mv init_users.py scripts/init_users.py
git mv initialize_test_data.py scripts/initialize_test_data.py
git mv create_tables.py scripts/create_tables.py
git mv create_supplier_payment.py scripts/create_supplier_payment.py
git mv create_supplier_prepayment_lines.py scripts/create_supplier_prepayment_lines.py
git mv clear_all_suppliers.py scripts/clear_all_suppliers.py
git mv clear_suppliers_now.py scripts/clear_suppliers_now.py
git mv populate_all_supplier_prepayments.py scripts/populate_all_supplier_prepayments.py
git mv populate_inbound_data.py scripts/populate_inbound_data.py
git mv link_customers_to_bookings.py scripts/link_customers_to_bookings.py
git mv performance_analysis.py scripts/performance_analysis.py
git mv performance_monitor.py scripts/performance_monitor.py
git mv check_arrival_notes.py scripts/check_arrival_notes.py
git mv replit_auth.py scripts/replit_auth.py
```

- [ ] **Step 4: Commit**

```bash
git add scripts/
git commit -m "refactor: move migration scripts to scripts/migrations/, utility scripts to scripts/"
```

---

### Task 4: Delete dead files

**CRITICAL:** Verify each file is unimported before deleting.

- [ ] **Step 1: Check orphaned root Python files**

```bash
# These are old pre-refactor files — verify not imported anywhere
grep -r "import models\|from models\|import routes\|from routes\|import forms\|from forms" app/ start_server.py
```
Expected: no output (app uses `app.models.*` not root `models.py`)

- [ ] **Step 2: Delete orphaned Python files at root**

```bash
git rm models.py
git rm routes.py  
git rm forms.py
git rm app.py.backup
```

- [ ] **Step 3: Delete test artifacts**

```bash
git rm test_final.pdf
git rm test_voucher.pdf
git rm test_voucher_final.pdf
git rm test_voucher_main.pdf
git rm test_save.json
git rm cookies.txt
git rm error.txt
git rm output.txt
```

- [ ] **Step 4: Delete duplicate/orphaned test scripts**

```bash
# Check each before deleting
grep -r "test_customer_relationship\|test_inbound_save\|test_populate\|test_run\|test_voucher_fix" app/ start_server.py
# Expected: no imports

git rm test_customer_relationship.py
git rm test_inbound_save.py
git rm test_populate.py
git rm test_run.py
git rm test_voucher_fix.py
```

- [ ] **Step 5: Delete broken service file**

```bash
git rm app/services/airline_voucher_generator_broken.py
```

- [ ] **Step 6: Delete template backup files**

```bash
git rm app/templates/dashboard.html.bak
git rm "app/templates/inbound/view_request.html.backup"
git rm app/templates/inbound/view_request_backup.html
git rm app/templates/dashboard_redesigned.html
```

- [ ] **Step 7: Delete HTML fragments at root**

```bash
git rm action_buttons.html
git rm customer_selection_modal.html
git rm flight_confirmation_form_complete.html
git rm status_flow_example.html
git rm test_download.html
```

- [ ] **Step 8: Delete images at root (moved to app/static already)**

```bash
git rm arabilogo.jpg
git rm generated-icon.png
git rm fullpage.png
git rm inbound_417_closed_workflow.png
git rm inbound_417_open_workflow.png
git rm inbound_detail_full.png
git rm inbound_detail_fullpage.png
git rm top_of_detail.png
git rm workflow_sidebar_open.png
```

- [ ] **Step 9: Delete duplicate entry points**

```bash
# Verify these aren't used anywhere
git rm main.py         # duplicate of start_server.py
git rm _start.py       # duplicate
git rm start_tmp.py    # temporary file
```

- [ ] **Step 10: Delete unknown files**

```bash
git rm -f analy        # unknown file
git rm -f -- -w        # unknown file named "-w"
```

- [ ] **Step 11: Add generated files to .gitignore**

Add to `.gitignore`:
```
# Generated files
*.pdf
test_*.json
*.log
output*.txt
error*.txt
server*.log
cookies.txt
```

- [ ] **Step 12: Verify app starts**

```bash
.venv/Scripts/python.exe start_server.py &
# Wait 5 seconds
curl http://127.0.0.1:5000/health
```
Expected: `{"status": "ok"}` or redirect to login (200/302)

- [ ] **Step 13: Run full test suite**

```bash
.venv/Scripts/python.exe -m pytest tests/ -v
```
Expected: all tests pass (no failures from file moves)

- [ ] **Step 14: Commit**

```bash
git add .gitignore
git commit -m "refactor: delete dead files (backups, test artifacts, duplicate entry points, broken service)"
```

---

### Task 5: Final verification and README

- [ ] **Step 1: Count root-level files**

```bash
ls -1 | wc -l
```
Expected: ≤ 12 files at root:
`.env`, `.env.example`, `.gitignore`, `requirements.txt`, `pyproject.toml`, `uv.lock`, `start_server.py`, `.replit`, `Dockerfile` (if not moved), `README.md`

- [ ] **Step 2: Run complete test suite**

```bash
.venv/Scripts/python.exe -m pytest tests/ -v --tb=short
```
Expected: all tests pass

- [ ] **Step 3: Start server and smoke test**

```bash
.venv/Scripts/python.exe start_server.py
```
Open http://127.0.0.1:5000 — login page loads
Login as admin/admin123 — hub loads
Navigate to /inbound/ — inbound list loads
Navigate to /finance/ — finance loads
Navigate to /inbound/analytics — analytics loads

- [ ] **Step 4: Final commit**

```bash
git add .
git commit -m "refactor(p3): enterprise file structure — root cleaned, 12 files only, all tests pass"
```

---

## Plan Complete

After all 5 tasks:

**Root contains only:**
```
.env              (gitignored)
.env.example
.gitignore
requirements.txt
pyproject.toml
uv.lock
start_server.py   (single entry point)
README.md
```

**All code in `app/`.**
**All migrations in `migrations/`.**
**All tests in `tests/`.**
**All scripts in `scripts/`.**
**All deployment in `deploy/`.**
**All docs in `docs/`.**

New developer onboarding time: 5 minutes instead of 30.
