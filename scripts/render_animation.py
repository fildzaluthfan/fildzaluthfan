from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

assets = Path("assets").resolve()
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", args=["--no-sandbox"])
    for theme in ("light", "dark"):
        page = browser.new_page(viewport={"width": 850, "height": 360},
                                color_scheme=theme, reduced_motion="no-preference")
        page.goto((assets / "contribution-skyline.svg").as_uri())
        page.evaluate("document.getAnimations().forEach(a => a.pause())")
        frames = []
        for ms in range(0, 12000, 100):
            page.evaluate("""async ms => {
                for (const a of document.getAnimations()) a.currentTime = ms;
                await new Promise(requestAnimationFrame);
            }""", ms)
            frames.append(Image.open(BytesIO(page.screenshot())).convert("RGB"))
        # Both the grid and the stats row must move in the actual exported frames.
        for crop in [(20, 80, 825, 240), (20, 295, 825, 354)]:
            assert ImageChops.difference(frames[0].crop(crop), frames[60].crop(crop)).getbbox()
        frames[0].save(assets / f"skyline-{theme}.webp", save_all=True,
                       append_images=frames[1:], duration=100, loop=0, lossless=True, method=4)
        page.close()
    browser.close()
