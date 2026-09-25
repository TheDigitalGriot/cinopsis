@echo off
cd /d C:\Users\digit\GriotApps\Cinopsis
del "%TEMP%\cinopsis_probe\BATCH2_DONE" 2>nul
C:\Python314\python.exe scripts\fetch_transcripts.py --ids %* --chunk 5 > "%TEMP%\cinopsis_probe\batch2.log" 2>&1
echo DONE > "%TEMP%\cinopsis_probe\BATCH2_DONE"
