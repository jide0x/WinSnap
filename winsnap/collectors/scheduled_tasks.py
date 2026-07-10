from winsnap.collectors.powershell import run_powershell_json


SCHEDULED_TASK_COLLECTION_TIMEOUT_SECONDS = 30


def collect_scheduled_tasks():
    return run_powershell_json(
        "Get-ScheduledTask | Select-Object TaskName,TaskPath,@{Name='State';Expression={$_.State.ToString()}},Author,@{Name='RunAsUser';Expression={$_.Principal.UserId}},@{Name='Triggers';Expression={@($_.Triggers | ForEach-Object { $_.ToString() })}},@{Name='Actions';Expression={@($_.Actions | ForEach-Object { $action = $_.Execute; if ($_.Arguments) { $action = $action + ' ' + $_.Arguments }; $action })}} | ConvertTo-Json -Depth 5",
        SCHEDULED_TASK_COLLECTION_TIMEOUT_SECONDS,
    )
