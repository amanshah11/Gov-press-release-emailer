# 📰 PIB Daily Press Release Digest

> Automatically scrapes [pib.gov.in](https://www.pib.gov.in) every evening and emails a neatly formatted **Word document** of all that day's press releases — grouped by Ministry, with clickable links.

Runs entirely on **GitHub Actions** for free. No server. No laptop. Works from an iPad.

---

## 📬 What You Get

Every evening at **09:00 PM IST**, a `.docx` lands in your inbox:

- 📋 All press releases published that day
- 🏛️ Correctly grouped by Ministry
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

### 1. Fork this repo

Click **Fork** (top right) to copy it to your own GitHub account.

### 2. Create a Gmail App Password

GitHub needs permission to send email through your Gmail.

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. Make sure 2-Step Verification is enabled first
3. App name: `PIB Digest` → click **Create**
4. Copy the 16-character password shown (remove spaces when saving)

### 3. Add GitHub Secrets

In your repo go to **Settings → Secrets and variables → Actions → New repository secret** and add all three:

| Secret Name | Value |
|---|---|
| `GMAIL_ADDRESS` | Gmail address used to **send** the email |
| `GMAIL_APP_PASSWORD` | 16-character App Password from Step 2 |
| `RECIPIENT_EMAIL` | Email address to **receive** the digest |

> The digest is sent to **both** `GMAIL_ADDRESS` and `RECIPIENT_EMAIL`.

### 4. Test it

Go to **Actions** tab → **PIB Daily Press Release Digest** → **Run workflow** → **Run workflow**.

Wait ~2 minutes. Check your inbox. ✅

The email subject will show today's date. The attached `.docx` contains all releases PIB has published so far today.

---

## 🕐 Schedule

Runs daily at **09:00 PM IST** (3:30 PM UTC).

PIB publishes releases throughout the day — running at 09 PM ensures you get the complete day's list.

To change the time, edit `.github/workflows/pib_daily.yml`:

```yaml
- cron: '30 15 * * *'   # minute hour(UTC) day month weekday
```

| Delivery Time (IST) | Cron (UTC) |
|---|---|
| 9:00 PM | `30 15 * * *`** ← current |
| 10:00 PM | `30 16 * * *` |
| 11:30 PM | `0 18 * * *` |

---

## 📅 How the Date Works

PIB always returns the **current day's** releases regardless of any date parameters in the URL. So:

- The scraper uses `datetime.now()` — whatever day it runs, that day's releases are fetched and the document is labeled with that date
- Running at 09 PM IST means the UTC time is 3:30 PM — still the same calendar date, so the label is always correct
- Running **manually** at any time gives you that day's releases so far

---

## 💾 Artifacts

Every generated `.docx` is also saved under **Actions → your latest run → Artifacts**, kept for 30 days. Useful if you missed an email or want to re-download an old digest.

---

## 🔧 Manual Usage

Run locally with:

```bash
# Install dependencies (once)
pip install requests beautifulsoup4
npm install docx

# Fetch today's releases
python pib_scraper.py

# Fetch and label with a specific date
python pib_scraper.py --date 2026-06-10
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
- Re-run manually from the Actions tab and check the logs

**Red ✗ on the Actions run**
- Click the failed run → click the failed step to read the error
- The workflow auto-retries once (60s wait) before failing
- Most common cause: incorrect App Password, or PIB was temporarily down

**Fewer releases than expected**
- PIB publishes throughout the day — if you run before 09 PM you may not get all releases yet
- Run again at 11 PM for the complete day's list

**GitHub Actions didn't run on schedule**
- Go to Actions tab and check for a yellow "disabled" banner — click Enable
- Or make a small commit (edit README, add a space) to reactivate the schedule
- GitHub pauses scheduled workflows on inactive repos after a period of inactivity
