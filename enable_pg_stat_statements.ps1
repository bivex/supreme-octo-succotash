# Enable pg_stat_statements in PostgreSQL configuration
# Requires administrator privileges

$configFile = "C:\Program Files\PostgreSQL\18\data\postgresql.conf"
$backupFile = "C:\Program Files\PostgreSQL\18\data\postgresql.conf.backup"

Write-Host "🔧 Enabling pg_stat_statements in PostgreSQL configuration"
Write-Host "=" * 60

# Check if running as administrator
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
$isAdmin = $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "❌ This script requires administrator privileges."
    Write-Host "Please run PowerShell as Administrator and try again."
    exit 1
}

# Create backup
Write-Host "📋 Creating backup of postgresql.conf..."
Copy-Item $configFile $backupFile -Force
Write-Host "✅ Backup created: $backupFile"

# Read current content
$content = Get-Content $configFile -Raw

# Update shared_preload_libraries
if ($content -match "#shared_preload_libraries = 'pg_stat_statements,auto_explain'") {
    $newContent = $content -replace "#shared_preload_libraries = 'pg_stat_statements,auto_explain'", "shared_preload_libraries = 'pg_stat_statements'"
    Write-Host "✅ Uncommented and updated shared_preload_libraries"
} elseif ($content -match "shared_preload_libraries") {
    Write-Host "⚠️  shared_preload_libraries is already configured"
} else {
    # Add the setting if it doesn't exist
    $newContent = $content + "`n# Added by enable_pg_stat_statements.ps1`nshared_preload_libraries = 'pg_stat_statements'`n"
    Write-Host "✅ Added shared_preload_libraries setting"
}

# Save changes
$newContent | Set-Content $configFile -Encoding UTF8
Write-Host "✅ Configuration updated"

Write-Host "`n🚨 IMPORTANT: PostgreSQL service needs to be restarted for changes to take effect!"
Write-Host "`nTo restart PostgreSQL service:"
Write-Host "1. Open Services (services.msc)"
Write-Host "2. Find 'postgresql-x64-18' service"
Write-Host "3. Right-click → Restart"
Write-Host "`nOr from command line (as Administrator):"
Write-Host "net stop postgresql-x64-18"
Write-Host "net start postgresql-x64-18"

Write-Host "`nAfter restart, pg_stat_statements will be fully functional."
