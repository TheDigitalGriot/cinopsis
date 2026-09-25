@echo off
cd /d C:\Users\digit\GriotApps\Cinopsis
set CINOPSIS_ENABLE_CDP=1
set CINOPSIS_ENABLE_SELENIUM=1
C:\Users\digit\.local\bin\claude.exe --add-dir C:\Users\digit\GriotMeta\digital-griot-marketplace --permission-mode acceptEdits -p < C:\Users\digit\GriotApps\Cinopsis\.prism\shared\yt_fix_prompt.txt > %TEMP%\cinopsis_probe\ytfix.log 2>&1
echo DONE > %TEMP%\cinopsis_probe\YTFIX_EXIT
