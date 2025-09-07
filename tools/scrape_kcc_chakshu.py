import os
import asyncio
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright


BASE_URL = "https://kcc-chakshu.icar-web.com/4_answer_extract_major.php"
OUTPUT_DIR = Path(os.getenv("KCC_OUTPUT_DIR", "./downloads/kcc_chakshu"))
TIMEOUT_MS = int(os.getenv("KCC_TIMEOUT_MS", "30000"))


async def scrape():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(accept_downloads=True)
        page = await context.new_page()
        await page.goto(BASE_URL, timeout=TIMEOUT_MS)

        crop_select = page.locator("select#crop")
        disease_select = page.locator("select#pest")

        # The actual IDs/names may differ; adjust selectors after inspecting the DOM
        # Fallback generic selectors by label text if IDs not present
        if await crop_select.count() == 0:
            crop_select = page.locator("xpath=//label[contains(., 'Select Crop')]/following::select[1]")
        if await disease_select.count() == 0:
            disease_select = page.locator("xpath=//label[contains(., 'Select Pest') or contains(., 'Select Pest/Disease')]/following::select[1]")

        crop_options = await crop_select.locator("option").all()
        crops = []
        for opt in crop_options:
            value = await opt.get_attribute("value")
            label = await opt.inner_text()
            if not value or value.strip() == "" or label.strip().startswith("--"):
                continue
            crops.append((value.strip(), label.strip()))

        total_downloads = 0
        for crop_value, crop_label in crops:
            await crop_select.select_option(value=crop_value)
            # Wait for diseases to populate (if dynamic)
            await page.wait_for_timeout(500)

            disease_options = await disease_select.locator("option").all()
            diseases = []
            for opt in disease_options:
                value = await opt.get_attribute("value")
                label = await opt.inner_text()
                if not value or value.strip() == "" or label.strip().startswith("--"):
                    continue
                diseases.append((value.strip(), label.strip()))

            for disease_value, disease_label in diseases:
                await disease_select.select_option(value=disease_value)

                # Click the CSV download button/link; adjust selector to match actual DOM
                # Common patterns: a[href*='csv'], button:text('CSV'), etc.
                # We'll try a few fallbacks.
                download = None
                for selector in [
                    "a[href*='.csv']",
                    "a:has-text('CSV')",
                    "button:has-text('CSV')",
                    "text=Download CSV",
                ]:
                    try:
                        async with page.expect_download(timeout=TIMEOUT_MS) as dl_info:
                            await page.locator(selector).first.click()
                        download = await dl_info.value
                        break
                    except Exception:
                        continue

                if not download:
                    print(f"[WARN] No CSV download control found for {crop_label} - {disease_label}")
                    continue

                # Save file with safe name
                safe_crop = "_".join(crop_label.split())
                safe_disease = "_".join(disease_label.split())
                timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
                filename = f"{safe_crop}__{safe_disease}__{timestamp}.csv"
                dest = OUTPUT_DIR / filename
                try:
                    await download.save_as(dest)
                    total_downloads += 1
                    print(f"[OK] Saved {dest}")
                except Exception as e:
                    print(f"[ERROR] Failed to save download for {crop_label} - {disease_label}: {e}")

        await context.close()
        await browser.close()
        print(f"Completed. Total CSVs downloaded: {total_downloads}")


if __name__ == "__main__":
    asyncio.run(scrape())


