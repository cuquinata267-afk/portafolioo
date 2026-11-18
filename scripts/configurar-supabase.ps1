$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectRoot '.env.supabase'
$secret = Read-Host 'Contrasena de la BASE DE DATOS de Supabase (no la API key)' -AsSecureString
if ($secret.Length -eq 0) { throw 'La contrasena no puede estar vacia.' }
$pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secret)
try {
    $encodedPassword = [Uri]::EscapeDataString([Runtime.InteropServices.Marshal]::PtrToStringBSTR($pointer))
    $connection = 'postgresql+psycopg://postgres.uqnrcyjebuljqsgbbugm:' + $encodedPassword + '@aws-0-us-east-2.pooler.supabase.com:5432/postgres?sslmode=require'
    $lines = @()
    if (Test-Path -LiteralPath $envPath) {
        $lines = @([IO.File]::ReadAllLines($envPath) | Where-Object { $_ -notmatch '^\s*DATABASE_URL\s*=' })
    }
    $lines += 'DATABASE_URL=' + $connection
    [IO.File]::WriteAllLines($envPath, [string[]]$lines, [Text.UTF8Encoding]::new($false))
    Write-Host 'Conexion guardada en .env.supabase. La contrasena no se ha mostrado.'
    Write-Host 'Todavia falta ejecutar la migracion y comprobar la conexion.'
} finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($pointer)
    $secret.Dispose()
    $encodedPassword = $null
    $connection = $null
    $lines = $null
}
