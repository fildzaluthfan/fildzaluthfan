from io import BytesIO
from pathlib import Path

from PIL import Image, ImageChops
from playwright.sync_api import sync_playwright

assets = Path("assets").resolve()
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(channel="chrome", args=["--no-sandbox"])
    for theme in ("light", "dark"):
        page = browser.new_page(viewport={"width": 850, "height": 360},
                                device_scale_factor=2, color_scheme=theme, reduced_motion="no-preference")
        page.goto((assets / "contribution-skyline.svg").as_uri())
        page.evaluate("document.getAnimations().forEach(a => a.pause())")
        frames = []
        duration_ms = int(page.locator(".grid").evaluate(
            "grid => grid.getAnimations()[0].effect.getTiming().duration"))
        # Include the last week's stagger before holding the completed skyline.
        duration_ms += round(page.evaluate("Math.max(...document.getAnimations().map(a => a.effect.getTiming().delay))"))
        frame_count = round(duration_ms * 60 / 1000)
        times = [round(i * duration_ms / frame_count) for i in range(frame_count + 1)]
        for ms in times:
            page.evaluate("""async ms => {
                for (const a of document.getAnimations()) a.currentTime = ms;
                await new Promise(resolve => requestAnimationFrame(() => requestAnimationFrame(resolve)));
            }""", ms)
            with Image.open(BytesIO(page.screenshot(scale="device"))) as sample:
                assert sample.size == (1700, 720)
                frame = sample.convert("RGB").resize((850, 360), Image.Resampling.LANCZOS)
                frames.append(frame)
        # Both the grid and the stats row must move in the actual exported frames.
        for crop in [(20, 80, 825, 240), (20, 295, 825, 354)]:
            assert ImageChops.difference(frames[0].crop(crop), frames[-1].crop(crop)).getbbox()
        frames[0].save(assets / f"skyline-{theme}.webp", save_all=True,
                       append_images=frames[1:], duration=[b - a for a, b in zip(times, times[1:])] + [1000],
                       loop=1, lossless=True, method=4)
        with Image.open(assets / f"skyline-{theme}.webp") as encoded:
            assert encoded.info["loop"] == 1
            for index, expected in [(0, frames[0]), (encoded.n_frames - 1, frames[-1])]:
                encoded.seek(index)
                assert not ImageChops.difference(encoded.convert("RGB"), expected).getbbox()
        page.close()
    browser.close()
