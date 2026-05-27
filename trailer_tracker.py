No problem! I'll give you the full code to copy directly from here.

Click **+ Code** in Colab, then paste this entire code into it:Here is the full code! Click **+ Code** in Colab, paste ALL of this, then press ▶:

```python
import requests
import smtplib
import json
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from googleapiclient.discovery import build

YOUTUBE_API_KEY   = "AIzaSyBoM0_w2aWD3ufS0e7glC8RnUl47r6spbM"
YOUR_EMAIL        = "yoyolyo2003@gmail.com"
EMAIL_APP_PASSWORD = "jzkxdprisxqtrvgp"
CHECK_EVERY_HOURS = 3
MIN_VIRAL_SCORE   = 40

SEARCH_QUERIES = [
    "official game trailer 2025","game reveal trailer 2025","DLC trailer announcement",
    "anime official trailer 2025","anime season 2 announcement","anime season 2 trailer",
    "new anime PV 2025","tekken trailer","one piece anime trailer","jujutsu kaisen trailer",
    "solo leveling trailer","dragon ball trailer","naruto new anime","demon slayer trailer",
    "black myth wukong","gta trailer","call of duty trailer","elden ring dlc","blue lock anime trailer",
]
TITLE_MUST_CONTAIN = ["trailer","reveal","announce","season","pv","official","dlc","expansion","teaser"]
TITLE_BLACKLIST = ["reaction","review","top 10","ranking","explained","theory","fan made","fanmade","compilation"]
SEEN_FILE = "seen_videos.json"

def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}")

def load_seen():
    if os.path.exists(SEEN_FILE):
        with open(SEEN_FILE,"r") as f: return json.load(f)
    return {}

def save_seen(seen):
    with open(SEEN_FILE,"w") as f: json.dump(seen,f)

def passes_title_filter(title):
    t = title.lower()
    return any(kw in t for kw in TITLE_MUST_CONTAIN) and not any(kw in t for kw in TITLE_BLACKLIST)

def viral_score(views, likes, hours, comments=0):
    if hours < 0.1: hours = 0.1
    return int(min(views/hours/5000*40,40) + min(likes/max(views,1)*200,35) + min(comments/max(views,1)*1000,25))

def category(title):
    t = title.lower()
    if any(k in t for k in ["anime","manga","season","pv","one piece","naruto","demon slayer","jjk","dragon ball","blue lock","solo leveling"]): return "Anime"
    if any(k in t for k in ["game","gameplay","dlc","ps5","xbox","tekken","elden ring","gta","call of duty","black myth","fortnite"]): return "Game"
    return "Viral"

def fetch(youtube, seen):
    found = []
    after = (datetime.utcnow() - timedelta(hours=CHECK_EVERY_HOURS+1)).strftime("%Y-%m-%dT%H:%M:%SZ")
    for query in SEARCH_QUERIES:
        try:
            resp = youtube.search().list(q=query,part="id,snippet",type="video",order="date",publishedAfter=after,maxResults=10).execute()
            ids = [i["id"]["videoId"] for i in resp.get("items",[])]
            if not ids: continue
            stats = youtube.videos().list(part="statistics,snippet",id=",".join(ids)).execute()
            for item in stats.get("items",[]):
                vid = item["id"]
                if vid in seen: continue
                title = item["snippet"]["title"]
                if not passes_title_filter(title): continue
                s = item.get("statistics",{})
                views,likes,comments = int(s.get("viewCount",0)),int(s.get("likeCount",0)),int(s.get("commentCount",0))
                pub = datetime.strptime(item["snippet"]["publishedAt"],"%Y-%m-%dT%H:%M:%SZ")
                hours = max((datetime.utcnow()-pub).total_seconds()/3600,0.1)
                score = viral_score(views,likes,hours,comments)
                if score >= MIN_VIRAL_SCORE:
                    found.append({"id":vid,"title":title,"channel":item["snippet"]["channelTitle"],
                        "url":f"https://youtube.com/watch?v={vid}","thumb":item["snippet"]["thumbnails"].get("high",{}).get("url",""),
                        "views":views,"likes":likes,"comments":comments,"score":score,"hours":round(hours,1),"category":category(title)})
        except Exception as e:
            log(f"Error: {e}")
    deduped = {}
    for v in found:
        if v["id"] not in deduped or v["score"] > deduped[v["id"]]["score"]: deduped[v["id"]] = v
    return sorted(deduped.values(), key=lambda x: x["score"], reverse=True)

def send_email(videos):
    rows = ""
    for v in videos:
        rows += f"""<div style="border:1px solid #e2e8f0;border-radius:10px;padding:16px;margin-bottom:16px;background:#fff;">
          <span style="background:{'#553c9a' if v['category']=='Anime' else '#276749'};color:#fff;font-size:11px;padding:2px 8px;border-radius:20px;">{v['category']}</span>
          <span style="background:#e53e3e;color:#fff;font-size:11px;padding:2px 8px;border-radius:20px;margin-left:6px;">Score {v['score']}/100</span>
          <h3 style="margin:8px 0 4px;font-size:15px;">{v['title']}</h3>
          <p style="margin:0;font-size:13px;color:#718096;">by {v['channel']} · {v['hours']}h ago</p>
          <p style="font-size:13px;">👁 {v['views']:,} views &nbsp; 👍 {v['likes']:,} likes &nbsp; 💬 {v['comments']:,} comments</p>
          <a href="{v['url']}" style="background:#ff0000;color:#fff;padding:8px 18px;border-radius:6px;text-decoration:none;font-weight:600;">▶ Watch on YouTube</a>
        </div>"""
    body = f"""<html><body style="font-family:Arial,sans-serif;background:#f7fafc;padding:20px;">
      <div style="max-width:600px;margin:0 auto;">
        <div style="background:#667eea;border-radius:12px;padding:24px;margin-bottom:24px;text-align:center;">
          <h1 style="color:#fff;margin:0;">🎬 Trailer Alert!</h1>
          <p style="color:#fff;margin:6px 0 0;">{len(videos)} hot trailer(s) found — make your reel fast!</p>
        </div>{rows}</div></body></html>"""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🔥 {len(videos)} Hot Trailer(s) Dropped!"
    msg["From"] = YOUR_EMAIL
    msg["To"] = YOUR_EMAIL
    msg.attach(MIMEText(body,"html"))
    try:
        with smtplib.SMTP("smtp.gmail.com",587) as s:
            s.starttls()
            s.login(YOUR_EMAIL,EMAIL_APP_PASSWORD)
            s.sendmail(YOUR_EMAIL,YOUR_EMAIL,msg.as_string())
        log("✅ Email sent!")
    except Exception as e:
        log(f"❌ Email failed: {e}")

def main():
    print("🎬 TRAILER TRACKER STARTED")
    print(f"   Emailing → {YOUR_EMAIL}")
    print(f"   Scanning every {CHECK_EVERY_HOURS} hours")
    youtube = build("youtube","v3",developerKey=YOUTUBE_API_KEY)
    seen = load_seen()
    while True:
        log("Scanning YouTube...")
        videos = fetch(youtube, seen)
        if videos:
            log(f"Found {len(videos)} trailer(s)!")
            for v in videos: log(f"  [{v['score']}/100] {v['title']}")
            send_email(videos)
            for v in videos: seen[v["id"]] = {"title":v["title"],"found":datetime.now().isoformat()}
            save_seen(seen)
        else:
            log("No new hot trailers this round.")
        log(f"Sleeping {CHECK_EVERY_HOURS} hours...")
        time.sleep(CHECK_EVERY_HOURS * 3600)

main()
```

Press ▶ and it will start! You'll see messages like `Scanning YouTube...` appear below the cell. Tell me what you see!
