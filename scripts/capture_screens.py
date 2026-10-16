"""Capture the app screenshots for Figures 2-5 of the Part 3 report (phone-sized, 2x resolution).

    (start the API on :8000 and the web app on :8081 first, e.g. .\\start.ps1)
    python scripts/capture_screens.py            -> docs/exemplar/figures/*.png

Drives the real web app with Playwright using the installed Microsoft Edge (channel "msedge"), so no browser
download is needed. Uses the watermarked example CV EXAMPLE_CV_SP15.pdf.
"""

import os
import sys

from playwright.sync_api import sync_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "docs", "exemplar", "figures")
CV = os.path.join(ROOT, "profiles", "cvs", "EXAMPLE_CV_SP15.pdf")
URL = os.environ.get("SKILLPATH_APP_URL", "http://localhost:8081")


def main():
    os.makedirs(OUT, exist_ok=True)
    with sync_playwright() as pw:
        browser = pw.chromium.launch(channel="msedge", headless=True)
        page = browser.new_context(viewport={"width": 390, "height": 844}, device_scale_factor=2).new_page()
        shot = lambda name: page.screenshot(path=os.path.join(OUT, name)) or print("saved", name)
        page.goto(URL)
        page.get_by_text("Find your next skill").first.wait_for(timeout=60000)
        shot("fig1_welcome.png")

        page.get_by_role("checkbox", name="I understand what SkillPath stores and I agree to take part.").click()
        page.get_by_role("checkbox", name="I confirm that I am 18 years or older.").click()
        page.get_by_role("button", name="Start").click()

        page.get_by_text("Start with your CV").wait_for(timeout=30000)
        with page.expect_file_chooser() as fc:
            page.get_by_role("button", name="Upload your CV").click()
        fc.value.set_files(CV)
        page.get_by_text("Untick any that are not right").wait_for(timeout=90000)
        page.wait_for_timeout(500)
        shot("fig2_profile_cv.png")

        page.get_by_role("radio").nth(1).click()  # "I know the basics"
        page.get_by_role("button", name="Find my next skill").click()
        page.get_by_text("Recommended for you").wait_for(timeout=30000)
        page.wait_for_timeout(800)
        shot("fig3a_recommendation.png")
        page.get_by_role("button", name="What's missing?", exact=False).first.click()
        page.get_by_text("Why this skill?").first.click()
        page.wait_for_timeout(500)
        page.get_by_text("What's missing?").first.scroll_into_view_if_needed()
        page.wait_for_timeout(300)
        shot("fig3b_transparency.png")

        page.get_by_role("button", name="Accept and start").click()
        page.get_by_role("button", name="I completed this").wait_for(timeout=30000)
        page.wait_for_timeout(500)
        shot("fig4_pathway.png")
        for _ in range(3):
            page.get_by_role("button", name="I completed this").click()
            page.wait_for_timeout(700)
        page.get_by_role("tab", name="Progress").click()
        page.get_by_text("Milestones").wait_for(timeout=30000)
        page.wait_for_timeout(500)
        shot("fig5_progress.png")
        page.get_by_role("tab", name="Home").click()
        page.get_by_text("Welcome back").wait_for(timeout=30000)
        page.wait_for_timeout(500)
        shot("fig_home.png")
        page.get_by_role("tab", name="Settings").click()
        page.get_by_text("Delete my data").first.wait_for(timeout=30000)
        shot("fig_settings.png")
        browser.close()


if __name__ == "__main__":
    sys.exit(main())
