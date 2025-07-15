# Test deployment script for AIFoundry.app 
Write-Host "🚀 Testing AIFoundry.app  Deployment" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Green

# Function to check if URL is accessible
function Test-Url {
    param(
        [string]$Url,
        [string]$Service
    )
    
    Write-Host "Testing $Service`: $Url" -ForegroundColor Yellow
    
    try {
        $response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 30
        if ($response.StatusCode -eq 200) {
            Write-Host "✅ $Service is healthy" -ForegroundColor Green
            return $true
        } else {
            Write-Host "❌ $Service returned status code: $($response.StatusCode)" -ForegroundColor Red
            return $false
        }
    } catch {
        Write-Host "❌ $Service is not responding: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to test API endpoints
function Test-Api {
    param([string]$BaseUrl)
    
    Write-Host "Testing API endpoints..." -ForegroundColor Cyan
    
    # Test health endpoint
    if (Test-Url -Url "$BaseUrl/healthz" -Service "Health Check") {
        Write-Host "✅ Health check passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Health check failed" -ForegroundColor Red
        return $false
    }
    
    # Test templates endpoint
    if (Test-Url -Url "$BaseUrl/api/templates" -Service "Templates API") {
        Write-Host "✅ Templates API accessible" -ForegroundColor Green
    } else {
        Write-Host "❌ Templates API not accessible" -ForegroundColor Red
        return $false
    }
    
    # Test filter options endpoint
    if (Test-Url -Url "$BaseUrl/api/filters" -Service "Filter Options API") {
        Write-Host "✅ Filter Options API accessible" -ForegroundColor Green
    } else {
        Write-Host "❌ Filter Options API not accessible" -ForegroundColor Red
        return $false
    }
    
    return $true
}

# Main testing logic
if ($args.Length -eq 0) {
    Write-Host "Usage: .\test-deployment.ps1 <backend-url> [frontend-url]" -ForegroundColor Red
    Write-Host "Example: .\test-deployment.ps1 https://backend.azurecontainerapps.io https://frontend.azurecontainerapps.io" -ForegroundColor Yellow
    exit 1
}

$BackendUrl = $args[0]
$FrontendUrl = $args[1]

Write-Host "Backend URL: $BackendUrl" -ForegroundColor Cyan
if ($FrontendUrl) {
    Write-Host "Frontend URL: $FrontendUrl" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "🔍 Testing Backend Services..." -ForegroundColor Yellow
Write-Host "-----------------------------"

if (Test-Api -BaseUrl $BackendUrl) {
    Write-Host "✅ Backend tests passed" -ForegroundColor Green
} else {
    Write-Host "❌ Backend tests failed" -ForegroundColor Red
    exit 1
}

if ($FrontendUrl) {
    Write-Host ""
    Write-Host "🔍 Testing Frontend..." -ForegroundColor Yellow
    Write-Host "--------------------"
    
    if (Test-Url -Url $FrontendUrl -Service "Frontend") {
        Write-Host "✅ Frontend tests passed" -ForegroundColor Green
    } else {
        Write-Host "❌ Frontend tests failed" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "🎉 All tests passed! Your AIFoundry.app  is ready to use." -ForegroundColor Green
Write-Host ""
Write-Host "📋 Next steps:" -ForegroundColor Cyan
Write-Host "1. Open your frontend URL in a browser"
Write-Host "2. Navigate through the templates"
Write-Host "3. Test the customization workflow"
Write-Host "4. Monitor logs for any issues" 