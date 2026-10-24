# PowerShell Helper to run skills easily on Windows
param (
    [string]$SkillName = "",
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$Host.UI.RawUI.WindowTitle = "Skills Portal Runner"

if ([string]::IsNullOrWhiteSpace($SkillName)) {
    python run_skill.py list
    Write-Host ""
    $SkillName = Read-Host "Nhập tên skill bạn muốn chạy"
    if ([string]::IsNullOrWhiteSpace($SkillName)) {
        exit
    }
}

python run_skill.py $SkillName $RemainingArgs
