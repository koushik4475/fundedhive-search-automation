import sys
import argparse
import os
import time

# Reconfigure stdout to support unicode emojis on Windows terminal
try:
    sys.stdout.reconfigure(encoding='utf-8')
except AttributeError:
    pass

import json
from concurrent.futures import ThreadPoolExecutor, as_completed
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from engines import SEARCH_ENGINES
from tqdm import tqdm

# === CONFIG ===
DEFAULT_QUERY = "FundedHive 1 minute payout OR 47 seconds OR $1000 compensation review"
DEFAULT_X_POST = "https://x.com/HyKoushik63455/status/2060435122684629268?s=20"

def get_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_window_size(1280, 960)
    return driver

def visit_x_post(url):
    print(f"\n🔍 Visiting X Post: {url}...")
    driver = None
    try:
        driver = get_driver(headless=True)
        driver.get(url)
        print("⏳ Waiting for X post to load (7 seconds)...")
        time.sleep(7)
        
        # Try to locate tweet text
        tweet_text = "Could not extract tweet text automatically."
        try:
            # Common selectors for tweet text on X
            selectors = [
                "[data-testid='tweetText']",
                "article [dir='auto']",
                "div.tweet-text"
            ]
            for selector in selectors:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                if elements:
                    tweet_text = "\n".join([el.text for el in elements if el.text])
                    if tweet_text.strip():
                        break
        except Exception as e:
            print(f"⚠️ Note on text extraction: {e}")

        # Save screenshot
        if not os.path.exists("results/screenshots"):
            os.makedirs("results/screenshots", exist_ok=True)
        
        screenshot_path = f"results/screenshots/x_post_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)
        print(f"📸 Captured X Post screenshot: {screenshot_path}")

        return {
            "URL": url,
            "Text": tweet_text,
            "Screenshot": screenshot_path,
            "Status": "Success"
        }
    except Exception as e:
        print(f"❌ Failed to visit X post: {e}")
        return {
            "URL": url,
            "Text": f"Error: {str(e)}",
            "Screenshot": None,
            "Status": "Failed"
        }
    finally:
        if driver:
            driver.quit()

def search_single(engine_name, base_url, query):
    driver = None
    try:
        driver = get_driver()
        url = base_url + query.replace(" ", "+")
        driver.get(url)
        time.sleep(4.5)  # Let results load
        
        screenshot_path = None
        if not os.path.exists("results/screenshots"):
            os.makedirs("results/screenshots", exist_ok=True)
        screenshot_path = f"results/screenshots/{engine_name.lower()}_{int(time.time())}.png"
        driver.save_screenshot(screenshot_path)

        return {
            "Engine": engine_name,
            "Search_URL": driver.current_url,
            "Page_Title": driver.title,
            "Screenshot": screenshot_path,
            "Status": "Success",
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "Error": ""
        }
    except Exception as e:
        return {
            "Engine": engine_name,
            "Search_URL": base_url + query.replace(" ", "+"),
            "Page_Title": "Failed to load",
            "Screenshot": None,
            "Status": "Failed",
            "Timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "Error": str(e)
        }
    finally:
        if driver:
            driver.quit()

