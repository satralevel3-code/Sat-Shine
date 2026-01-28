#!/bin/bash
# Railway Deployment Script for SAT-SHINE

echo "🚀 Deploying SAT-SHINE to Railway..."

# Check if git is initialized
if [ ! -d ".git" ]; then
    echo "Initializing git repository..."
    git init
    git add .
    git commit -m "Initial commit for Railway deployment"
fi

# Add all changes
echo "Adding changes to git..."
git add .
git commit -m "Update for Railway deployment - $(date)"

# Push to GitHub (assuming origin is set)
echo "Pushing to GitHub..."
git push origin main || git push origin master

echo "✅ Code pushed to GitHub!"
echo ""
echo "📋 Next steps in Railway Dashboard:"
echo "1. Connect your GitHub repository"
echo "2. Add PostgreSQL service"
echo "3. Set environment variables:"
echo "   - SECRET_KEY=your-secret-key"
echo "   - DEBUG=False"
echo "4. Deploy!"
echo ""
echo "🔗 Health check URL: https://your-app.railway.app/health/"
echo "🔗 Login URL: https://your-app.railway.app/login/"