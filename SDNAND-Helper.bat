@echo off
if exist output (
	echo ERROR: Output folder already exists
	echo Press any key to exit
	pause > NUL
	exit
)
if not exist lib (
	md lib
	cd lib
	C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe -command "& { (New-Object Net.WebClient).DownloadFile('https://eternallybored.org/misc/wget/1.19.4/32/wget.exe', 'wget.exe') }"
	wget https://github.com/ihaveamac/fuse-3ds/releases/download/v1.2b4/fuse-3ds-1.2b4-win32.zip
	wget http://emiyl.com/assets/files/selectfile.vbs
	wget http://emiyl.com/assets/files/OSFMount.com
	wget https://github.com/develar/7zip-bin/raw/master/win/ia32/7za.exe
	del wget.exe
	7za.exe e fuse-3ds-1.2b4-win32.zip
	del 7za.exe
	del fuse-3ds-1.2b4-win32.zip
	cd ..\
)
cd lib
echo Selecting nand.bin image...
C:\Windows\System32\cscript.exe selectfile.vbs > NUL
for /f "delims=" %%x in (file) do set path=%%x
del file
IF %path%=="" exit
IF NOT [%path:~-4%]==[.bin] (
	echo ERROR: File must be a .bin file
	echo Press any key to exit
	pause > NUL
	exit
)
set bytesize=251658304
FOR /F "usebackq" %%A IN ('%path%') DO set size=%%~zA
if %size% LSS %bytesize% (
	echo ERROR: NAND is too small ^(expected 251658304 bytes^)
	echo Press any key to exit
	pause > NUL
	exit
)
if %size% GTR %bytesize% (
	echo ERROR: NAND is too large ^(expected 251658304 bytes^)
	echo Press any key to exit
	pause > NUL
	exit
)
echo Decrypting DSi NAND...
start /b fuse-3ds nanddsi %path% NAND > NUL
C:\Windows\System32\ping.exe 127.0.0.1 -n 4 > NUL
echo Mounting DSi NAND...
for %%a in (z y x w v u t s r q p o n m l k j i h g f e d c) do CD %%a: 1>> nul 2>&1 & if errorlevel 1 set freedrive=%%a:
osfmount -a -t file -f NAND\twl_main.img -m %freedrive%
echo Copying contents...
md ..\output
C:\Windows\System32\xcopy /s %freedrive%\*.* ..\output
IF NOT EXIST ..\output\import md ..\output\import
IF NOT EXIST ..\output\progress md ..\output\progress
echo Unmounting DSi NAND...
osfmount -d -m %freedrive%
echo Press Ctrl+Pause/Break to exit
