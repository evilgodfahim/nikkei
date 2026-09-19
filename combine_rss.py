import feedparser
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
import re

rss_feeds = [
    ("https://asia.nikkei.com/rss/feed/nar", "https://archive.is/o/EGrwV/"),
]

def escape_xml(text):
    if not text:
        return ""
    text = str(text)
    text = text.replace("&", "&amp;")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    text = text.replace('"', "&quot;")
    text = text.replace("'", "&apos;")
    return text

def extract_image(entry):
    if hasattr(entry, "media_content") and entry.media_content:
        for media in entry.media_content:
            if "url" in media:
                return media["url"]

    if hasattr(entry, "media_thumbnail") and entry.media_thumbnail:
        for thumb in entry.media_thumbnail:
            if "url" in thumb:
                return thumb["url"]

    if hasattr(entry, "enclosures") and entry.enclosures:
        for enc in entry.enclosures:
            if enc.get("type", "").startswith("image/"):
                return enc.get("url", "")

    content = ""
    if hasattr(entry, "content") and entry.content:
        content = entry.content[0].get("value", "")
    elif hasattr(entry, "summary"):
        content = entry.summary
    elif hasattr(entry, "description"):
        content = entry.description

    if content:
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', content, re.IGNORECASE)
        if img_match:
            return img_match.group(1)

    return None

def fetch_items(feed_tuples):
    all_items = []

    for feed_url, archive_prefix in feed_tuples:
        print(f"Fetching: {feed_url}")
        try:
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                if not hasattr(entry, "link"):
                    continue

                original_link = entry.link
                archive_link = archive_prefix + original_link

                image_url = extract_image(entry)
                if image_url:
                    print(f"  📸 Image found: {image_url[:60]}...")

                raw_date = entry.get("published", "")
                try:
                    pub_dt = parsedate_to_datetime(raw_date)
                    if pub_dt.tzinfo is None:
                        pub_dt = pub_dt.replace(tzinfo=timezone.utc)
                    pub_str = raw_date
                except Exception:
                    pub_dt = datetime.now(timezone.utc)
                    pub_str = pub_dt.strftime("%a, %d %b %Y %H:%M:%S +0000")

                all_items.append({
                    "title": entry.title,
                    "link": archive_link,
                    "description": entry.get("description", ""),
                    "pubDate": pub_str,
                    "pub_dt": pub_dt,
                    "image": image_url
                })
        except Exception as e:
            print(f"  ❌ Error: {e}")

    all_items.sort(key=lambda x: x["pub_dt"], reverse=True)

    limited_items = all_items[:500]
    print(f"\n✅ Total items: {len(limited_items)}")
    print(f"📸 Items with images: {sum(1 for i in limited_items if i['image'])}")

    return limited_items

def create_rss(items):
    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<rss version="2.0" xmlns:media="http://search.yahoo.com/mrss/">')
    xml_lines.append('  <channel>')
    xml_lines.append('    <title>Nikkei Asia RSS Feed</title>')
    xml_lines.append('    <link>https://yourusername.github.io/combined.xml</link>')
    xml_lines.append('    <description>Nikkei Asia feed with archive.is links</description>')

    for item in items:
        xml_lines.append('    <item>')
        xml_lines.append(f'      <title>{escape_xml(item["title"])}</title>')
        xml_lines.append(f'      <link>{escape_xml(item["link"])}</link>')
        xml_lines.append(f'      <description>{escape_xml(item["description"])}</description>')
        xml_lines.append(f'      <pubDate>{item["pubDate"]}</pubDate>')

        if item["image"]:
            xml_lines.append(f'      <media:thumbnail url="{escape_xml(item["image"])}" />')
            xml_lines.append(f'      <media:content url="{escape_xml(item["image"])}" medium="image" />')
            xml_lines.append(f'      <enclosure url="{escape_xml(item["image"])}" type="image/jpeg" />')

        xml_lines.append('    </item>')

    xml_lines.append('  </channel>')
    xml_lines.append('</rss>')

    return '\n'.join(xml_lines)

if __name__ == "__main__":
    print("=" * 70)
    print("Nikkei Asia RSS Feed Aggregator")
    print("=" * 70)

    items = fetch_items(rss_feeds)
    rss_xml = create_rss(items)

    with open("combined.xml", "w", encoding="utf-8") as f:
        f.write(rss_xml)

    print("\n✅ Combined RSS feed created successfully (combined.xml)")
    print("=" * 70)
