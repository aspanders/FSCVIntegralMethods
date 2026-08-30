<#
.SYNOPSIS
    Pull the latest BeadSnap and build a signed release bundle for Google Play.

.DESCRIPTION
    Does the whole round trip in one command: fetch the branch, build, and tell
    you exactly which file to upload.

    Every step that has actually gone wrong on this machine is handled here
    rather than left to be rediscovered:

      * JAVA_HOME unset. Gradle refuses to start. The script finds Android
        Studio's bundled JDK itself.
      * adb not on PATH. Only needed for -Install, and found the same way.
      * Being in the wrong directory. Paths are resolved from the script's own
        location, so it works from anywhere.
      * Uploading the .apk to Play, which only accepts .aab. Both are built and
        both are named explicitly at the end, with the right one first.
      * Reusing a versionCode. Play burns one on upload, even if you never roll
        it out. The current value is printed before the build, and the script
        refuses to build a versionCode you have already recorded as used.

.PARAMETER Branch
    Branch to build. Defaults to the development branch.

.PARAMETER SkipPull
    Build what is already checked out; do not touch git.

.PARAMETER Install
    Also install the APK on the attached phone when the build succeeds.

.PARAMETER NoClean
    Skip 'clean'. Faster, but only safe when no signature or dependency has
    changed. The default is a clean build for a reason: a stale incremental
    build linking against a changed signature is a genuinely confusing failure.

.EXAMPLE
    .\scripts\build-release.ps1
    .\scripts\build-release.ps1 -Install
    .\scripts\build-release.ps1 -SkipPull -NoClean
#>

[CmdletBinding()]
param(
    [string] $Branch = 'claude/fuse-bead-converter-app-706h2s',
    [switch] $SkipPull,
    [switch] $Install,
    [switch] $NoClean
)

$ErrorActionPreference = 'Stop'

function Say  ($m) { Write-Host "==> $m" -ForegroundColor Cyan }
function Ok   ($m) { Write-Host "    $m" -ForegroundColor Green }
function Warn ($m) { Write-Host "    $m" -ForegroundColor Yellow }
function Die  ($m) { Write-Host "ERROR: $m" -ForegroundColor Red; exit 1 }

# ── Where things are ─────────────────────────────────────────────────────────
$RepoRoot   = Split-Path -Parent $PSScriptRoot
$AndroidDir = Join-Path $RepoRoot 'BeadSnapAndroid'
$GradleFile = Join-Path $AndroidDir 'app\build.gradle.kts'
$UsedFile   = Join-Path $RepoRoot '.uploaded-version-codes'

if (-not (Test-Path $GradleFile)) {
    Die "Not a BeadSnap checkout - no $GradleFile. Run this from the repo's scripts folder."
}

# ── Java ─────────────────────────────────────────────────────────────────────
Say 'Java'
if ($env:JAVA_HOME -and (Test-Path (Join-Path $env:JAVA_HOME 'bin\java.exe'))) {
    Ok "JAVA_HOME already set: $env:JAVA_HOME"
} else {
    $candidates = @(
        'C:\Program Files\Android\Android Studio\jbr',
        'C:\Program Files\Android\Android Studio\jre',
        "$env:LOCALAPPDATA\Programs\Android Studio\jbr",
        "$env:LOCALAPPDATA\Programs\Android Studio\jre",
        'C:\Program Files\Android\Android Studio Preview\jbr'
    )
    $found = $candidates | Where-Object { Test-Path (Join-Path $_ 'bin\java.exe') } | Select-Object -First 1
    if (-not $found) {
        Die ("No JDK found. Android Studio ships one - set JAVA_HOME to it, e.g.`n" +
             '  $env:JAVA_HOME = "C:\Program Files\Android\Android Studio\jbr"')
    }
    $env:JAVA_HOME = $found
    Ok "Using Android Studio's JDK: $found"
}

# ── Signing ──────────────────────────────────────────────────────────────────
Say 'Signing key'
$KeyProps = Join-Path $AndroidDir 'keystore.properties'
if (-not (Test-Path $KeyProps)) {
    Die ("No keystore.properties in $AndroidDir.`n" +
         "    A release build without it is unsigned and Play will reject it.`n" +
         '    Copy keystore.properties.template and fill in your real values.')
}
Ok 'keystore.properties present (never committed, never printed)'

