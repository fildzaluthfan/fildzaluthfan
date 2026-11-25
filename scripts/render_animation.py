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
        duration_ms = int(page.locator(".grid").evaluate(
            "grid => grid.getAnimations()[0].effect.getTiming().duration"))
        frame_count = round(duration_ms * 30 / 1000)
        times = [round(i * duration_ms / frame_count) for i in range(frame_count + 1)]
        for ms in times[:-1]:
            page.evaluate("""async ms => {
                for (const a of document.getAnimations()) a.currentTime = ms;
                await new Promise(requestAnimationFrame);
            }""", ms)
            frames.append(Image.open(BytesIO(page.screenshot())).convert("RGB"))
        # Both the grid and the stats row must move in the actual exported frames.
        for crop in [(20, 80, 825, 240), (20, 295, 825, 354)]:
            assert ImageChops.difference(frames[0].crop(crop), frames[frame_count // 2].crop(crop)).getbbox()
        frames[0].save(assets / f"skyline-{theme}.webp", save_all=True,
                       append_images=frames[1:], duration=[b - a for a, b in zip(times, times[1:])],
                       loop=0, quality=88, method=4)
        page.close()
    browser.close()
