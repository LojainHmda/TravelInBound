# Quick memory check - run when Cursor feels slow or before OOM
# Usage: .\check-memory.ps1

Write-Host "=== Cursor / Code Processes ===" -ForegroundColor Cyan
Get-Process -Name "Cursor","Code" -ErrorAction SilentlyContinue | 
    Select-Object Id, ProcessName, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet64/1MB,2)}}, CPU |
    Format-Table -AutoSize

Write-Host "=== Python Processes ===" -ForegroundColor Cyan
Get-Process -Name "python","python3" -ErrorAction SilentlyContinue | 
    Select-Object Id, ProcessName, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet64/1MB,2)}}, CPU |
    Format-Table -AutoSize

Write-Host "=== Node Processes (if any) ===" -ForegroundColor Cyan
Get-Process -Name "node" -ErrorAction SilentlyContinue | 
    Select-Object Id, ProcessName, @{N='Memory(MB)';E={[math]::Round($_.WorkingSet64/1MB,2)}}, CPU |
    Format-Table -AutoSize

Write-Host "Tip: Restart Cursor if memory > 3GB. Keep chat sessions under 2 hours." -ForegroundColor Yellow
