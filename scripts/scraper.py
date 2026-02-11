import os, sqlite3, time, subprocess
from playwright.sync_api import sync_playwright

# --- KONFIGURASI ---
#COLLECTION_URL = "https://www.tiktok.com/@ryuuzen_vv/collection/waifu-7599147794905058068"
COLLECTION_URL = "https://www.tiktok.com/@ryuuzen_vv/collection/waifu-7360103874431306501"

DB_PATH = "scripts/database.db"
DOWNLOAD_DIR = "downloads"

os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def check_video_exists(video_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM videos WHERE video_id = ?", (video_id,))
    exists = cursor.fetchone()
    conn.close()
    return exists

def save_to_db(video_id, title, filename):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO videos (video_id, title, filename) VALUES (?, ?, ?)", 
                   (video_id, title, filename))
    conn.commit()
    conn.close()

def download_with_ytdlp(url, video_id):
    filename = f"{video_id}.mp4"
    output_path = os.path.join(DOWNLOAD_DIR, filename)
    cookie_file = "tiktok_cookies.txt" 
    try:
        # Gunakan shell=True agar lebih stabil di Linux
        cmd = f'yt-dlp --cookies {cookie_file} --no-check-certificate -o "{output_path}" "{url}"'
        subprocess.run(cmd, shell=True, check=True)
        return filename
    except Exception as e:
        print(f"❌ Gagal download {video_id}: {e}")
        return None

def run_scraper():
    with sync_playwright() as p:     #headless=True
        browser = p.chromium.launch(headless=False, args=['--disable-blink-features=AutomationControlled', '--no-sandbox'])
        context = browser.new_context(user_agent="Mozilla/5.0 ...")
        page = context.new_page()
        page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        print(f"🚀 Membuka koleksi: {COLLECTION_URL}")
        page.goto(COLLECTION_URL, wait_until="networkidle", timeout=900000)

        processed_ids = set()
        consecutive_exists = 0  # Counter untuk stop jika ketemu video lama berturut-turut
        
        print("🔄 Memulai scanning & auto-download...")

        while True:
            # 1. Ambil semua link video yang saat ini ada di DOM
            links = page.query_selector_all('a[href*="/video/"]')
            current_batch_found = 0

            for link in links:
                href = link.get_attribute('href')
                if not href: continue
                
                url = href.split('?')[0]
                video_id = url.split('/')[-1]

                if video_id not in processed_ids:
                    processed_ids.add(video_id)
                    
                    if not check_video_exists(video_id):
                        print(f"📥 New Video Found: {video_id}. Downloading...")
                        fname = download_with_ytdlp(url, video_id)
                        if fname:
                            save_to_db(video_id, "TikTok Video", fname)
                            print(f"✅ Saved: {fname}")
                        consecutive_exists = 0 # Reset counter karena ada yang baru
                    else:
                        print(f"⏩ Skip: {video_id} (Already in DB)")
                        consecutive_exists += 1
                    
                    current_batch_found += 1

            # 2. Scroll ke bawah untuk memicu loading video baru (Lazy Load)
            page.evaluate("window.scrollBy(0, 1500)")
            time.sleep(3) # Tunggu render batch berikutnya

            # 3. Logika Berhenti (Threshold)
            # Jika dalam 3 kali scroll tidak nemu video baru (semua sudah ada di DB)
            if consecutive_exists > 15: 
                print("info: Sepertinya sudah mencapai batas video lama. Berhenti.")
                break
            
            # Pengaman agar tidak looping selamanya jika koleksi sangat besar
            if len(processed_ids) > 2000:
                break

        browser.close()

if __name__ == "__main__":
    run_scraper()