def generate_html_report(x_result, search_results, output_path):
    print("📊 Generating beautiful HTML report...")
    
    # Process paths to make them relative to output report location (which is in results/)
    def make_relative(path):
        if not path:
            return "#"
        # Since report is in results/ and screenshots are in results/screenshots/
        # the relative path is screenshots/filename.png
        return path.replace("results/", "")

    x_ss = make_relative(x_result.get("Screenshot"))
    x_text_escaped = x_result.get("Text", "").replace("\n", "<br>")

    x_screenshot_html = ""
    if x_result.get("Screenshot"):
        x_screenshot_html = f"<div class='x-screenshot-container' onclick='openModal(\"{x_ss}\")'><img src='{x_ss}' alt='X Post Screenshot'></div>"
    else:
        x_screenshot_html = "<div class='card-screenshot-failed'>No screenshot captured</div>"

    cards_html = ""
    for r in search_results:
        ss_rel = make_relative(r.get("Screenshot"))
        status_badge = "success" if r.get("Status") == "Success" else "danger"
        
        screenshot_html = ""
        if r.get("Screenshot"):
            screenshot_html = f'''
            <div class="card-screenshot" onclick="openModal('{ss_rel}')">
                <img src="{ss_rel}" alt="{r['Engine']} Screenshot">
                <div class="screenshot-overlay">
                    <span>🔍 View Fullscreen</span>
                </div>
            </div>
            '''
        else:
            screenshot_html = f'''
            <div class="card-screenshot-failed">
                <span>❌ No Screenshot Available<br><small>{r.get("Error", "Unknown error")}</small></span>
            </div>
            '''

        cards_html += f'''
        <div class="engine-card">
            <div class="card-header">
                <div class="engine-name">{r['Engine']}</div>
                <span class="status-badge badge-{status_badge}">{r['Status']}</span>
            </div>
            <div class="card-body">
                <p class="card-title"><strong>Title:</strong> {r['Page_Title']}</p>
                <p class="card-url"><strong>URL:</strong> <a href="{r['Search_URL']}" target="_blank">{r['Search_URL']}</a></p>
                {screenshot_html}
                <div class="card-footer">
                    <span class="timestamp">🕒 {r['Timestamp']}</span>
                </div>
            </div>
        </div>
        '''

    html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FundedHive Search Automation Report</title>
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-color: #0b0f19;
            --card-bg: rgba(22, 28, 45, 0.6);
            --border-color: rgba(255, 255, 255, 0.08);
            --primary: #6366f1;
            --primary-hover: #4f46e5;
            --success: #10b981;
            --danger: #ef4444;
            --text-main: #f3f4f6;
            --text-muted: #9ca3af;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}

        body {{
            background-color: var(--bg-color);
            color: var(--text-main);
            font-family: 'Plus Jakarta Sans', sans-serif;
            line-height: 1.6;
            padding: 2rem 1.5rem;
            min-height: 100vh;
        }}

        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}

        header {{
            text-align: center;
            margin-bottom: 3rem;
            position: relative;
        }}

        header h1 {{
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, #a5b4fc, #6366f1);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 0.5rem;
        }}

        header p {{
            color: var(--text-muted);
            font-size: 1.1rem;
        }}

        /* X Post Section */
        .x-post-section {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            padding: 2rem;
            margin-bottom: 3rem;
            backdrop-filter: blur(12px);
            box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
        }}

        .x-post-grid {{
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 2rem;
        }}

        @media (max-width: 768px) {{
            .x-post-grid {{
                grid-template-columns: 1fr;
            }}
        }}

        .x-post-info h2 {{
            font-size: 1.5rem;
            margin-bottom: 1rem;
            color: #38bdf8; /* X blue/light blue */
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .x-post-url {{
            font-size: 0.9rem;
            margin-bottom: 1.5rem;
            word-break: break-all;
        }}

        .x-post-url a {{
            color: #38bdf8;
            text-decoration: none;
        }}

        .x-post-url a:hover {{
            text-decoration: underline;
        }}

        .tweet-content-box {{
            background: rgba(0, 0, 0, 0.2);
            border-left: 4px solid #38bdf8;
            padding: 1.2rem;
            border-radius: 4px 8px 8px 4px;
            font-style: italic;
            margin-bottom: 1.5rem;
            color: #e5e7eb;
        }}

        .x-screenshot-container {{
            border-radius: 12px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            cursor: pointer;
            position: relative;
        }}

        .x-screenshot-container img {{
            width: 100%;
            display: block;
            transition: transform 0.3s ease;
        }}

        .x-screenshot-container:hover img {{
            transform: scale(1.02);
        }}

        /* Search Results Section */
        .results-section h2 {{
            font-size: 1.8rem;
            font-weight: 600;
            margin-bottom: 1.5rem;
            border-left: 4px solid var(--primary);
            padding-left: 0.75rem;
        }}

        .results-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
        }}

        .engine-card {{
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 16px;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            backdrop-filter: blur(8px);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }}

        .engine-card:hover {{
            transform: translateY(-5px);
            border-color: rgba(99, 102, 241, 0.4);
            box-shadow: 0 10px 20px rgba(0, 0, 0, 0.2);
        }}

        .card-header {{
            padding: 1.25rem 1.5rem;
            border-bottom: 1px solid var(--border-color);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .engine-name {{
            font-weight: 600;
            font-size: 1.2rem;
        }}

        .status-badge {{
            font-size: 0.75rem;
            font-weight: 700;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            text-transform: uppercase;
        }}

        .badge-success {{
            background-color: rgba(16, 185, 129, 0.15);
            color: var(--success);
        }}

        .badge-danger {{
            background-color: rgba(239, 68, 68, 0.15);
            color: var(--danger);
        }}

        .card-body {{
            padding: 1.5rem;
            display: flex;
            flex-direction: column;
            flex-grow: 1;
        }}

        .card-title {{
            font-size: 0.95rem;
            margin-bottom: 0.5rem;
            color: var(--text-main);
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .card-url {{
            font-size: 0.85rem;
            margin-bottom: 1.25rem;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
        }}

        .card-url a {{
            color: var(--primary);
            text-decoration: none;
        }}

        .card-url a:hover {{
            text-decoration: underline;
        }}

        .card-screenshot {{
            border-radius: 8px;
            overflow: hidden;
            border: 1px solid var(--border-color);
            position: relative;
            cursor: pointer;
            margin-top: auto;
        }}

        .card-screenshot img {{
            width: 100%;
            height: 180px;
            object-fit: cover;
            display: block;
            transition: transform 0.3s ease;
        }}

        .card-screenshot:hover img {{
            transform: scale(1.05);
        }}

        .screenshot-overlay {{
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            align-items: center;
            justify-content: center;
            opacity: 0;
            transition: opacity 0.3s ease;
        }}

        .card-screenshot:hover .screenshot-overlay {{
            opacity: 1;
        }}

        .card-screenshot-failed {{
            height: 180px;
            background: rgba(0, 0, 0, 0.2);
            border: 1px dashed var(--border-color);
            border-radius: 8px;
            display: flex;
            align-items: center;
            justify-content: center;
            text-align: center;
            color: var(--text-muted);
            margin-top: auto;
        }}

        .card-footer {{
            margin-top: 1rem;
            padding-top: 0.75rem;
            border-top: 1px solid var(--border-color);
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        /* Fullscreen Modal */
        .modal {{
            display: none;
            position: fixed;
            z-index: 9999;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(5, 7, 12, 0.95);
            align-items: center;
            justify-content: center;
            padding: 20px;
        }}

        .modal-content {{
            max-width: 90%;
            max-height: 90%;
            border-radius: 8px;
            box-shadow: 0 0 30px rgba(0,0,0,0.5);
            border: 1px solid rgba(255,255,255,0.1);
        }}

        .modal-close {{
            position: absolute;
            top: 20px;
            right: 30px;
            color: #fff;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
            transition: color 0.2s;
        }}

        .modal-close:hover {{
            color: var(--primary);
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>FundedHive Search Automation Report</h1>
            <p>Verification & Multi-Engine Search Results for FundedHive Reviews</p>
        </header>

        <!-- X Post Section -->
        <section class="x-post-section">
            <div class="x-post-grid">
                <div class="x-post-info">
                    <h2>🐦 Verification target: X Post</h2>
                    <div class="x-post-url">
                        <strong>Source URL:</strong> <a href="{x_result['URL']}" target="_blank">{x_result['URL']}</a>
                    </div>
                    <div class="tweet-content-box">
                        {x_text_escaped}
                    </div>
                    <p style="color: var(--text-muted); font-size: 0.9rem;">
                        This X post from @HyKoushik63455 was automatically visited and parsed by the automation engine to correlate search engine indexation.
                    </p>
                </div>
                <div>
                    <strong>Captured Post Snapshot:</strong>
                    {x_screenshot_html}
                </div>
            </div>
        </section>

        <!-- Search Engines Grid -->
        <section class="results-section">
            <h2>Search Engine Indexation Grid</h2>
            <div class="results-grid">
                {cards_html}
            </div>
        </section>
    </div>

    <!-- Modal -->
    <div id="imageModal" class="modal" onclick="closeModal()">
        <span class="modal-close">&times;</span>
        <img class="modal-content" id="modalImg">
    </div>

    <script>
        function openModal(imgSrc) {{
            document.getElementById('modalImg').src = imgSrc;
            document.getElementById('imageModal').style.display = 'flex';
        }}

        function closeModal() {{
            document.getElementById('imageModal').style.display = 'none';
        }}
        
        // Close on ESC
        document.addEventListener('keydown', function(event) {{
            if (event.key === 'Escape') {{
                closeModal();
            }}
        }});
    </script>
</body>
</html>
'''
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)
    print(f"✨ HTML report successfully created at: {output_path}")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--query", type=str, default=DEFAULT_QUERY, help="Search query")
    parser.add_argument("--x-post", type=str, default=DEFAULT_X_POST, help="X Post URL to visit")
    parser.add_argument("--headless", action="store_true", default=True)
    args = parser.parse_args()

    print("🚀 FundedHive Multi-Search Automation Starting")
    print(f"Search Query: {args.query}")
    print(f"X Post URL  : {args.x_post}\n")

    # Step 1: Visit X Post
    x_result = visit_x_post(args.x_post)

    # Step 2: Run Search Engines in Parallel
    print("\n🔍 Launching Multi-Engine Searches...")
    search_results = []
    with ThreadPoolExecutor(max_workers=6) as executor:
        futures = [executor.submit(search_single, name, url, args.query) 
                  for name, url in SEARCH_ENGINES.items()]
        
        for future in tqdm(as_completed(futures), total=len(futures), desc="Searching"):
            search_results.append(future.result())

    # Step 3: Save results CSV
    os.makedirs("results", exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    df = pd.DataFrame(search_results)
    csv_path = f"results/fundedhive_search_{timestamp}.csv"
    df.to_csv(csv_path, index=False)
    print(f"\n✅ CSV saved to: {csv_path}")

    # Save X post metadata to json for completeness
    x_meta_path = f"results/x_post_metadata_{timestamp}.json"
    with open(x_meta_path, "w", encoding="utf-8") as f:
        json.dump(x_result, f, indent=4)

    # Step 4: Generate HTML Report
    report_path = "results/report.html"
    generate_html_report(x_result, search_results, report_path)

    print(f"\n🚀 ALL STEPS COMPLETED!")
    print(f"📄 HTML Report: {os.path.abspath(report_path)}")
    print(f"📊 CSV Data  : {os.path.abspath(csv_path)}")

if __name__ == "__main__":
    main()
