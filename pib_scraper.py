#!/usr/bin/env python3
"""
PIB Daily Press Release Scraper
Fetches all English press releases from pib.gov.in for yesterday
and generates a formatted Word document.

Usage:
    python pib_scraper.py              # yesterday (default)
    python pib_scraper.py --date 2026-06-08
    python pib_scraper.py --today
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json, subprocess, os, sys, argparse, re

OUTPUT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output")
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PIB_BASE   = "https://www.pib.gov.in/allRel.aspx"

# ── Critical: these headers tell PIB to serve English content ──────────────
HEADERS = {
    "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/124.0.0.0 Safari/537.36",
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",   # ← PIB uses this to decide language
    "Accept-Encoding": "gzip, deflate, br",
    "Connection":      "keep-alive",
    "Cache-Control":   "no-cache",
    "Pragma":          "no-cache",
}


def fetch_release_list(target_date: datetime) -> list:
    url = (f"{PIB_BASE}?reg=48&lang=1"
           f"&d={target_date.day}&m={target_date.month}&y={target_date.year}")
    print(f"  Fetching: {url}")

    # Single clean request — no sessions, no cookies, no pre-visits
    # Sessions/cookie manipulation caused Hindi fallback in previous versions
    resp = requests.get(url, headers=HEADERS, timeout=30)
    resp.raise_for_status()

    # Language guard
    if "सभी विज्ञप्ति" in resp.text and "All Releases" not in resp.text:
        raise RuntimeError(
            "PIB returned Hindi page. Re-run the workflow — this is a transient PIB server issue."
        )

    soup = BeautifulSoup(resp.text, "html.parser")

    # Log what PIB says the count is
    count_tag = soup.find(string=re.compile(r"Displaying \d+ Press Release"))
    if count_tag:
        print(f"  PIB reports: {count_tag.strip()}")

    releases, current_ministry = [], "Uncategorised"
    content = (soup.find("div", id="pageContent")
               or soup.find("div", class_="content")
               or soup)

    for tag in content.find_all(["h3", "li"]):
        if tag.name == "h3":
            text = tag.get_text(strip=True)
            if text:
                current_ministry = text
        elif tag.name == "li":
            link = tag.find("a", href=True)
            if link and "PressReleasePage" in link.get("href", ""):
                href     = link["href"]
                title    = link.get_text(strip=True)
                full_url = href if href.startswith("http") else "https://www.pib.gov.in" + href
                m        = re.search(r"PRID=(\d+)", full_url, re.IGNORECASE)
                prid     = m.group(1) if m else ""
                if title:
                    releases.append({"ministry": current_ministry,
                                     "title": title, "url": full_url, "prid": prid})

    # Deduplicate by PRID
    seen, unique = set(), []
    for r in releases:
        if r["prid"] and r["prid"] in seen:
            continue
        if r["prid"]:
            seen.add(r["prid"])
        unique.append(r)

    return unique


def generate_docx(releases: list, target_date: datetime, output_path: str) -> bool:
    date_str    = target_date.strftime("%d %B %Y")
    by_ministry = {}
    for r in releases:
        by_ministry.setdefault(r["ministry"], []).append(r)

    js_script = r"""
const {
  Document, Packer, Paragraph, TextRun, ExternalHyperlink,
  AlignmentType, BorderStyle, ShadingType, LevelFormat,
  Header, Footer, PageNumber
} = require('docx');
const fs = require('fs');

const byMinistry = """ + json.dumps(by_ministry, ensure_ascii=False) + r""";
const dateStr    = """ + json.dumps(date_str) + r""";
const outputPath = """ + json.dumps(output_path) + r""";
const total      = Object.values(byMinistry).reduce((s,a)=>s+a.length,0);

const GOV_BLUE="1F3864",ACCENT="2E75B6",LIGHT_BG="EAF2FB",GREY="555555";
const sp=(b,a)=>new Paragraph({spacing:{before:b||0,after:a||0},children:[]});
const rule=()=>new Paragraph({border:{bottom:{style:BorderStyle.SINGLE,size:4,color:ACCENT,space:1}},spacing:{before:0,after:120},children:[]});

const header=new Header({children:[new Paragraph({border:{bottom:{style:BorderStyle.SINGLE,size:6,color:ACCENT,space:4}},spacing:{before:0,after:0},children:[new TextRun({text:"Press Information Bureau — Government of India",font:"Arial",size:18,color:GREY}),new TextRun({text:"   |   Daily Digest",font:"Arial",size:18,color:ACCENT})]})]});
const footer=new Footer({children:[new Paragraph({border:{top:{style:BorderStyle.SINGLE,size:4,color:ACCENT,space:4}},alignment:AlignmentType.CENTER,spacing:{before:0,after:0},children:[new TextRun({text:"Source: pib.gov.in  |  Page ",font:"Arial",size:16,color:GREY}),new TextRun({children:[PageNumber.CURRENT],font:"Arial",size:16,color:GREY}),new TextRun({text:" of ",font:"Arial",size:16,color:GREY}),new TextRun({children:[PageNumber.TOTAL_PAGES],font:"Arial",size:16,color:GREY})]})]});

