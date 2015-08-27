@echo off
setlocal enabledelayedexpansion

set PYTHON=
for %%i in (pythonw.exe) do (set PYTHON=%%~$PATH:i)

echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "EagleEye Wizard.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "!PYTHON!" >> CreateShortcut.vbs
echo oLink.Arguments = "wizard.py" >> CreateShortcut.vbs
echo oLink.WorkingDirectory = "%~dp0" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs