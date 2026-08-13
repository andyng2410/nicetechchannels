$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

try {
    [Console]::OutputEncoding = [System.Text.UTF8Encoding]::new()
    $OutputEncoding = [System.Text.UTF8Encoding]::new()
    chcp 65001 *> $null
} catch {}

$RootDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $RootDir

$VenvDir = Join-Path $RootDir ".venv"
$VenvPython = Join-Path $VenvDir "Scripts\python.exe"
$ToolsDir = Join-Path $RootDir ".tools"
$LocalFfmpegBin = Join-Path $ToolsDir "ffmpeg\bin"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Write-Ok {
    param([string]$Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Write-WarnVi {
    param([string]$Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Write-ErrVi {
    param([string]$Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Refresh-Path {
    $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    $env:Path = (($machinePath, $userPath, $env:Path) -join ";")

    $extraPaths = @(
        (Join-Path $VenvDir "Scripts"),
        $LocalFfmpegBin,
        (Join-Path $env:ProgramFiles "nodejs"),
        (Join-Path $env:APPDATA "npm"),
        (Join-Path $env:USERPROFILE "scoop\shims"),
        "C:\ProgramData\scoop\shims",
        "C:\ProgramData\chocolatey\bin",
        "C:\ffmpeg\bin",
        (Join-Path $env:ProgramFiles "ffmpeg\bin"),
        (Join-Path $env:ProgramFiles "Gyan\FFmpeg\bin"),
        (Join-Path $env:ProgramFiles "GyanD\FFmpeg\bin"),
        (Join-Path $env:LOCALAPPDATA "Microsoft\WindowsApps")
    )
    $programFilesX86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    if ($programFilesX86) {
        $extraPaths += (Join-Path $programFilesX86 "nodejs")
        $extraPaths += (Join-Path $programFilesX86 "ffmpeg\bin")
        $extraPaths += (Join-Path $programFilesX86 "Gyan\FFmpeg\bin")
    }
    if ($env:NVM_SYMLINK) { $extraPaths += $env:NVM_SYMLINK }
    if ($env:NVM_HOME) { $extraPaths += $env:NVM_HOME }
    if ($env:VOLTA_HOME) { $extraPaths += (Join-Path $env:VOLTA_HOME "bin") }

    foreach ($pathItem in $extraPaths) {
        if ($pathItem -and (Test-Path -LiteralPath $pathItem) -and ($env:Path -notlike "*$pathItem*")) {
            $env:Path = "$pathItem;$env:Path"
        }
    }
}

function Test-CommandExists {
    param([string]$Name)
    return $null -ne (Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-Native {
    param(
        [Parameter(Mandatory = $true)][string]$File,
        [string[]]$CommandArgs = @(),
        [switch]$AllowFail
    )

    $code = 1
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $File @CommandArgs 2>&1 | ForEach-Object {
            if ($_ -is [System.Management.Automation.ErrorRecord]) {
                Write-Host $_.Exception.Message
            } else {
                Write-Host $_
            }
        }
        $code = $LASTEXITCODE
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
    if (($code -ne 0) -and (-not $AllowFail)) {
        throw "Lệnh thất bại (exit code $code): $File $($CommandArgs -join ' ')"
    }
    return $code
}

function Install-WingetPackage {
    param(
        [Parameter(Mandatory = $true)][string]$PackageId,
        [Parameter(Mandatory = $true)][string]$DisplayName
    )

    if (-not (Test-CommandExists "winget")) {
        throw "Không tìm thấy winget. Hãy cài '$DisplayName' thủ công rồi chạy lại script."
    }

    Write-Step "Đang cài $DisplayName bằng winget..."
    $code = Invoke-Native -File "winget" -CommandArgs @(
        "install", "--id", $PackageId, "-e",
        "--accept-package-agreements", "--accept-source-agreements"
    ) -AllowFail

    if ($code -ne 0) {
        throw "Không cài được $DisplayName bằng winget. Hãy cài thủ công rồi chạy lại script."
    }
    Refresh-Path
}

function Test-PythonCandidate {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [string[]]$Args = @()
    )

    $checkScript = @"
import ensurepip
import sys
if sys.version_info < (3, 11) or sys.version_info >= (3, 15):
    raise SystemExit(1)
"@

    $tempFile = [System.IO.Path]::GetTempFileName() + ".py"
    try {
        Set-Content -LiteralPath $tempFile -Value $checkScript -Encoding UTF8
        $allArgs = @()
        $allArgs += $Args
        $allArgs += $tempFile
        & $Exe @allArgs *> $null
        return $LASTEXITCODE -eq 0
    } catch {
        return $false
    } finally {
        Remove-Item -LiteralPath $tempFile -ErrorAction SilentlyContinue
    }
}

function Find-Python {
    Refresh-Path
    $candidates = @(
        @{ Exe = "py"; Args = @("-3.14") },
        @{ Exe = "py"; Args = @("-3.13") },
        @{ Exe = "py"; Args = @("-3.12") },
        @{ Exe = "py"; Args = @("-3.11") },
        @{ Exe = "python"; Args = @() },
        @{ Exe = "python3"; Args = @() }
    )

    foreach ($candidate in $candidates) {
        $candidateExe = $candidate["Exe"]
        $candidateArgs = [string[]]$candidate["Args"]
        if (-not (Test-CommandExists $candidateExe)) { continue }
        if (Test-PythonCandidate -Exe $candidateExe -Args $candidateArgs) { return $candidate }
    }
    return $null
}

function Ensure-Python {
    $python = Find-Python
    if ($python) { return $python }

    Write-WarnVi "Chưa tìm thấy Python 3.11–3.14 phù hợp. Script sẽ thử cài Python 3.14."
    Install-WingetPackage -PackageId "Python.Python.3.14" -DisplayName "Python 3.14"
    $python = Find-Python
    if (-not $python) {
        throw "Không tìm thấy Python 3.11–3.14 sau khi cài. Hãy cài Python 3.14 từ https://www.python.org/downloads/windows/ rồi chạy lại."
    }
    return $python
}

function Invoke-Python {
    param(
        [Parameter(Mandatory = $true)]$Python,
        [Parameter(Mandatory = $true)][string[]]$CommandArgs
    )

    $allArgs = @()
    $allArgs += $Python["Args"]
    $allArgs += $CommandArgs
    $pythonExe = $Python["Exe"]
    Invoke-Native -File $pythonExe -CommandArgs $allArgs | Out-Null
}

function Test-VenvOk {
    $venvActivate = Join-Path $VenvDir "Scripts\Activate.ps1"
    if (-not (Test-Path -LiteralPath $VenvPython)) { return $false }
    if (-not (Test-Path -LiteralPath $venvActivate)) { return $false }
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & $VenvPython -m pip --version *> $null
        return $LASTEXITCODE -eq 0
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
}

function Invoke-VenvPython {
    param([Parameter(Mandatory = $true)][string[]]$CommandArgs)
    Invoke-Native -File $VenvPython -CommandArgs $CommandArgs | Out-Null
}

function Test-VenvPythonCode {
    param(
        [Parameter(Mandatory = $true)][string]$Code,
        [switch]$ShowOutput
    )

    $tempFile = [System.IO.Path]::GetTempFileName() + ".py"
    try {
        Set-Content -LiteralPath $tempFile -Value $Code -Encoding UTF8
        $oldErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        try {
            $output = & $VenvPython $tempFile 2>&1
            $code = $LASTEXITCODE
        } finally {
            $ErrorActionPreference = $oldErrorActionPreference
        }
        if (($code -ne 0) -and $ShowOutput) {
            $output | ForEach-Object { Write-Host $_ }
        }
        return $code -eq 0
    } finally {
        Remove-Item -LiteralPath $tempFile -ErrorAction SilentlyContinue
    }
}

function Ensure-Venv {
    param([Parameter(Mandatory = $true)]$Python)

    if (-not (Test-VenvOk)) {
        if (Test-Path -LiteralPath $VenvDir) {
            $brokenVenv = Join-Path $RootDir (".venv.broken-" + (Get-Date -Format "yyyyMMdd-HHmmss"))
            Write-WarnVi ".venv hiện tại bị thiếu Scripts\Activate.ps1 hoặc pip, chuyển sang $(Split-Path -Leaf $brokenVenv) và tạo lại."
            Move-Item -LiteralPath $VenvDir -Destination $brokenVenv
        }

        $versionArgs = @()
        $versionArgs += $Python["Args"]
        $versionArgs += "--version"
        $pythonVersion = (& $Python["Exe"] @versionArgs 2>&1 | Select-Object -First 1)
        Write-Step "Tạo virtualenv .venv bằng $pythonVersion"
        Invoke-Python -Python $Python -CommandArgs @("-m", "venv", $VenvDir)
    } else {
        Write-Ok "Đã có virtualenv .venv hợp lệ"
    }

    if (-not (Test-VenvOk)) {
        throw "Tạo .venv thất bại hoặc pip chưa sẵn sàng."
    }
}

function Install-PortableFfmpeg {
    $downloadUrl = "https://media.githubusercontent.com/media/zackees/ffmpeg_bins/df95abcb0ce6efff710dda5ef28a2f6f1dc21493/v8.0/win32.zip"
    $expectedSha256 = "92662c2241e93fe71b3f3a01e94a0b0dc8cfad726019f96b83bc109ce44c5d0b"
    $tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) ("escbase-ffmpeg-" + [Guid]::NewGuid().ToString("N"))
    $archivePath = "$tempRoot.zip"
    $extractDir = "$tempRoot-extracted"

    try {
        Write-Step "Tải FFmpeg portable (~72 MB), vui lòng chờ thanh tiến độ..."
        if (Test-CommandExists "curl.exe") {
            Invoke-Native -File "curl.exe" -CommandArgs @(
                "--fail", "--location", "--retry", "2",
                "--connect-timeout", "20",
                "--output", $archivePath,
                $downloadUrl
            ) | Out-Null
        } else {
            Invoke-WebRequest -Uri $downloadUrl -OutFile $archivePath -UseBasicParsing
        }

        $actualSha256 = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($actualSha256 -ne $expectedSha256) {
            throw "Gói FFmpeg tải về không đúng checksum."
        }

        Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDir -Force

        $ffmpegExe = Get-ChildItem -LiteralPath $extractDir -Filter "ffmpeg.exe" -File -Recurse |
            Select-Object -First 1
        $ffprobeExe = Get-ChildItem -LiteralPath $extractDir -Filter "ffprobe.exe" -File -Recurse |
            Select-Object -First 1
        if (-not $ffmpegExe -or -not $ffprobeExe) {
            throw "Gói FFmpeg tải về không có đủ ffmpeg.exe và ffprobe.exe."
        }

        New-Item -ItemType Directory -Path $LocalFfmpegBin -Force | Out-Null
        Copy-Item -LiteralPath $ffmpegExe.FullName -Destination (Join-Path $LocalFfmpegBin "ffmpeg.exe") -Force
        Copy-Item -LiteralPath $ffprobeExe.FullName -Destination (Join-Path $LocalFfmpegBin "ffprobe.exe") -Force
    } finally {
        Remove-Item -LiteralPath $archivePath -Force -ErrorAction SilentlyContinue
        Remove-Item -LiteralPath $extractDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}

function Ensure-Ffmpeg {
    Refresh-Path
    if ((Test-CommandExists "ffmpeg") -and (Test-CommandExists "ffprobe")) {
        Write-Ok "Đã có ffmpeg và ffprobe"
        return
    }

    Write-WarnVi "Chưa có ffmpeg/ffprobe. Script sẽ thử cài FFmpeg."
    try {
        Install-WingetPackage -PackageId "Gyan.FFmpeg" -DisplayName "FFmpeg"
    } catch {
        Write-WarnVi "winget chưa cài được FFmpeg. Chuyển sang tải bản portable vào project."
        Write-Host $_.Exception.Message -ForegroundColor Yellow
    }
    Refresh-Path

    if ((Test-CommandExists "ffmpeg") -and (Test-CommandExists "ffprobe")) {
        Write-Ok "Đã cài FFmpeg"
        return
    }

    Install-PortableFfmpeg
    Refresh-Path

    if ((Test-CommandExists "ffmpeg") -and (Test-CommandExists "ffprobe")) {
        Write-Ok "Đã cài FFmpeg portable trong .tools\ffmpeg\bin"
        return
    }

    throw "Đã thử cài FFmpeg bằng winget và bản portable nhưng vẫn chưa thấy ffmpeg/ffprobe."
}

function Ensure-YtDlp {
    Refresh-Path
    if (Test-CommandExists "yt-dlp") {
        Write-Ok "Đã có yt-dlp"
        return
    }

    Write-Step "Cài yt-dlp để tải video X/Twitter, YouTube"
    try {
        Install-WingetPackage -PackageId "yt-dlp.yt-dlp" -DisplayName "yt-dlp"
    } catch {
        Write-WarnVi "winget chưa cài được yt-dlp. Chuyển sang cài bằng pip trong .venv."
        Write-Host $_.Exception.Message -ForegroundColor Yellow
    }
    Refresh-Path

    if (Test-CommandExists "yt-dlp") {
        Write-Ok "Đã cài yt-dlp"
        return
    }

    Write-Step "Cài yt-dlp bằng pip trong .venv"
    Invoke-VenvPython -CommandArgs @("-m", "pip", "install", "--upgrade", "yt-dlp")
    Refresh-Path

    if (Test-CommandExists "yt-dlp") {
        Write-Ok "Đã cài yt-dlp trong .venv"
        return
    }

    throw "Đã thử cài yt-dlp bằng winget và pip nhưng vẫn chưa thấy lệnh tại .venv\Scripts\yt-dlp.exe."
}

function Test-Node20OrNewer {
    if (-not (Test-CommandExists "node")) { return $false }
    $oldErrorActionPreference = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try {
        & node -e "process.exit(Number(process.versions.node.split('.')[0]) >= 20 ? 0 : 1)" *> $null
        return $LASTEXITCODE -eq 0
    } finally {
        $ErrorActionPreference = $oldErrorActionPreference
    }
}

function Ensure-NodeForBird {
    Refresh-Path
    if ((Test-CommandExists "npm") -and (Test-Node20OrNewer)) {
        $nodeVersion = (& node --version 2>$null | Select-Object -First 1)
        $npmVersion = (& npm --version 2>$null | Select-Object -First 1)
        Write-Ok "Đã thấy Node $nodeVersion và npm $npmVersion"
        return $true
    }

    Write-Step "Cài Node.js LTS để cài bird"
    try {
        Install-WingetPackage -PackageId "OpenJS.NodeJS.LTS" -DisplayName "Node.js LTS"
    } catch {
        Write-WarnVi "Chưa cài được Node.js bằng winget. Sẽ bỏ qua bird để setup chính không bị dừng."
        Write-Host $_.Exception.Message -ForegroundColor Yellow
        return $false
    }
    Refresh-Path

    if ((Test-CommandExists "npm") -and (Test-Node20OrNewer)) {
        $nodeVersion = (& node --version 2>$null | Select-Object -First 1)
        $npmVersion = (& npm --version 2>$null | Select-Object -First 1)
        Write-Ok "Đã thấy Node $nodeVersion và npm $npmVersion"
        return $true
    }

    Write-WarnVi "bird cần Node.js >= 20 và npm. Hãy cài Node.js LTS từ https://nodejs.org/ rồi chạy lại script nếu cần bird."
    return $false
}

function Read-SecretValue {
    param([Parameter(Mandatory = $true)][string]$Prompt)

    $secure = Read-Host -Prompt $Prompt -AsSecureString
    $ptr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
    try {
        return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($ptr)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($ptr)
    }
}

function Test-BirdAuth {
    return (-not [string]::IsNullOrWhiteSpace($env:AUTH_TOKEN)) -and (-not [string]::IsNullOrWhiteSpace($env:CT0))
}

function Set-UserEnvValue {
    param(
        [Parameter(Mandatory = $true)][string]$Name,
        [Parameter(Mandatory = $true)][string]$Value
    )

    [Environment]::SetEnvironmentVariable($Name, $Value, "User")
    Set-Item -Path ("Env:{0}" -f $Name) -Value $Value
}

function Configure-BirdAuth {
    if (Test-BirdAuth) {
        Write-Ok "Đã có AUTH_TOKEN và CT0 trong môi trường"
        return
    }

    Write-Host ""
    Write-WarnVi "bird dùng cookie đăng nhập X/Twitter."
    Write-Host "Ai có auth_token và ct0 có thể dùng phiên đăng nhập của bạn."
    Write-Host "Nên dùng tài khoản phụ, không dán token vào chat/log công khai, và có thể logout X để thu hồi phiên."
    Write-Host ""
    Write-Host "Cách lấy:"
    Write-Host "  1. Đăng nhập x.com trong trình duyệt."
    Write-Host "  2. Mở DevTools: F12 hoặc Ctrl + Shift + I."
    Write-Host "  3. Vào Application -> Cookies -> https://x.com."
    Write-Host "  4. Copy giá trị auth_token và ct0."
    Write-Host ""
    Write-Host "Khi dán token vào PowerShell, ký tự sẽ không hiện lên màn hình; dán xong cứ bấm Enter."
    Write-Host ""

    $authToken = Read-SecretValue -Prompt "Dán auth_token"
    $ct0 = Read-SecretValue -Prompt "Dán ct0"

    if ([string]::IsNullOrWhiteSpace($authToken) -or [string]::IsNullOrWhiteSpace($ct0)) {
        Write-WarnVi "Thiếu auth_token hoặc ct0, bỏ qua cấu hình bird."
        return
    }

    Set-UserEnvValue -Name "AUTH_TOKEN" -Value $authToken
    Set-UserEnvValue -Name "CT0" -Value $ct0
    Write-Ok "Đã lưu AUTH_TOKEN và CT0 vào User environment variables"
}

function Ensure-BirdOptional {
    Write-Host ""
    $answer = Read-Host "Bạn có muốn làm nội dung với link X/Twitter không? Cài bird để đọc thread? [y/N]"
    if ($answer -notin @("y", "Y", "yes", "YES")) {
        Write-Host "Bỏ qua bird. Khi cần làm bài từ X/Twitter, chạy lại setup và chọn y." -ForegroundColor Yellow
        return
    }

    Refresh-Path
    if (-not (Test-CommandExists "bird")) {
        if (-not (Ensure-NodeForBird)) {
            Write-WarnVi "Bỏ qua bird. Web UI và render vẫn tiếp tục cài bình thường."
            return
        }
        Write-Step "Cài bird để extract thread X/Twitter"
        $code = Invoke-Native -File "npm" -CommandArgs @("install", "-g", "@steipete/bird") -AllowFail
        if ($code -ne 0) {
            Write-WarnVi "npm chưa cài được bird. Bỏ qua bird để setup chính không bị dừng."
            return
        }
        Refresh-Path
    }

    if (-not (Test-CommandExists "bird")) {
        Write-WarnVi "Đã thử cài bird nhưng PowerShell hiện tại chưa thấy lệnh. Bỏ qua bird, khi cần X/Twitter hãy mở PowerShell mới rồi chạy: bird --version"
        return
    }

    Write-Ok "Đã có bird"
    Configure-BirdAuth
    if (Test-BirdAuth) {
        Invoke-Native -File "bird" -CommandArgs @("whoami") -AllowFail | Out-Null
    }
}

function Ensure-MediaTools {
    Write-Step "Kiểm tra media tools cho workflow X/Twitter và video"
    Ensure-YtDlp
    Ensure-Ffmpeg
    Ensure-BirdOptional
}

function Ensure-VCRuntime {
    $check = @"
import ctypes
ctypes.CDLL("vcruntime140.dll")
ctypes.CDLL("vcruntime140_1.dll")
print("OK")
"@
    if (Test-VenvPythonCode -Code $check) {
        Write-Ok "Đã có Microsoft Visual C++ Runtime"
        return
    }

    Write-WarnVi "Thiếu Microsoft Visual C++ Runtime. Script sẽ thử cài bằng winget."
    Install-WingetPackage -PackageId "Microsoft.VCRedist.2015+.x64" -DisplayName "Microsoft Visual C++ Redistributable 2015-2022 x64"

    if (Test-VenvPythonCode -Code $check) {
        Write-Ok "Đã có Microsoft Visual C++ Runtime"
        return
    }

    Write-WarnVi "Visual C++ Runtime vừa cài nhưng Python hiện tại vẫn chưa load được DLL. Có thể cần reboot Windows."
}

function Ensure-PythonDependencies {
    Write-Step "Cài Python dependencies"
    Invoke-VenvPython -CommandArgs @("-m", "pip", "install", "--upgrade", "pip")
    Invoke-VenvPython -CommandArgs @("-m", "pip", "install", "-r", "requirements.txt")
}

function Ensure-PlaywrightImport {
    $check = @"
import greenlet
import playwright.async_api
print('OK')
"@
    if (Test-VenvPythonCode -Code $check) {
        Write-Ok "Playwright và greenlet import OK"
        return
    }

    Write-WarnVi "Playwright/greenlet chưa import được. Trên Windows thường do thiếu Microsoft Visual C++ Redistributable."
    Install-WingetPackage -PackageId "Microsoft.VCRedist.2015+.x64" -DisplayName "Microsoft Visual C++ Redistributable 2015-2022 x64"

    Write-Step "Cài lại greenlet và playwright sau khi cài Visual C++ Runtime"
    Invoke-VenvPython -CommandArgs @("-m", "pip", "install", "--force-reinstall", "--no-cache-dir", "greenlet", "playwright")

    if (-not (Test-VenvPythonCode -Code $check -ShowOutput)) {
        throw "Playwright vẫn chưa import được. Hãy reboot Windows, rồi chạy lại script. Nếu vẫn lỗi, gửi log đoạn import greenlet/playwright."
    }
    Write-Ok "Playwright và greenlet import OK"
}

function Find-SystemChromium {
    $programFiles = $env:ProgramFiles
    $programFilesX86 = [Environment]::GetEnvironmentVariable("ProgramFiles(x86)")
    $localAppData = $env:LOCALAPPDATA
    $paths = @()
    if ($programFiles) {
        $paths += (Join-Path $programFiles "Microsoft\Edge\Application\msedge.exe")
        $paths += (Join-Path $programFiles "Google\Chrome\Application\chrome.exe")
    }
    if ($programFilesX86) {
        $paths += (Join-Path $programFilesX86 "Microsoft\Edge\Application\msedge.exe")
        $paths += (Join-Path $programFilesX86 "Google\Chrome\Application\chrome.exe")
    }
    if ($localAppData) {
        $paths += (Join-Path $localAppData "Microsoft\Edge\Application\msedge.exe")
        $paths += (Join-Path $localAppData "Google\Chrome\Application\chrome.exe")
    }

    foreach ($browserPath in $paths) {
        if ($browserPath -and (Test-Path -LiteralPath $browserPath)) { return $browserPath }
    }
    return $null
}

function Ensure-Browser {
    $browser = Find-SystemChromium
    if ($browser) {
        Write-Ok "Đã có browser hệ thống để render: $browser"
        return
    }

    Write-WarnVi "Chưa thấy Microsoft Edge/Google Chrome. Script sẽ thử cài Microsoft Edge để render."
    Install-WingetPackage -PackageId "Microsoft.Edge" -DisplayName "Microsoft Edge"
    $browser = Find-SystemChromium
    if ($browser) {
        Write-Ok "Đã có browser hệ thống để render: $browser"
        return
    }

    Write-WarnVi "Không thấy Edge/Chrome. Thử tải Chromium của Playwright. Nếu mạng yếu, bước này có thể fail."
    $code = Invoke-Native -File $VenvPython -CommandArgs @("-m", "playwright", "install", "chromium") -AllowFail
    if ($code -ne 0) {
        throw "Không cài được browser render. Hãy cài Microsoft Edge hoặc Google Chrome, hoặc chạy lại script khi mạng ổn hơn."
    }
}

function Test-PlaywrightRuntime {
    $browser = Find-SystemChromium
    if ($browser) {
        $env:ESCBASE_BROWSER_PATH = $browser
    } else {
        Remove-Item Env:ESCBASE_BROWSER_PATH -ErrorAction SilentlyContinue
    }

    $smoke = @"
import asyncio
import os
import tempfile

from playwright.async_api import async_playwright

async def main():
    browser_path = os.environ.get("ESCBASE_BROWSER_PATH")
    launch_options = {
        "headless": True,
        "args": ["--allow-file-access-from-files", "--autoplay-policy=no-user-gesture-required"],
    }
    if browser_path:
        launch_options["executable_path"] = browser_path
    async with async_playwright() as p:
        browser = await p.chromium.launch(**launch_options)
        context = await browser.new_context(
            viewport={"width": 320, "height": 180},
            record_video_dir=tempfile.mkdtemp(prefix="escbase-playwright-"),
            record_video_size={"width": 320, "height": 180},
        )
        page = await context.new_page()
        await page.goto("data:text/html,<html><body>escbase ok</body></html>")
        await context.close()
        await browser.close()

asyncio.run(main())
"@

    return Test-VenvPythonCode -Code $smoke
}

function Ensure-PlaywrightRuntime {
    if (Test-PlaywrightRuntime) {
        Write-Ok "Playwright launch browser/record video OK"
        return
    }

    Write-WarnVi "Playwright import được nhưng chưa launch/record video được. Thử cài thêm Playwright FFmpeg."
    Invoke-Native -File $VenvPython -CommandArgs @("-m", "playwright", "install", "ffmpeg") -AllowFail | Out-Null

    if (Test-PlaywrightRuntime) {
        Write-Ok "Playwright launch browser/record video OK"
        return
    }

    Write-WarnVi "Vẫn chưa launch được. Nếu mạng ổn, thử tải Chromium của Playwright."
    Invoke-Native -File $VenvPython -CommandArgs @("-m", "playwright", "install", "chromium") -AllowFail | Out-Null

    if (Test-PlaywrightRuntime) {
        Write-Ok "Playwright launch browser/record video OK"
        return
    }

    throw "Playwright chưa launch/record video được. Hãy cài Microsoft Edge hoặc Google Chrome, reboot Windows nếu vừa cài Visual C++ Runtime, rồi chạy lại script."
}

try {
    Write-Host ""
    Write-Host "Cài đặt môi trường và chạy Web UI" -ForegroundColor Cyan
    Write-Host "Repo: $RootDir"
    Write-Host ""

    $python = Ensure-Python
    Ensure-Venv -Python $python
    Ensure-MediaTools
    Ensure-VCRuntime
    Ensure-PythonDependencies
    Ensure-PlaywrightImport
    Ensure-Browser
    Ensure-PlaywrightRuntime

    Write-Host ""
    Write-Ok "Môi trường đã sẵn sàng"
    Write-Host "Mở Web UI tại: http://localhost:8765" -ForegroundColor Cyan
    Write-Host "Lần sau chỉ cần chạy: .\run.cmd" -ForegroundColor Cyan
    Write-Host ""
    Invoke-VenvPython -CommandArgs (@("web_server.py") + $args)
} catch {
    Write-Host ""
    Write-ErrVi "Setup thất bại."
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Gợi ý kiểm tra nhanh:" -ForegroundColor Yellow
    Write-Host "  where python"
    Write-Host "  where yt-dlp"
    Write-Host "  where ffmpeg"
    Write-Host "  where ffprobe"
    Write-Host "  where bird"
    Write-Host "  node --version"
    Write-Host "  npm --version"
    Write-Host '  .\.venv\Scripts\python.exe -c "import greenlet; import playwright.async_api; print(''OK'')"'
    exit 1
}