const children=[];
children.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:200,after:80},children:[new TextRun({text:"PIB Daily Press Release Digest",font:"Arial",size:56,bold:true,color:GOV_BLUE})]}));
children.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:0,after:60},children:[new TextRun({text:dateStr,font:"Arial",size:32,color:ACCENT})]}));
children.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:0,after:300},children:[new TextRun({text:`${total} press release${total!==1?'s':''} across ${Object.keys(byMinistry).length} ministr${Object.keys(byMinistry).length!==1?'ies':'y'}`,font:"Arial",size:22,color:GREY,italics:true})]}));
children.push(rule());children.push(sp(0,120));

for(const[ministry,items]of Object.entries(byMinistry)){
  children.push(new Paragraph({spacing:{before:280,after:80},shading:{fill:LIGHT_BG,type:ShadingType.CLEAR},border:{left:{style:BorderStyle.SINGLE,size:20,color:ACCENT,space:6}},children:[new TextRun({text:`  ${ministry}`,font:"Arial",size:26,bold:true,color:GOV_BLUE})]}));
  children.push(new Paragraph({spacing:{before:0,after:80},children:[new TextRun({text:`${items.length} release${items.length!==1?'s':''}`,font:"Arial",size:18,color:GREY,italics:true})]}));
  for(const r of items){
    children.push(new Paragraph({numbering:{reference:"nums",level:0},spacing:{before:100,after:60},children:[new ExternalHyperlink({link:r.url,children:[new TextRun({text:r.title,font:"Arial",size:22,color:ACCENT,style:"Hyperlink"})]}),
    ...(r.prid?[new TextRun({text:`  [PRID: ${r.prid}]`,font:"Arial",size:18,color:GREY,italics:true})]:[])]}));
  }
  children.push(sp(0,80));
}
children.push(rule());
children.push(new Paragraph({alignment:AlignmentType.CENTER,spacing:{before:200,after:0},children:[new TextRun({text:`Auto-generated on ${new Date().toLocaleString('en-IN',{timeZone:'Asia/Kolkata'})} IST  |  pib.gov.in`,font:"Arial",size:18,color:GREY,italics:true})]}));

const doc=new Document({
  numbering:{config:[{reference:"nums",levels:[{level:0,format:LevelFormat.DECIMAL,text:"%1.",alignment:AlignmentType.LEFT,style:{paragraph:{indent:{left:540,hanging:360}}}}]}]},
  styles:{default:{document:{run:{font:"Arial",size:22}}}},
  sections:[{headers:{default:header},footers:{default:footer},properties:{page:{size:{width:11906,height:16838},margin:{top:1200,right:1200,bottom:1200,left:1200}}},children}]
});
Packer.toBuffer(doc).then(buf=>{fs.writeFileSync(outputPath,buf);console.log("DOCX_OK:"+outputPath);}).catch(err=>{console.error("DOCX_ERR:"+err.message);process.exit(1);});
"""

    js_path = os.path.join(SCRIPT_DIR, "_gen_doc.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write(js_script)

    env = os.environ.copy()
    local_modules = os.path.join(SCRIPT_DIR, "node_modules")
    try:
        global_modules = subprocess.run(["npm","root","-g"],capture_output=True,text=True).stdout.strip()
    except:
        global_modules = ""
    env["NODE_PATH"] = local_modules + os.pathsep + global_modules

    result = subprocess.run(["node", js_path], capture_output=True, text=True, env=env)
    try: os.unlink(js_path)
    except: pass

    if "DOCX_OK:" in result.stdout:
        return True
    print(f"  JS error: {result.stderr or result.stdout}")
    return False


def set_github_env(key, value):
    genv = os.environ.get("GITHUB_ENV")
    if genv:
        with open(genv, "a") as f:
            f.write(f"{key}={value}\n")


def run(target_date: datetime):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    print(f"\n{'='*55}")
    print(f"  PIB Digest — {target_date.strftime('%d %B %Y')}")
    print(f"{'='*55}\n")
    set_github_env("DIGEST_DATE", target_date.strftime("%d %B %Y"))

    print("[1/3] Fetching releases...")
    releases = fetch_release_list(target_date)

    if not releases:
        print("  No releases found.")
        releases = [{"ministry":"Notice",
                     "title":f"No press releases found on PIB for {target_date.strftime('%d %B %Y')}",
                     "url":"https://www.pib.gov.in","prid":""}]

    print(f"  Found {len(releases)} releases across {len(set(r['ministry'] for r in releases))} ministries.\n")

    output_path = os.path.join(OUTPUT_DIR, f"PIB_Digest_{target_date.strftime('%Y-%m-%d')}.docx")

    print("[2/3] Generating Word document...")
    if generate_docx(releases, target_date, output_path):
        print(f"\n[3/3] Done! → {output_path} ({os.path.getsize(output_path)//1024} KB)\n")
    else:
        print("\n  Failed to generate document.")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--date",  type=str)
    g.add_argument("--today", action="store_true")
    args = parser.parse_args()

    if args.date:
        target = datetime.strptime(args.date, "%Y-%m-%d")
    elif args.today:
        target = datetime.now()
    else:
        target = datetime.now() - timedelta(days=1)  # yesterday

    run(target)
