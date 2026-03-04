from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True) # Pakai headless=True buat di server
    page = browser.new_page()
    page.goto("https://www.google.com")
    print("Berhasil akses:", page.title())
    browser.close()
