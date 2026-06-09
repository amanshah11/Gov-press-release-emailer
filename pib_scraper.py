#!/usr/bin/env python3
"""
PIB Daily Press Release Scraper
Fetches all press releases from pib.gov.in for the previous day
and generates a formatted Word document.

Usage:
    python pib_scraper.py              # Fetch yesterday's releases (default)
    python pib_scraper.py --date 2026-06-06   # Fetch a specific date
    python pib_scraper.py --today      # Fetch today's releases
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
import json
import subprocess
import os
import sys
import argparse
import re
import time

# ─────────────────────────────────────────────
#  Configuration
# ─────────────────────────────────────────────
OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

PIB_BASE = "https://www.pib.gov.in/allRel.aspx"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
}

# ─────────────────────────────────────────────
#  Step 1: Scrape release list
# ─────────────────────────────────────────────

def fetch_release_list(target_date: datetime) -> list:
    """Returns list of {ministry, title, url, prid} for the given date."""
    url = (
        f"{PIB_BASE}?reg=48&lang=1"
        f"&d={target_date.day}&m={target_date.month}&y={target_date.year}"
    )
    print(f"  Fetching: {url}")

    session = requests.Session()
    # First visit the homepage to get cookies
    try:
        session.get("https://www.pib.gov.in/index.aspx", headers=HEADERS, timeout=20)
        time.sleep(1)
    except Exception:
        pass

    resp = session.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    soup = BeautifulSoup(resp.text, "html.parser")

    releases = []
    current_ministry = "Uncategorised"

    content = (
        soup.find("div", id="pageContent")
        or soup.find("div", class_="content")
        or soup
    )

    for tag in content.find_all(["h3", "li"]):
        if tag.name == "h3":
            text = tag.get_text(strip=True)
            if text:
                current_ministry = text
        elif tag.name == "li":
            link = tag.find("a", href=True)
            if link and "PressReleasePage" in link.get("href", ""):
                href = link["href"]
                title = link.get_text(strip=True)
                full_url = href if href.startswith("http") else "https://www.pib.gov.in" + href
                prid_match = re.search(r"PRID=(\d+)", full_url, re.IGNORECASE)
                prid = prid_match.group(1) if prid_match else ""
                if title:
                    releases.append({
                        "ministry": current_ministry,
                        "title": title,
                        "url": full_url,
                        "prid": prid,
                    })

    # Deduplicate by PRID — same release can appear under multiple ministries
    seen_prids = set()
    unique_releases = []
    for r in releases:
        if r["prid"] and r["prid"] in seen_prids:
            continue
        if r["prid"]:
            seen_prids.add(r["prid"])
        unique_releases.append(r)

    return unique_releases


# ─────────────────────────────────────────────
#  Step 2: Generate Word document via docx-js
# ─────────────────────────────────────────────

def generate_docx(releases: list, target_date: datetime, output_path: str) -> bool:
    """Generate a .docx report using docx-js (Node.js)."""

    date_str = target_date.strftime("%d %B %Y")

    # Group releases by ministry
    by_ministry = {}
    for r in releases:
        by_ministry.setdefault(r["ministry"], []).append(r)

    items_js = json.dumps(by_ministry, ensure_ascii=False)

    js_script = r"""
const {
  Document, Packer, Paragraph, TextRun, ExternalHyperlink,
  AlignmentType, BorderStyle, ShadingType, LevelFormat,
  Header, Footer, PageNumber, WidthType
} = require('docx');
const fs = require('fs');

const byMinistry = """ + items_js + r""";
const dateStr = """ + json.dumps(date_str) + r""";
const outputPath = """ + json.dumps(output_path) + r""";
const totalReleases = Object.values(byMinistry).reduce((s, a) => s + a.length, 0);

const GOV_BLUE   = "1F3864";
const ACCENT     = "2E75B6";
const LIGHT_BG   = "EAF2FB";
const GREY       = "555555";
const BORDER_COL = "B8CCE4";

const thinBorder = (c) => ({ style: BorderStyle.SINGLE, size: 1, color: c || BORDER_COL });

