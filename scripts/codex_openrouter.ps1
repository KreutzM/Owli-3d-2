[CmdletBinding()]
param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]] $CodexArgs
)

$ErrorActionPreference = "Stop"

if (-not (Get-Command codex -ErrorAction SilentlyContinue)) {
    throw "Codex CLI was not found on PATH."
}

if ([string]::IsNullOrWhiteSpace($env:OPENROUTER_API_KEY)) {
    throw "OPENROUTER_API_KEY is not set. Set it in the environment; never commit the key."
}

$overrides = @(
    "-c", 'model_provider="openrouter"',
    "-c", 'model="deepseek/deepseek-v4.1-flash"',
    "-c", 'model_reasoning_effort="medium"'
)

& codex @overrides @CodexArgs
exit $LASTEXITCODE
