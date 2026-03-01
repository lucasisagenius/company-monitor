#!/bin/bash

echo "Deploying Company Monitor to GitHub"
echo "======================================"
echo ""

# Get repo URL
read -p "Enter your GitHub repository URL (https://github.com/USERNAME/company-monitor.git): " REPO_URL

# Initialize if needed
if [ ! -d .git ]; then
    echo "Initializing git repository..."
    git init
fi

# Add remote if not exists
if ! git remote get-url origin &>/dev/null; then
    echo "Adding remote: $REPO_URL"
    git remote add origin "$REPO_URL"
fi

# Configure git
git config --local user.email "action@github.com"
git config --local user.name "GitHub Action"

# Stage files
echo "Staging files..."
git add .

# Commit
echo "Creating commit..."
git commit -m "Deploy Company Monitor Agent to GitHub" || echo "No changes to commit"

# Push
echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✓ Successfully deployed to GitHub!"
echo ""
echo "Next steps:"
echo "1. Go to: $REPO_URL"
echo "2. Go to Settings → Secrets and variables → Actions"
echo "3. Add these 3 secrets:"
echo "   - OPENROUTER_API_KEY"
echo "   - MAIL_USERNAME"
echo "   - MAIL_PASSWORD"
echo "4. Go to Actions tab and run workflow manually"
echo ""