function spacer(before, after) {
  return new Paragraph({ spacing: { before: before||0, after: after||0 }, children: [] });
}
function rule() {
  return new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 1 } },
    spacing: { before: 0, after: 120 }, children: []
  });
}

// Header
const header = new Header({ children: [
  new Paragraph({
    border: { bottom: { style: BorderStyle.SINGLE, size: 6, color: ACCENT, space: 4 } },
    spacing: { before: 0, after: 0 },
    children: [
      new TextRun({ text: "Press Information Bureau — Government of India", font: "Arial", size: 18, color: GREY }),
      new TextRun({ text: "   |   Daily Digest", font: "Arial", size: 18, color: ACCENT }),
    ]
  })
]});

// Footer
const footer = new Footer({ children: [
  new Paragraph({
    border: { top: { style: BorderStyle.SINGLE, size: 4, color: ACCENT, space: 4 } },
    alignment: AlignmentType.CENTER,
    spacing: { before: 0, after: 0 },
    children: [
      new TextRun({ text: "Source: pib.gov.in  |  Page ", font: "Arial", size: 16, color: GREY }),
      new TextRun({ children: [PageNumber.CURRENT], font: "Arial", size: 16, color: GREY }),
      new TextRun({ text: " of ", font: "Arial", size: 16, color: GREY }),
      new TextRun({ children: [PageNumber.TOTAL_PAGES], font: "Arial", size: 16, color: GREY }),
    ]
  })
]});

const children = [];

// Title
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 200, after: 80 },
  children: [new TextRun({ text: "PIB Daily Press Release Digest", font: "Arial", size: 56, bold: true, color: GOV_BLUE })]
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 0, after: 60 },
  children: [new TextRun({ text: dateStr, font: "Arial", size: 32, color: ACCENT })]
}));
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 0, after: 300 },
  children: [new TextRun({
    text: `${totalReleases} press release${totalReleases !== 1 ? 's' : ''} across ${Object.keys(byMinistry).length} ministr${Object.keys(byMinistry).length !== 1 ? 'ies' : 'y'}`,
    font: "Arial", size: 22, color: GREY, italics: true
  })]
}));
children.push(rule());
children.push(spacer(0, 120));

// Ministry sections
for (const [ministry, items] of Object.entries(byMinistry)) {
  // Ministry heading with left blue bar
  children.push(new Paragraph({
    spacing: { before: 280, after: 80 },
    shading: { fill: LIGHT_BG, type: ShadingType.CLEAR },
    border: { left: { style: BorderStyle.SINGLE, size: 20, color: ACCENT, space: 6 } },
    children: [new TextRun({ text: `  ${ministry}`, font: "Arial", size: 26, bold: true, color: GOV_BLUE })]
  }));
  children.push(new Paragraph({
    spacing: { before: 0, after: 80 },
    children: [new TextRun({ text: `${items.length} release${items.length !== 1 ? 's' : ''}`, font: "Arial", size: 18, color: GREY, italics: true })]
  }));

  // Releases
  for (const r of items) {
    children.push(new Paragraph({
      numbering: { reference: "nums", level: 0 },
      spacing: { before: 100, after: 60 },
      children: [
        new ExternalHyperlink({
          link: r.url,
          children: [new TextRun({ text: r.title, font: "Arial", size: 22, color: ACCENT, style: "Hyperlink" })]
        }),
        ...(r.prid ? [new TextRun({ text: `  [PRID: ${r.prid}]`, font: "Arial", size: 18, color: GREY, italics: true })] : [])
      ]
    }));
  }
  children.push(spacer(0, 80));
}

children.push(rule());
children.push(new Paragraph({
  alignment: AlignmentType.CENTER, spacing: { before: 200, after: 0 },
  children: [new TextRun({
    text: `Auto-generated on ${new Date().toLocaleString('en-IN', {timeZone:'Asia/Kolkata'})} IST  |  pib.gov.in`,
    font: "Arial", size: 18, color: GREY, italics: true
  })]
}));

