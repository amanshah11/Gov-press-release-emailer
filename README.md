# 📰 PIB Daily Press Release Digest

> Automatically scrapes [pib.gov.in](https://www.pib.gov.in) every morning and emails a neatly formatted **Word document** of all press releases from the previous day — grouped by Ministry, with clickable links.

Runs entirely on **GitHub Actions** for free. No server. No laptop. Works from an iPad.

---

## 📬 What You Get

Every morning at **7:30 AM IST**, a `.docx` lands in your inbox:

- 📋 All press releases from the previous day
- 🏛️ Grouped by Ministry
- 🔗 Each title is a clickable link to the full release on pib.gov.in
- 🔢 PRID reference number for each release
- 📄 Page numbers, header, footer, auto-timestamp

---

## 🗂️ Repository Structure

```
├── pib_scraper.py                  # Main scraper + Word doc generator
└── .github/
    └── workflows/
        └── pib_daily.yml           # GitHub Actions schedule & email config
```

---

## ⚙️ Setup

### 1. Fork or clone this repo

Click **Fork** (top right) to copy it to your own GitHub account.

### 2. Create a Gmail App Password

GitHub needs permission to send email through Gmail.

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Make sure 2-Step Verification is enabled first
3. App name: `PIB Digest` → click **Create**
4. Copy the 16-character password shown (remove spaces when saving)

### 3. Add GitHub Secrets

In your repo, go to **Settings → Secrets and variables → Actions → New repository secret** and add all three:

| Secret Name | Value |
|---|---|
| `GMAIL_ADDRESS` | The Gmail address used to **send** the email |
| `GMAIL_APP_PASSWORD` | The 16-character App Password from Step 2 |
| `RECIPIENT_EMAIL` | The email address to **receive** the digest |

### 4. Test it

Go to the **Actions** tab → **PIB Daily Press Release Digest** → **Run workflow** → **Run workflow**.

Wait ~2 minutes. Check your inbox. ✅

---

## 🕐 Schedule

The workflow runs daily at **2:00 AM UTC = 7:30 AM IST**.

To change the time, edit `.github/workflows/pib_daily.yml` and update the cron line:

```yaml
- cron: '0 2 * * *'   # minute hour(UTC) day month weekday
```

| Delivery Time (IST) | Cron (UTC) |
|---|---|
| 6:00 AM | `30 0 * * *` |
| 7:30 AM | `0 2 * * *` |
| 8:00 AM | `30 2 * * *` |
| 9:00 AM | `30 3 * * *` |

---

## 💾 Artifacts

Every generated `.docx` is also saved under **Actions → your latest run → Artifacts**, kept for 30 days. Useful if you missed an email or want to re-download an old digest.

---

## 🔧 Manual Usage

You can also run the scraper locally:

```bash
# Install dependencies
pip install requests beautifulsoup4
npm install docx

# Fetch yesterday's releases (default)
python pib_scraper.py

# Fetch a specific date
python pib_scraper.py --date 2026-06-06

# Fetch today's releases
python pib_scraper.py --today
```

Output `.docx` files appear in the `output/` folder.

---

## 🆓 Cost

| Resource | Cost |
|---|---|
| GitHub account | Free |
| GitHub Actions (public repo) | Free — 2,000 min/month included |
| This workflow (per run) | ~2 minutes |
| Monthly usage | ~60 min/month |
| Gmail sending | Free |

---

## 📡 Data Source

All data is fetched from the official **Press Information Bureau** website:
[https://www.pib.gov.in](https://www.pib.gov.in) — Government of India

---

## 🛠️ Troubleshooting

**No email received**
- Check your spam folder
- Verify the App Password has no spaces
- Re-run from Actions tab and check the logs

**Red ✗ on the Actions run**
- Click the failed run → click the failed step to read the error
- Most common cause: incorrect App Password, or PIB was temporarily down

**Empty digest / no releases found**
- PIB may not have published for that day (public holidays, weekends)
- The script handles this gracefully and still sends a notice email
