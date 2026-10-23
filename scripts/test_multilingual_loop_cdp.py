import os
import time

# 1. Navigate to portal
goto_url("http://localhost:5173/")
wait_for_load()
time.sleep(2)

print("Page loaded. Testing 10-language voice assistant widget and hands-free loop...")

# 2. Open assistant widget
print("\n--- 1. Opening Assistant Widget ---")
js("document.querySelector('.sahaay-launcher-btn')?.click()")
time.sleep(1.5)

widget_open = js("Boolean(document.querySelector('.sahaay-widget-panel'))")
print("Widget Panel Open:", widget_open)

# 3. Check Language Options count and contents
print("\n--- 2. Checking 10-Language Dropdown ---")
lang_options = js("""(() => {
    const select = document.querySelector('.widget-lang-select');
    if (!select) return [];
    return Array.from(select.options).map(opt => ({ value: opt.value, label: opt.text }));
})()""")
print(f"Supported Languages count: {len(lang_options)}")
for opt in lang_options:
    print(f"  - [{opt['value']}] {opt['label']}")

# 4. Check Hands-free Loop Button
print("\n--- 3. Checking Hands-free Loop Button ---")
loop_btn_text = js("document.querySelector('.btn-loop-toggle')?.innerText")
is_active = js("Boolean(document.querySelector('.btn-loop-active'))")
print("Hands-free Loop button text:", loop_btn_text)
print("Hands-free Loop is active:", is_active)

# 5. Test Switching to Kannada ('kn')
print("\n--- 4. Switching Language to Kannada ('kn') ---")
js("""(() => {
    const select = document.querySelector('.widget-lang-select');
    if (select) {
        select.value = 'kn';
        select.dispatchEvent(new Event('change', { bubbles: true }));
    }
})()""")
time.sleep(2)

kannada_greeting = js("""(() => {
    const bubbles = document.querySelectorAll('.bubble-assistant .bubble-text');
    return bubbles.length ? bubbles[bubbles.length - 1].innerText : '';
})()""")
print("Kannada Greeting text:\n", kannada_greeting)

# 6. Test Switching to Hindi ('hi')
print("\n--- 5. Switching Language to Hindi ('hi') ---")
js("""(() => {
    const select = document.querySelector('.widget-lang-select');
    if (select) {
        select.value = 'hi';
        select.dispatchEvent(new Event('change', { bubbles: true }));
    }
})()""")
time.sleep(2)

hindi_greeting = js("""(() => {
    const bubbles = document.querySelectorAll('.bubble-assistant .bubble-text');
    return bubbles.length ? bubbles[bubbles.length - 1].innerText : '';
})()""")
print("Hindi Greeting text:\n", hindi_greeting)

# 7. Test Conversational Step in Widget (providing age '35 साल')
print("\n--- 6. Conversational Turn & Prompt Progression ---")
js("""(() => {
    const input = document.querySelector('.text-fallback-input');
    const form = document.querySelector('.text-fallback-form');
    if (input && form) {
        const nativeSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, 'value').set;
        nativeSetter.call(input, '35 साल');
        input.dispatchEvent(new Event('input', { bubbles: true }));
        const submitBtn = form.querySelector('.btn-submit');
        if (submitBtn) submitBtn.click();
    }
})()""")
time.sleep(3)

latest_assistant_msg = js("""(() => {
    const bubbles = document.querySelectorAll('.bubble-assistant .bubble-text');
    return bubbles.length ? bubbles[bubbles.length - 1].innerText : '';
})()""")
print("Assistant Next Question (Hindi):\n", latest_assistant_msg)

# Check Quick Answer Options rendered
quick_options = js("""(() => {
    return Array.from(document.querySelectorAll('.question-option-chip')).map(el => el.innerText);
})()""")
print("Rendered Quick Option Chips:", quick_options)

# 8. Test Clicking a Quick Option Chip ('किसान')
if quick_options:
    print("\n--- 7. Selecting Quick Option 'किसान' ---")
    js("""(() => {
        const chips = Array.from(document.querySelectorAll('.question-option-chip'));
        const farmerChip = chips.find(c => c.innerText.includes('किसान') || c.innerText.includes('Farmer'));
        if (farmerChip) farmerChip.click();
    })()""")
    time.sleep(3)
    
    after_chip_msg = js("""(() => {
        const bubbles = document.querySelectorAll('.bubble-assistant .bubble-text');
        return bubbles.length ? bubbles[bubbles.length - 1].innerText : '';
    })()""")
    print("Assistant Response after selecting Farmer:\n", after_chip_msg)

# 9. Test Loop Toggle interaction
print("\n--- 8. Testing Hands-free Loop Button Toggle ---")
js("document.querySelector('.btn-loop-toggle')?.click()")
time.sleep(0.5)
toggled_text = js("document.querySelector('.btn-loop-toggle')?.innerText")
toggled_active = js("Boolean(document.querySelector('.btn-loop-active'))")
print(f"After toggle: text='{toggled_text}', active={toggled_active}")

# Re-enable loop for active demo
js("document.querySelector('.btn-loop-toggle')?.click()")
time.sleep(0.5)
restored_text = js("document.querySelector('.btn-loop-toggle')?.innerText")
print(f"Restored loop: text='{restored_text}'")

# 10. Capture Full Screen Verification Snapshot
os.makedirs("docs/screenshots", exist_ok=True)
screenshot_path = "docs/screenshots/live_multilingual_loop_verified.png"
capture_screenshot(screenshot_path)
print(f"\nLive Screenshot captured at: {screenshot_path}")

print("\n=== MULTILINGUAL & HANDS-FREE LOOP TEST COMPLETED SUCCESSFULLY ===")
