# PIB Digest — Complete iPad Setup Guide
## Get daily press releases in your inbox, fully automated, 100% free

---

## What you'll need
- Your iPad
- A Gmail account (you probably already have one)
- 15 minutes

---

## PART 1 — Prepare your Gmail (5 minutes)

GitHub needs special permission to send emails through your Gmail.
You create an "App Password" — a one-time code just for this.

**Step 1.1 — Turn on 2-Step Verification (required first)**
1. On your iPad, open Safari and go to: **myaccount.google.com**
2. Tap **Security** (in the left menu, or scroll down)
3. Tap **2-Step Verification** → follow the steps to turn it on
   *(If it's already on, skip to Step 1.2)*

**Step 1.2 — Create an App Password**
1. Go to: **myaccount.google.com/apppasswords**
   *(You may need to sign in again)*
2. Under "App name", type: `PIB Digest`
3. Tap **Create**
4. Google shows you a **16-letter password** like: `abcd efgh ijkl mnop`
5. **Screenshot this or write it down** — you'll need it in Part 3
   *(Remove the spaces when you use it: `abcdefghijklmnop`)*

---

## PART 2 — Set up GitHub (5 minutes)

**Step 2.1 — Create a free GitHub account**
1. Open Safari, go to: **github.com**
2. Tap **Sign up**
3. Enter your email, create a password, choose a username
4. Verify your email when they send you a confirmation

**Step 2.2 — Create a new repository**
1. After signing in, tap the **+** icon (top right) → **New repository**
2. Fill in:
   - Repository name: `pib-digest`
   - Description: `Daily PIB press release digest`
   - Visibility: **Public** ← important (free Actions only on public repos)
3. Tick **Add a README file**
4. Tap **Create repository**

**Step 2.3 — Upload the script file**
1. You should now see your new empty repository
2. Tap **Add file** → **Upload files**
3. Upload **`pib_scraper.py`** (the file you downloaded earlier)
4. Scroll down, tap **Commit changes**

**Step 2.4 — Create the workflow folder structure**
GitHub Actions needs files in a specific folder: `.github/workflows/`

1. In your repository, tap **Add file** → **Create new file**
2. In the filename box at the top, type exactly:
   ```
   .github/workflows/pib_daily.yml
   ```
   *(As you type the `/` characters, GitHub automatically creates the folders)*
3. In the big text area below, paste the **entire contents** of `pib_daily.yml`
   (the other file you downloaded)
4. Scroll down, tap **Commit new file**

---

## PART 3 — Add your Gmail secrets (3 minutes)

GitHub stores your email and password securely as "Secrets" —
they're encrypted and never visible to anyone, even you, after saving.

1. In your repository, tap **Settings** (tab at the top)
2. In the left sidebar, tap **Secrets and variables** → **Actions**
3. Tap **New repository secret**

**Add Secret 1:**
- Name: `GMAIL_ADDRESS`
- Secret: `yourname@gmail.com` ← your actual Gmail address
- Tap **Add secret**

**Add Secret 2:**
- Tap **New repository secret** again
- Name: `GMAIL_APP_PASSWORD`
- Secret: `abcdefghijklmnop` ← the 16-letter code from Part 1, no spaces
- Tap **Add secret**

---

## PART 4 — Test it right now (2 minutes)

Don't wait until tomorrow morning — test it immediately!

1. In your repository, tap the **Actions** tab
2. On the left, tap **PIB Daily Press Release Digest**
3. On the right, tap **Run workflow** → **Run workflow** (green button)
4. Wait about 2-3 minutes — you'll see a yellow spinning circle turn green ✓
5. Check your Gmail inbox — the digest should be there!

If you see a red ✗ instead of green, tap it to see what went wrong —
most likely the App Password was typed incorrectly.

---

## You're done!

From now on, every morning at **7:30 AM IST**, GitHub will automatically:
1. Scrape pib.gov.in for yesterday's press releases
2. Generate a neat Word document grouped by Ministry
3. Email it to your Gmail

**The digest will also be saved in GitHub** under Actions → your latest run →
Artifacts, in case you want to re-download an old one.

---

## Troubleshooting

**Email not arriving?**
- Check your Spam folder
- Make sure the App Password has no spaces
- Re-run manually from the Actions tab and check for errors

**Red ✗ on the Actions run?**
- Tap the failed run → tap the failed step to see the error message
- Most common: wrong App Password, or PIB website was temporarily down

**Want to change the delivery time?**
- In your repository, go to `.github/workflows/pib_daily.yml`
- Tap the pencil (edit) icon
- Change `'0 2 * * *'` — the numbers mean: minute, hour (UTC), day, month, weekday
- 7:30 AM IST = 2:00 AM UTC → `'0 2 * * *'`
- 8:00 AM IST = 2:30 AM UTC → `'30 2 * * *'`
- 6:00 AM IST = 0:30 AM UTC → `'30 0 * * *'`

**Want releases for a specific ministry only?**
- This can be added to the script — just ask!
