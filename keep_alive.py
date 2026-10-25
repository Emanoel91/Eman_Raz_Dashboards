import json
import re
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

PORTFOLIO_URL = "https://emanraz-dashboards.streamlit.app/"

WAKE_BUTTON = re.compile(r"get this app back up", re.I)


def load_urls():
    data = json.loads(Path("dashboards.json").read_text(encoding="utf-8"))
    urls = [d["url"] for d in data["dashboards"] if d.get("url")]
    urls.append(PORTFOLIO_URL)
    return list(dict.fromkeys(urls))  # حذف تکراری‌ها با حفظ ترتیب


def ping(browser, url):
    page = browser.new_page()
    try:
        page.goto(url, wait_until="domcontentloaded", timeout=60_000)
        page.wait_for_timeout(5_000)

        woke = False
        button = page.get_by_role("button", name=WAKE_BUTTON)
        if button.count() > 0:
            button.first.click()
            woke = True

        # صبر کنیم تا اپ بالا بیاید و اتصال websocket برقرار شود
        page.wait_for_selector(
            'iframe[title="streamlitApp"], [data-testid="stApp"]',
            timeout=120_000,
        )
        page.wait_for_timeout(15_000)

        print(f"OK    {url}" + ("  (was sleeping, woken up)" if woke else ""))
        return True
    except Exception as e:
        print(f"FAIL  {url}  ->  {type(e).__name__}: {e}")
        return False
    finally:
        page.close()


def main():
    urls = load_urls()
    print(f"Pinging {len(urls)} apps...\n")
    failed = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url in urls:
            if not ping(browser, url):
                failed.append(url)
        browser.close()

    print(f"\nDone. {len(urls) - len(failed)}/{len(urls)} OK.")
    if failed:
        print("Failed:", *failed, sep="\n  ")
        sys.exit(1)


if __name__ == "__main__":
    main()
