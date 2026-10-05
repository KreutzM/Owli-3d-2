# Codex CLI with DeepSeek V4.1 Flash via OpenRouter

This repository pins the OpenRouter model `deepseek/deepseek-v4.1-flash` in
`.codex/config.toml`.

Codex currently requires custom provider definitions such as
`model_providers.openrouter` in the **user-level** Codex configuration. A
project-local `.codex/config.toml` cannot reliably define or select that
provider, so the provider setup below is intentionally kept separate from the
repository configuration.

No API key belongs in this repository.

## 1. Configure OpenRouter once on Windows

Merge the contents of
`.codex/openrouter.user.windows.example.toml` into:

```text
%USERPROFILE%\.codex\config.toml
```

The required block is:

```toml
[model_providers.openrouter]
name = "OpenRouter"
base_url = "https://openrouter.ai/api/v1"
wire_api = "responses"

[model_providers.openrouter.auth]
command = "powershell"
args = ["-NoProfile", "-Command", "Write-Output $env:OPENROUTER_API_KEY"]
```

The command-based auth form is preferred over a plain `env_key` because Codex
can then refresh OpenRouter's model catalog and use the model's actual metadata.

Do not add a top-level `model_provider = "openrouter"` unless you want
OpenRouter to become the default provider for every Codex project on this
machine. The repository launcher selects it only for Owli sessions.

## 2. Set the OpenRouter key outside Git

For the current PowerShell session:

```powershell
$env:OPENROUTER_API_KEY = "sk-or-v1-..."
```

To store it as a Windows user environment variable:

```powershell
[Environment]::SetEnvironmentVariable(
    "OPENROUTER_API_KEY",
    "sk-or-v1-...",
    "User"
)
```

Open a new terminal after setting the persistent variable.

Never paste the real key into `.codex/config.toml`, scripts, documentation,
issues, commits, or review artifacts.

## 3. Start Codex for Owli

From the repository root:

```powershell
.\scripts\codex_openrouter.ps1
```

The launcher verifies that `codex` and `OPENROUTER_API_KEY` are available
and starts Codex with:

- provider: `openrouter`
- model: `deepseek/deepseek-v4.1-flash`
- reasoning effort: `medium`

The project still uses the repository's normal `AGENTS.md` instructions and
required reading order.

On first use, allow/trust this repository when Codex asks. Project-local Codex
settings are ignored for untrusted projects.

## 4. Override settings for one run

Arguments are forwarded to Codex after the repository defaults, so a later
override can be supplied explicitly. For example:

```powershell
.\scripts\codex_openrouter.ps1 -c 'model_reasoning_effort="high"'
```

Use high reasoning for difficult topology, rigging, or evidence-chain work and
medium for normal implementation/review iterations.

## 5. Verify routing

Inside Codex, inspect the selected model (for example with the model picker) and
confirm that the model is:

```text
deepseek/deepseek-v4.1-flash
```

Then send a small test request and verify the request in the OpenRouter activity
dashboard. If Codex reports `model_not_found`, first check the exact model slug
and that the user-level OpenRouter provider block is present.

If Codex reports an unknown-model/fallback-metadata warning, check that the
provider uses the command-based `auth` block above rather than only
`env_key = "OPENROUTER_API_KEY"`.

## macOS/Linux variant

Use the same provider block but replace the auth command with:

```toml
[model_providers.openrouter.auth]
command = "sh"
args = ["-c", "echo $OPENROUTER_API_KEY"]
```

Then export the key in the shell environment and invoke Codex with the
equivalent provider/model overrides.
