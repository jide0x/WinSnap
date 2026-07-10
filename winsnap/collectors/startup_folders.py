from winsnap.collectors.powershell import run_powershell_json


STARTUP_FOLDER_COLLECTION_TIMEOUT_SECONDS = 30


def collect_startup_folders():
    return run_powershell_json(
        "$folders = @(" \
        "@{Scope='User';Path=[Environment]::ExpandEnvironmentVariables('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup')}," \
        "@{Scope='Machine';Path=[Environment]::ExpandEnvironmentVariables('%PROGRAMDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Startup')}" \
        "); " \
        "$shell = New-Object -ComObject WScript.Shell; " \
        "$results = @(); " \
        "foreach ($folder in $folders) { " \
        "if (Test-Path -LiteralPath $folder.Path) { " \
        "Get-ChildItem -LiteralPath $folder.Path -File -Force | Where-Object { $_.Name -ine 'desktop.ini' } | ForEach-Object { " \
        "$targetPath = $null; $arguments = $null; $workingDirectory = $null; " \
        "if ($_.Extension -ieq '.lnk') { " \
        "$shortcut = $shell.CreateShortcut($_.FullName); " \
        "$targetPath = $shortcut.TargetPath; " \
        "$arguments = $shortcut.Arguments; " \
        "$workingDirectory = $shortcut.WorkingDirectory; " \
        "}; " \
        "$results += [pscustomobject]@{Scope=$folder.Scope;FolderPath=$folder.Path;Name=$_.Name;FullName=$_.FullName;Extension=$_.Extension;Length=$_.Length;LastWriteTimeUtc=$_.LastWriteTimeUtc.ToString('o');TargetPath=$targetPath;Arguments=$arguments;WorkingDirectory=$workingDirectory} " \
        "} } }; " \
        "$results | ConvertTo-Json -Depth 4",
        STARTUP_FOLDER_COLLECTION_TIMEOUT_SECONDS,
    )
