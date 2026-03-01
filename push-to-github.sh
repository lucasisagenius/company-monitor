#!/bin/bash
# Push Company Monitor to GitHub

set -e

echo "Company Monitor - GitHub Push Script"
echo "====================================="
echo ""

# Check if git is initialized
if [ ! -d .git ]; then
    echo "Git not initialized. Initializing..."
    git init
fi

# Check if remote exists
if ! git remote get-url origin &>/dev/null; then
    echo "No remote found. Please enter your GitHub repository URL:"
    read -p "Repository URL (https://github.com/USERNAME/company-monitor.git): " repo_url
    git remote add origin "$repo_url"
else
    echo "Remote found: $(git remote get-url origin)"
fi

echo ""
echo "Staging files..."
git add .

echo "Creating commit..."
git commit -m "Deploy Company Monitor Agent to GitHub" || echo "No changes to commit"

echo ""
echo "Pushing to GitHub..."
git branch -M main
git push -u origin main

echo ""
echo "✓ Successfully pushed to GitHub!"
echo ""
echo "Next steps:"
echo "1. Go to: https://github.com/YOUR-USERNAME/company-monitor"
echo "2. Click Settings → Secrets and variables → Actions"
echo "3. Add these secrets:"
echo "   - OPENROUTER_API_KEY"
echo "   - MAIL_USERNAME"
echo "   - MAIL_PASSWORD"
echo "4. Go to Actions tab and run the workflow manually"
echo ""
echo "See GITHUB_DEPLOYMENT.md for detailed instructions"
