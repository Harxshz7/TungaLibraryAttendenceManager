; ============================================================
;  Inno Setup Script — TungaLibrary Attendance Manager
;  Tested with Inno Setup 6.x  (https://jrsoftware.org/isinfo.php)
;
;  HOW TO BUILD:
;    1. Run PyInstaller first:   pyinstaller TungaLibrary.spec
;    2. Open this file in Inno Setup Compiler and click Build
;    3. Installer lands in:      installer\Output\TungaLibrarySetup.exe
;
;  INSTALL TARGET:
;    No admin rights needed — installs to %LocalAppData%
;    so it works on locked-down college PCs.
; ============================================================

#define AppName        "TungaLibrary Attendance Manager"
#define AppVersion     "1.0.0"
#define AppPublisher   "Tunga Mahavidyalaya"
#define AppExeName     "TungaLibrary.exe"
#define AppId          "{{A3F2C1D4-5E6B-7F8A-9B0C-1D2E3F4A5B6C}"
; ^^^ Change this GUID if you ever release a new major version

; Path to PyInstaller output — relative to this .iss file (../dist/TungaLibrary)
#define DistDir        "..\dist\TungaLibrary"

[Setup]
AppId={#AppId}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisher={#AppPublisher}
AppPublisherURL=
DefaultDirName={localappdata}\{#AppName}
DefaultGroupName={#AppName}
AllowNoIcons=yes
; No admin required — per-user install
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=Output
OutputBaseFilename=TungaLibrarySetup
SetupIconFile=..\assets\logo.ico
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
; Minimum Windows version: Windows 10
MinVersion=10.0.10240
DisableDirPage=no
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExeName}
UninstallDisplayName={#AppName}

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";  Description: "Create a &desktop shortcut";  GroupDescription: "Additional icons:"; Flags: checked
Name: "startmenuicon"; Description: "Create a &Start Menu shortcut"; GroupDescription: "Additional icons:"; Flags: checked

; ── Files ──────────────────────────────────────────────────────────────────

[Files]
; The entire PyInstaller output folder (exe + all Qt DLLs + bundled assets)
Source: "{#DistDir}\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

; Student photos — kept alongside the exe so the app can find them
Source: "..\photos\*"; DestDir: "{app}\photos"; Flags: ignoreversion recursesubdirs createallsubdirs

; Database — copy the initial (possibly seeded) DB; never overwrite on upgrade
Source: "..\data\attendance.db"; DestDir: "{app}\data"; Flags: ignoreversion onlyifdoesntexist

; ── Shortcuts ──────────────────────────────────────────────────────────────

[Icons]
; Desktop shortcut
Name: "{userdesktop}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\logo.ico"; Tasks: desktopicon

; Start Menu shortcut
Name: "{userprograms}\{#AppName}\{#AppName}"; Filename: "{app}\{#AppExeName}"; IconFilename: "{app}\assets\logo.ico"; Tasks: startmenuicon

; Uninstall entry in Start Menu
Name: "{userprograms}\{#AppName}\Uninstall {#AppName}"; Filename: "{uninstallexe}"; Tasks: startmenuicon

; ── Run after install ──────────────────────────────────────────────────────

[Run]
Filename: "{app}\{#AppExeName}"; Description: "Launch {#AppName} now"; Flags: nowait postinstall skipifsilent

; ── Uninstall ──────────────────────────────────────────────────────────────

[UninstallDelete]
; Remove auto-created report folders on uninstall (leave data/ so DB is preserved)
Type: filesandordirs; Name: "{app}\reports"

; ── Code section — create writable dirs if missing ─────────────────────────

[Dirs]
; Ensure reports and photos dirs exist on fresh install
Name: "{app}\reports\daily"
Name: "{app}\reports\monthly"
Name: "{app}\reports\student"
Name: "{app}\photos"
Name: "{app}\data"
