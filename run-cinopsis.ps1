$ErrorActionPreference="Continue"
Set-Location "C:\Users\digit\GriotApps\Cinopsis"
$pr = Get-Content ".\router-cinopsis.md" -Raw
& "C:\Users\digit\.local\bin\claude.exe" --agent claude --dangerously-skip-permissions --verbose -p $pr *> ".\cinopsis-icm-run.log"
