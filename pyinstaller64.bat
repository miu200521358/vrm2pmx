@echo off
rem --- 
rem ---  exeを生成
rem --- 

rem ---  カレントディレクトリを実行先に変更
cd /d %~dp0

cls

activate vmdsizing_cython && src\setup_install.bat && pyinstaller --clean motion_supporter64.spec
