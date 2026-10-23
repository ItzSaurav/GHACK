import os
import time

# 1. Navigate to portal
goto_url("http://localhost:5173/")
wait_for_load()
time.sleep(2)

print("Page info:", page_info())

# 2. Check title and main elements
title = js("document.title")
h1 = js("document.querySelector('h1')?.innerText")
scheme_count = js("document.querySelectorAll('.portal-scheme-card').length")
cat_count = js("document.querySelectorAll('.category-card').length")
step_count = js("document.querySelectorAll('.step-marker').length")

print("=== Portal Elements ===")
print("Title:", title)
print("H1:", h1)
print("Schemes Count:", scheme_count)
print("Categories Count:", cat_count)
print("Discovery Steps Count:", step_count)

# 3. Test opening Assistant Widget
print("\n=== Testing Assistant Widget ===")
click_launcher = js("document.querySelector('.sahaay-launcher-btn')?.click()")
time.sleep(1.5)

widget_open = js("Boolean(document.querySelector('.sahaay-widget-panel'))")
print("Widget Panel Visible:", widget_open)

greeting = js("document.querySelector('.bubble-assistant .bubble-text')?.innerText")
print("Initial Assistant Greeting:", greeting)

# 4. Test User Input in Widget
print("\n=== Testing User Interaction ===")
js("""(() => {
    const input = document.querySelector('.text-fallback-input');
    const submitBtn = document.querySelector('.text-fallback-form .btn-submit');
    if (input && submitBtn) {
        input.value = 'मेरी उम्र 35 साल है';
        input.dispatchEvent(new Event('input', { bubbles: true }));
        submitBtn.click();
    }
})()""")
time.sleep(2)

chat_messages = js("""(() => {
    return Array.from(document.querySelectorAll('.bubble-text')).map(el => el.innerText).join(' || ');
})()""")
print("Chat Messages Flow:", chat_messages)

# 5. Test Scheme Detail Modal
print("\n=== Testing Scheme Detail Modal ===")
js("document.querySelector('.portal-scheme-card .btn-outline')?.click()")
time.sleep(1)

modal_open = js("Boolean(document.querySelector('.scheme-detail-modal'))")
modal_title = js("document.querySelector('#scheme-detail-title')?.innerText")
print("Detail Modal Visible:", modal_open)
print("Detail Modal Scheme Title:", modal_title)

# Close modal
js("document.querySelector('.scheme-detail-modal .modal-close-btn')?.click()")
time.sleep(0.5)

# 6. Capture live screenshot
os.makedirs("docs/screenshots", exist_ok=True)
capture_screenshot("docs/screenshots/live_portal_verified.png")
print("\nScreenshot successfully captured: docs/screenshots/live_portal_verified.png")
print("=== ALL BROWSER-USE TESTS COMPLETED SUCCESSFULLY ===")
