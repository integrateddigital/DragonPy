@echo off

title "%~0"

REM ~ set python=C:\Python27\python.exe
set python=D:\pypy-2.3.1-win32\pypy.exe
if NOT exist %python% (
    echo Error: '%python%' doesn't exists?!?
    pause
    exit 1
)

echo on
REM ~ %python% console_6809_test.py
%python% console_6809_test_OLD.py
@pause