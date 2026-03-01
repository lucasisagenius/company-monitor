# GitHub Actions Deployment Guide

This guide explains how to deploy the Company Monitor Agent on GitHub Actions for free!

## Overview

- **Cost:** FREE (unlimited for public repositories)
- **Runs:** Every 6 hours on schedule
- **Storage:** GitHub repositories (free)
- **Data Persistence:** SQLite database backed up to GitHub

## Setup Steps (5 minutes)

### Step 1: Create GitHub Repository

```bash
# If not already done
cd ~/company-monitor
git init
git add .
git commit -m "Initial commit: Company Monitor Agent"
```

Create a new repository on [GitHub.com](https://github.com/new):
- Name: `company-monitor`
- Description: "Automated monitoring of company news and filings"
- Public (recommended for free GitHub Actions)
- Click "Create repository"

### Step 2: Push to GitHub

```bash
git remote add origin https://github.com/YOUR-USERNAME/company-monitor.git
git branch -M main
git push -u origin main
```

### Step 3: Add Secrets to GitHub

Go to your repository on GitHub:

**Settings → Secrets and variables → Actions**

Click **"New repository secret"** and add these secrets:

#### Secret 1: OPENROUTER_API_KEY
- Name: `OPENROUTER_API_KEY`
- Value: `sk-or-v1-...` (your API key from .env)

#### Secret 2: MAIL_USERNAME
- Name: `MAIL_USERNAME`
- Value: `your-email@gmail.com` (from .env)

#### Secret 3: MAIL_PASSWORD
- Name: `MAIL_PASSWORD`
- Value: Your Gmail App Password (from .env)

**Important:** Never commit `.env` file to GitHub!

### Step 4: Test the Workflow

Go to **Actions** tab in GitHub → **Company Monitor Agent** workflow

Click **"Run workflow"** → **"Run workflow"** button

Wait 1-2 minutes and check if:
- ✅ All steps are green
- ✅ Email is received

### Step 5: Verify Scheduled Runs

The workflow runs automatically at:
- **8:00 AM UTC**
- **2:00 PM UTC**
- **8:00 PM UTC**

(You can adjust times in `.github/workflows/monitor.yml` line 6)

---

## Monitoring Your Deployment

### Check Workflow Runs

1. Go to GitHub repository
2. Click **"Actions"** tab
3. Click **"Company Monitor Agent"**
4. See all run history with status (✅ passed or ❌ failed)

### Check Run Logs

Click on any run → View detailed logs:
- Fetched items count
- Items filtered by date
- Email sent confirmation
- Any errors

### View Database Updates

Click on any successful run → Scroll to "Artifacts"

The `monitor.db` file is automatically:
- ✅ Updated after each run
- ✅ Committed to GitHub
- ✅ Backed up (never lost)

---

## Customization

### Change Schedule

Edit `.github/workflows/monitor.yml`:

```yaml
on:
  schedule:
    - cron: '0 8,14,20 * * *'  # Modify these times
```

**Cron format:** `minute hour day month weekday`

Examples:
```yaml
# Every day at 9am UTC
- cron: '0 9 * * *'

# Every 6 hours
- cron: '0 */6 * * *'

# Every hour
- cron: '0 * * * *'

# Every Monday at 8am
- cron: '0 8 * * 1'
```

### Change Companies/Configuration

Edit `config/companies.yaml` and push to GitHub:

```bash
git add config/companies.yaml
git commit -m "Update companies config"
git push
```

The workflow will use the updated config on next run.

---

## Troubleshooting

### Workflow doesn't run

**Solution:** Check if workflow is enabled:
- Go to **Actions** tab
- Click **"Company Monitor Agent"**
- If disabled, click "Enable workflow"

### Email not received

**Solution:**
1. Check GitHub Action logs for errors
2. Verify secrets are correctly set
3. Check your email spam folder
4. Test manually: `python scheduler.py --run-once`

### Database not updating

**Solution:**
1. Check workflow logs for "Commit database changes" step
2. Verify GitHub token has write permissions
3. Check if there are new items to report

---

## Disk Storage Used

- Repository: ~5-10 MB
- SQLite database: Grows ~1 KB per item tracked
- At 50 items/week: ~200 KB/month

Very small footprint!

---

## Costs

| Item | Cost |
|------|------|
| GitHub repository | FREE |
| GitHub Actions (unlimited for public) | FREE |
| Storage (50 GB free) | FREE |
| Total | **FREE** |

---

## Advanced: Private Repository

If you want a **private repository**:

1. Create **private** repository on GitHub
2. GitHub Actions are still free for private repos (with limits):
   - 2,000 minutes/month on macOS
   - 3,000 minutes/month on Linux
   - This agent uses ~2 minutes per run × 3 runs/day = ~180 minutes/month ✅ Within free tier

**Recommendation:** Keep it **public** for unlimited free GitHub Actions!

---

## Workflow File Structure

`.github/workflows/monitor.yml` does:

1. **Trigger:** Every 6 hours (or on manual run)
2. **Setup:** Install Python 3.11
3. **Install:** Install requirements.txt
4. **Configure:** Create .env from GitHub secrets
5. **Run:** Execute `scheduler.py --run-once`
6. **Backup:** Commit database to GitHub
7. **Notify:** Alert if anything fails

---

## Manual Trigger

Want to run immediately without waiting for scheduled time?

1. Go to **Actions** tab
2. Click **"Company Monitor Agent"** workflow
3. Click **"Run workflow"** dropdown
4. Click **"Run workflow"** button
5. Check logs in 1-2 minutes

---

## Next Steps

1. ✅ Push to GitHub
2. ✅ Add secrets
3. ✅ Test workflow manually
4. ✅ Wait for first scheduled run
5. ✅ Monitor via GitHub Actions tab

You're all set! 🚀

---

## Support

**Issue:** Something not working?

Check these in order:
1. GitHub Actions logs (Actions → Run → Logs)
2. Secrets are correctly set (Settings → Secrets)
3. `.env` file is NOT committed to GitHub
4. Requirements are installed
5. Test locally: `python scheduler.py --run-once`

---

## File Reference

Key files in `.github/workflows/`:

- `monitor.yml` - Main workflow configuration

Key files in root:
- `scheduler.py` - Entry point
- `agent.py` - Main logic
- `requirements.txt` - Dependencies
- `config/companies.yaml` - Your companies
- `monitor.db` - Tracking database (auto-backed up)

Note: `.env` is NOT committed (stays secure!)