# ── Pull ─────────────────────────────────────────────────────────────────────
Push-Location $RepoRoot
try {
    if ($SkipPull) {
        Warn 'Skipping git (-SkipPull). Building whatever is checked out.'
    } else {
        Say "Pulling $Branch"

        # NB: no 2>&1 anywhere below. git writes ordinary progress to stderr,
        # and redirecting a native command's stderr into the pipeline while
        # $ErrorActionPreference is 'Stop' turns that progress into a
        # terminating NativeCommandError. Let the streams reach the console as
        # they are and judge success by $LASTEXITCODE, which is what it is for.
        $dirty = git status --porcelain
        if ($LASTEXITCODE -ne 0) { Die 'git is not available on PATH.' }
        if ($dirty) {
            Write-Host $dirty
            Die ("You have uncommitted changes. Commit or stash them first, or run " +
                 'with -SkipPull to build them as they are.')
        }

        # Retry: a failed fetch here is almost always transient.
        $pulled = $false
        foreach ($delay in 0, 2, 4, 8) {
            if ($delay -gt 0) { Warn "Retrying in ${delay}s..."; Start-Sleep -Seconds $delay }
            git fetch origin $Branch
            if ($LASTEXITCODE -eq 0) { $pulled = $true; break }
        }
        if (-not $pulled) { Die 'Could not reach GitHub after four attempts.' }

        git checkout $Branch
        if ($LASTEXITCODE -ne 0) { Die "Could not check out $Branch." }
        git merge --ff-only "origin/$Branch"
        if ($LASTEXITCODE -ne 0) {
            Die ("Your local $Branch has diverged from origin and cannot fast-forward.`n" +
                 '    Sort that out by hand - this script will not rewrite your history.')
        }
        Ok "At $(git rev-parse --short HEAD)  $(git log -1 --pretty=%s)"
    }

    # ── Version ──────────────────────────────────────────────────────────────
    Say 'Version'
    $gradleText  = Get-Content $GradleFile -Raw
    $codeMatch   = [regex]::Match($gradleText, 'versionCode\s*=\s*(\d+)')
    $nameMatch   = [regex]::Match($gradleText, 'versionName\s*=\s*"([^"]+)"')
    if (-not $codeMatch.Success) { Die "Could not read versionCode from $GradleFile." }
    $versionCode = [int] $codeMatch.Groups[1].Value
    $versionName = if ($nameMatch.Success) { $nameMatch.Groups[1].Value } else { '?' }
    Ok "versionName $versionName, versionCode $versionCode"

    # Play consumes a versionCode the moment a bundle carrying it is uploaded,
    # to any track, whether or not it is ever rolled out. This has already cost
    # two rebuilds on this project, so the ones you have used are remembered.
    if (Test-Path $UsedFile) {
        $used = Get-Content $UsedFile | Where-Object { $_ -match '^\s*\d+\s*$' } | ForEach-Object { [int] $_.Trim() }
        if (@($used) -contains $versionCode) {
            Die ("versionCode $versionCode is recorded as already uploaded to Play.`n" +
                 "    Play will reject it. Bump the version first:`n" +
                 "        bash scripts/bump-version.sh $versionName`n" +
                 "    (or edit versionCode in app\build.gradle.kts by hand), commit, and re-run.`n" +
                 "    If that record is wrong, remove $versionCode from $UsedFile.")
        }
    }

    # ── Build ────────────────────────────────────────────────────────────────
    Push-Location $AndroidDir
    try {
        $tasks = @()
        if (-not $NoClean) { $tasks += 'clean' }
        $tasks += 'bundleRelease'
        $tasks += 'assembleRelease'

        Say "Building: $($tasks -join ' ')"
        if ($NoClean) {
            Warn 'Incremental build (-NoClean). If a signature changed, this can fail oddly - drop the flag.'
        }

        # $tasks, not @tasks: the @ form is cmdlet splatting and does not
        # mean the same thing for a native command. A plain array variable
        # is expanded into separate arguments, which is what is wanted.
        & .\gradlew.bat $tasks
        if ($LASTEXITCODE -ne 0) {
            Die ("Gradle failed (exit $LASTEXITCODE). The first 'e: ' line above is the real cause;`n" +
                 '    everything after it is usually fallout.')
        }
    } finally {
        Pop-Location
    }

    # ── Results ──────────────────────────────────────────────────────────────
    $aab = Join-Path $AndroidDir 'app\build\outputs\bundle\release\app-release.aab'
    $apk = Join-Path $AndroidDir 'app\build\outputs\apk\release\app-release.apk'

    Say 'Done'
    if (Test-Path $aab) {
        $mb = [math]::Round((Get-Item $aab).Length / 1MB, 1)
        Write-Host ''
        Write-Host '  UPLOAD THIS TO GOOGLE PLAY (.aab - Play rejects .apk):' -ForegroundColor Green
        Write-Host "  $aab" -ForegroundColor White
        Write-Host "  ${mb} MB, versionCode $versionCode, versionName $versionName"
    } else {
        Die "bundleRelease reported success but $aab is missing."
    }

    if (Test-Path $apk) {
        $mb = [math]::Round((Get-Item $apk).Length / 1MB, 1)
        Write-Host ''
        Write-Host '  For testing on your own phone (sideload, NOT for Play):' -ForegroundColor Cyan
        Write-Host "  $apk"
        Write-Host "  ${mb} MB"
    }

    # ── Optional install ─────────────────────────────────────────────────────
    if ($Install) {
        Say 'Installing on the attached device'
        $adb = Get-Command adb -ErrorAction SilentlyContinue
        if (-not $adb) {
            $guess = Join-Path $env:LOCALAPPDATA 'Android\Sdk\platform-tools\adb.exe'
            if (Test-Path $guess) { $adb = $guess } else {
                Warn "adb not found. Install by hand, or add $env:LOCALAPPDATA\Android\Sdk\platform-tools to PATH."
                $adb = $null
            }
        } else {
            $adb = $adb.Source
        }
        if ($adb) {
            $devices = & $adb devices | Select-Object -Skip 1 | Where-Object { $_ -match '\tdevice$' }
            if (-not $devices) {
                Warn 'No device. Enable USB debugging and accept the prompt on the phone.'
            } else {
                & $adb install -r $apk
                if ($LASTEXITCODE -ne 0) {
                    Warn ('Install failed. A signature mismatch with an existing install is the usual ' +
                          'cause - uninstall the old copy first.')
                } else {
                    Ok 'Installed.'
                }
            }
        }
    }

    Write-Host ''
    Write-Host '  After a SUCCESSFUL upload to Play, record the version code so this' -ForegroundColor DarkGray
    Write-Host '  script can stop you reusing it:' -ForegroundColor DarkGray
    Write-Host "      Add-Content '$UsedFile' $versionCode" -ForegroundColor DarkGray
} finally {
    Pop-Location
}
