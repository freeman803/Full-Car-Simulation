@echo off
setlocal enableextensions

set XOF=
set TMPSTR=
set VIG_CMD="C:/Program Files/VI-grade/VI-CarRealTime 2025/common/vig"
call %VIG_CMD% > nul 2>&1
if %ERRORLEVEL% neq 0 (
  set VIG_CMD=vig2025
)
:parse_args
if "%1"=="" goto run_script
set TMPSTR=%1
if "%TMPSTR:~0,5%"=="/xof:" goto xof_found
shift
goto parse_args

:xof_found
set XOF_OPT=-xof=%TMPSTR:~5%
set XOF_MSG=[%TMPSTR:~5%]
shift
goto parse_args

:run_script 
set VICRT_PY_PPT=.\custom_ppt
set sendfile=VI_Racer_E_Endurance_send_svm.xml
if defined VICRT_MULTIRUN goto muted

call %VIG_CMD% acreal ru-mxp %sendfile% %XOF_OPT%
goto alldone

:muted
echo Running background simulation %sendfile% %XOF_MSG% ...
call %VIG_CMD% acreal ru-mxp %sendfile% %XOF_OPT% >nul 2>nul

:alldone
if ERRORLEVEL 0 (
  exit 0
) else (
  echo  -- ERROR -- %sendfile% %XOF_MSG% simulation failure.
  exit 1
)
endlocal
