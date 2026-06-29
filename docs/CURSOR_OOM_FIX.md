# Fix Cursor OOM (Out of Memory) - Code -536870904

Cursor crashes with "The window terminated unexpectedly (reason: 'oom', code: '-536870904')" when it runs out of memory. Use these steps to reduce memory usage.

## 1. Update .cursorignore (Project-Level)

Edit `.cursorignore` in your project root and add these lines so Cursor skips indexing heavy files:

```
# Add to existing .cursorignore:

# Migrations
migrations/

# Documentation
*.md
!README.md

# Binary / media
*.pdf
*.png
*.jpg
*.jpeg

# Agent transcripts
**/agent-transcripts/

# Deployment scripts
deploy*.ps1
deploy*.sh
cloudbuild.yaml
```

## 2. Cursor Settings (Application-Level)

1. Open **File → Preferences → Settings** (or `Ctrl+,`)
2. Search for **"memory"** or **"files watcher exclude"**
3. Add exclusions for: `**/node_modules`, `**/.venv`, `**/__pycache__`, `**/instance`, `**/app/static/uploads`

## 3. Reduce Memory Usage

| Action | Why |
|--------|-----|
| **Close unused tabs** | Each tab uses memory |
| **Restart Cursor every 2 hours** | Long sessions cause memory bloat |
| **Start new chats** | Old chat history increases memory |
| **Disable unused extensions** | Extensions add memory overhead |
| **Run Cursor with fewer extensions** | `cursor --disable-extensions` to test |

## 4. Windows-Specific

- Cursor (Electron) has a ~4GB limit on Windows
- Close other heavy apps (Chrome, other IDEs)
- Increase virtual memory: **Settings → System → About → Advanced system settings → Performance → Advanced → Virtual memory**

## 5. Quick Recovery When OOM Happens

1. Open **Task Manager** (`Ctrl+Shift+Esc`)
2. End any **Cursor** or **Cursor Helper** processes
3. Wait 5–10 seconds
4. Restart Cursor
5. Open only the folders/files you need

## 6. Check Memory (PowerShell)

```powershell
# See Cursor memory usage
Get-Process | Where-Object { $_.Name -like "*Cursor*" } | Select-Object Name, @{N='MB';E={[math]::Round($_.WorkingSet64/1MB)}}
```

Restart Cursor when usage is above ~3GB to avoid crashes.
