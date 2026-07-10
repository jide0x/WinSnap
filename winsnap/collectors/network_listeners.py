from winsnap.collectors.powershell import run_powershell_json


NETWORK_LISTENER_COLLECTION_TIMEOUT_SECONDS = 30


def collect_network_listeners():
    return run_powershell_json(
        "$processes = @{}; " \
        "Get-CimInstance Win32_Process | ForEach-Object { $processes[[int]$_.ProcessId] = $_ }; " \
        "$servicesByPid = @{}; " \
        "Get-CimInstance Win32_Service | Where-Object { $_.ProcessId -and $_.ProcessId -ne 0 } | ForEach-Object { " \
        "$pidValue = [int]$_.ProcessId; " \
        "if (-not $servicesByPid.ContainsKey($pidValue)) { $servicesByPid[$pidValue] = @() }; " \
        "$servicesByPid[$pidValue] += $_.Name " \
        "}; " \
        "$results = @(); " \
        "function Add-Listener($protocol, $address, $port, $state, $pidValue) { " \
        "$process = $null; " \
        "$serviceNames = @(); " \
        "$pidInt = if ($null -ne $pidValue) { [int]$pidValue } else { $null }; " \
        "if ($null -ne $pidInt -and $processes.ContainsKey($pidInt)) { $process = $processes[$pidInt] }; " \
        "if ($null -ne $pidInt -and $servicesByPid.ContainsKey($pidInt)) { $serviceNames = @($servicesByPid[$pidInt]) }; " \
        "$script:results += [pscustomobject]@{Protocol=$protocol;LocalAddress=[string]$address;LocalPort=[int]$port;State=$state;OwningProcess=$pidInt;ProcessName=if ($process) { $process.Name } else { $null };ProcessPath=if ($process) { $process.ExecutablePath } else { $null };ServiceNames=$serviceNames} " \
        "}; " \
        "Get-NetTCPConnection -State Listen | ForEach-Object { Add-Listener 'TCP' $_.LocalAddress $_.LocalPort 'Listen' $_.OwningProcess }; " \
        "Get-NetUDPEndpoint | ForEach-Object { Add-Listener 'UDP' $_.LocalAddress $_.LocalPort $null $_.OwningProcess }; " \
        "$results | Sort-Object Protocol,LocalAddress,LocalPort,OwningProcess | ConvertTo-Json -Depth 5",
        NETWORK_LISTENER_COLLECTION_TIMEOUT_SECONDS,
    )
