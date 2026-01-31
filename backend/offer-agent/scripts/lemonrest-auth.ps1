# LemonRest API Authentication and MCP Server Script
param(
    [Parameter(Mandatory=$true)]
    [string]$Username,
    
    [Parameter(Mandatory=$true)]
    [string]$Password,
    
    [Parameter(Mandatory=$true)]
    [string]$Database,
    
    [Parameter(Mandatory=$true)]
    [string]$ApiKey,
    
    [string]$BaseUrl = "https://lvirdsh1.lvi-keskus.local/LemonRest",
    [string]$OpenApiMcpPath = ".\bin\openapi-mcp.exe",
    [string]$OpenApiSpecPath = ".\docs\lemonrest-openapi3.json"
)

Write-Host "Authenticating with LemonRest API..." -ForegroundColor Yellow

# Step 1: Login to get session token
$loginUrl = "$BaseUrl/api/auth/login"
$loginBody = @{
    UserName = $Username
    Password = $Password
    Database = $Database
    ApiKey = $ApiKey
} | ConvertTo-Json

try {
    # Ignore SSL certificate errors for self-signed certificates
    [System.Net.ServicePointManager]::ServerCertificateValidationCallback = {$true}
    
    $loginResponse = Invoke-RestMethod -Uri $loginUrl -Method POST -Body $loginBody -ContentType "application/json"
    
    if ($loginResponse.token) {
        $sessionToken = $loginResponse.token
        Write-Host "✅ Successfully authenticated! Session token obtained." -ForegroundColor Green
        
        # Step 2: Start openapi-mcp with the session token
        Write-Host "Starting MCP server with LemonRest API..." -ForegroundColor Yellow
        
        $env:BEARER_TOKEN = $sessionToken
        $env:OPENAPI_BASE_URL = $BaseUrl
        
        # Start the MCP server
        & $OpenApiMcpPath $OpenApiSpecPath
        
    } else {
        Write-Host "❌ Authentication failed: No token received" -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "❌ Authentication failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} 