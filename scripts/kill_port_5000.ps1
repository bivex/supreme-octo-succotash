# Kill processes listening on port 5000
Write-Host "Finding processes on port 5000..."

$processes = netstat -aon | Select-String ":5000" | Select-String "LISTENING" | ForEach-Object {
    $fields = $_.Line -split '\s+'
    $processId = $fields[-1]
    [PSCustomObject]@{PID = $processId}
} | Select-Object -Unique PID

if ($processes) {
    foreach ($process in $processes) {
        Write-Host "Terminating process with PID $($process.PID)"
        taskkill /F /PID $process.PID 2>$null
    }
    Write-Host "Done."
} else {
    Write-Host "No processes found listening on port 5000."
}
