# Windows PowerShell Compatibility Layer for Trading Bot
# Use these commands instead of bash-style syntax

# COMMAND SEPARATORS (PowerShell vs Bash)
# Bash:   command1 && command2    (run if first succeeds)
# PS:     command1; command2      (always run both)
# PS:     if ($?) { command2 }    (run second only if first succeeds)

# EXAMPLES:

# ✅ CORRECT - Change directory and run
# cd C:\path; python script.py

# ✅ CORRECT - Check if command succeeded
# git status
# if ($LASTEXITCODE -eq 0) { Write-Host "Success" }

# ✅ CORRECT - Fallback if command fails  
# try { git status } catch { Write-Host "Not a git repo" }

# ✅ CORRECT - File existence check
# if (Test-Path file.txt) { Get-Content file.txt }

# ❌ WRONG - Bash syntax won't work
# cd path && python script.py
# command || echo "fallback"
# ls -la 2>/dev/null || echo "missing"

# COMMON POWERShell EQUIVALENTS:
# ls -la           →   Get-ChildItem -Force   OR   dir
# cat file         →   Get-Content file
# touch file       →   New-Item -ItemType File file
# rm -rf dir       →   Remove-Item -Recurse -Force dir
# mkdir -p dir     →   New-Item -ItemType Directory -Force dir
# which cmd        →   Get-Command cmd
# > file.txt       →   works the same (redirection)
# 2>&1             →   works the same (stderr to stdout)
