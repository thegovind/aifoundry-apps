#!/bin/bash

# Test deployment script for SE Agent Factory
echo "🚀 Testing SE Agent Factory Deployment"
echo "======================================"

# Function to check if URL is accessible
check_url() {
    local url=$1
    local service=$2
    
    echo "Testing $service: $url"
    
    if curl -s -o /dev/null -w "%{http_code}" "$url" | grep -q "200"; then
        echo "✅ $service is healthy"
        return 0
    else
        echo "❌ $service is not responding"
        return 1
    fi
}

# Function to test API endpoints
test_api() {
    local base_url=$1
    echo "Testing API endpoints..."
    
    # Test health endpoint
    if check_url "$base_url/healthz" "Health Check"; then
        echo "✅ Health check passed"
    else
        echo "❌ Health check failed"
        return 1
    fi
    
    # Test templates endpoint
    if check_url "$base_url/api/templates" "Templates API"; then
        echo "✅ Templates API accessible"
    else
        echo "❌ Templates API not accessible"
        return 1
    fi
    
    # Test filter options endpoint
    if check_url "$base_url/api/filters" "Filter Options API"; then
        echo "✅ Filter Options API accessible"
    else
        echo "❌ Filter Options API not accessible"
        return 1
    fi
    
    return 0
}

# Main testing logic
if [ "$#" -eq 0 ]; then
    echo "Usage: $0 <backend-url> [frontend-url]"
    echo "Example: $0 https://backend.azurecontainerapps.io https://frontend.azurecontainerapps.io"
    exit 1
fi

BACKEND_URL=$1
FRONTEND_URL=$2

echo "Backend URL: $BACKEND_URL"
if [ -n "$FRONTEND_URL" ]; then
    echo "Frontend URL: $FRONTEND_URL"
fi

echo ""
echo "🔍 Testing Backend Services..."
echo "-----------------------------"

if test_api "$BACKEND_URL"; then
    echo "✅ Backend tests passed"
else
    echo "❌ Backend tests failed"
    exit 1
fi

if [ -n "$FRONTEND_URL" ]; then
    echo ""
    echo "🔍 Testing Frontend..."
    echo "--------------------"
    
    if check_url "$FRONTEND_URL" "Frontend"; then
        echo "✅ Frontend tests passed"
    else
        echo "❌ Frontend tests failed"
        exit 1
    fi
fi

echo ""
echo "🎉 All tests passed! Your SE Agent Factory is ready to use."
echo ""
echo "📋 Next steps:"
echo "1. Open your frontend URL in a browser"
echo "2. Navigate through the templates"
echo "3. Test the customization workflow"
echo "4. Monitor logs for any issues" 