const doc = new Document({
  numbering: { config: [{
    reference: "nums",
    levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "%1.", alignment: AlignmentType.LEFT,
      style: { paragraph: { indent: { left: 540, hanging: 360 } } } }]
  }]},
  styles: { default: { document: { run: { font: "Arial", size: 22 } } } },
  sections: [{
    headers: { default: header },
    footers: { default: footer },
    properties: { page: { size: { width: 11906, height: 16838 }, margin: { top: 1200, right: 1200, bottom: 1200, left: 1200 } } },
    children
  }]
});

Packer.toBuffer(doc).then(buf => {
  fs.writeFileSync(outputPath, buf);
  console.log("DOCX_OK:" + outputPath);
}).catch(err => {
  console.error("DOCX_ERR:" + err.message);
  process.exit(1);
});
"""

    js_path = os.path.join(SCRIPT_DIR, "_gen_doc.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_script)

    # Set NODE_PATH so Node can find 'docx' whether installed locally or globally
    env = os.environ.copy()
    local_modules = os.path.join(SCRIPT_DIR, "node_modules")
    try:
        global_modules = subprocess.run(
            ["npm", "root", "-g"], capture_output=True, text=True
        ).stdout.strip()
    except Exception:
        global_modules = ""
    env["NODE_PATH"] = local_modules + os.pathsep + global_modules

    result = subprocess.run(["node", js_path], capture_output=True, text=True, env=env)

    try:
        os.unlink(js_path)
    except Exception:
        pass

    if "DOCX_OK:" in result.stdout:
        return True
    print(f"  JS error: {result.stderr or result.stdout}")
    return False


# ─────────────────────────────────────────────
#  Step 3: Set GitHub env var for email subject
# ─────────────────────────────────────────────

def set_github_env(key: str, value: str):
    """Write to GITHUB_ENV so later workflow steps can use the value."""
    github_env = os.environ.get("GITHUB_ENV")
    if github_env:
        with open(github_env, "a") as f:
            f.write(f"{key}={value}\n")


# ─────────────────────────────────────────────
#  Main
# ─────────────────────────────────────────────

def run(target_date: datetime):
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"\n{'='*55}")
    print(f"  PIB Digest — {target_date.strftime('%d %B %Y')}")
    print(f"{'='*55}\n")

    # Export date for GitHub Actions email subject line
    set_github_env("DIGEST_DATE", target_date.strftime("%d %B %Y"))

    print("[1/3] Fetching release list from pib.gov.in...")
    releases = fetch_release_list(target_date)

    if not releases:
        print("\n  No releases found for this date.")
        print("  This can happen on public holidays or if PIB hasn't published yet.")
        print("  Creating a 'no releases' notice document...\n")
        # Create a minimal notice doc so the email step doesn't fail
        releases = [{
            "ministry": "Notice",
            "title": f"No press releases found on PIB for {target_date.strftime('%d %B %Y')}",
            "url": "https://www.pib.gov.in",
            "prid": ""
        }]

    ministry_count = len(set(r["ministry"] for r in releases))
    print(f"  Found {len(releases)} releases across {ministry_count} ministries.\n")

    date_slug = target_date.strftime("%Y-%m-%d")
    output_path = os.path.join(OUTPUT_DIR, f"PIB_Digest_{date_slug}.docx")

    print("[2/3] Generating Word document...")
    success = generate_docx(releases, target_date, output_path)

    if success:
        size_kb = os.path.getsize(output_path) // 1024
        print(f"\n[3/3] Done! → {output_path} ({size_kb} KB)\n")
        return output_path
    else:
        print("\n  Failed to generate document.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PIB Daily Press Release Scraper")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--date", type=str, help="Target date (YYYY-MM-DD)")
    group.add_argument("--today", action="store_true", help="Fetch today's releases")
    args = parser.parse_args()

    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d")
    elif args.today:
        target = datetime.now()
    else:
        # Use IST timezone so "yesterday" is correct regardless of when GitHub runs
        IST = ZoneInfo("Asia/Kolkata")
        target = datetime.now(IST) - timedelta(days=1)

    run(target)
