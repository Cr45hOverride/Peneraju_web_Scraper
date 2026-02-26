import csv
import os
import time
import random
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager

def get_text_or_none(element):
    """Helper to extract stripped text if element exists."""
    if element:
        return element.get_text(strip=True)
    return "N/A"

def parse_html(html_content, course_id):
    """Parses the HTML content using BeautifulSoup (reuses V2 logic)."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Check if page has content
    title_tag = soup.select_one('h5.card-title')
    if not title_tag:
        # Check for CAPTCHA specific text if possible, or just assume empty
        if "Validation request" in str(soup):
            return "CAPTCHA"
        return None

    data = {}
    data['ID'] = str(course_id)
    
    # 1. Course Name
    if title_tag:
        course_name = title_tag.find(string=True, recursive=False)
        if course_name:
            data['Course Name'] = course_name.strip()
        else:
            data['Course Name'] = title_tag.get_text(strip=True)
    else:
        data['Course Name'] = "N/A"

    # Helper to find values based on labels
    def find_value_by_label(label_text):
        label_div = soup.find('div', class_='label', string=lambda t: t and label_text.lower() in t.lower())
        if label_div:
            value_div = label_div.find_next_sibling('div', class_='value')
            if value_div:
                return value_div.get_text(strip=True)
        
        label_p = soup.find(lambda tag: tag.name == 'p' and label_text.lower() == tag.get_text(strip=True).lower())
        if label_p:
           value_p = label_p.find_next_sibling('p')
           if value_p:
               return value_p.get_text(strip=True)
        return "N/A"

    data['Method'] = find_value_by_label("Method")
    data['Duration'] = find_value_by_label("Duration")
    data['ALTI Name'] = find_value_by_label("ALTI Name")
    
    # 5. Issuer
    label_issuer = soup.find('label', string=lambda t: t and "Issuer" in t)
    if label_issuer:
        issuer_span = label_issuer.find_next_sibling('span')
        if issuer_span:
            data['Issuer'] = issuer_span.get_text(strip=True)
        else:
             data['Issuer'] = "N/A"
    else:
        data['Issuer'] = "N/A"

    # 6. Phone
    icon_phone = soup.select_one('.ti-headset')
    if icon_phone:
        parent = icon_phone.parent
        if parent:
            data['Phone'] = parent.get_text(strip=True)
    else:
        data['Phone'] = "N/A"

    # 7. Email
    email_link = soup.select_one('a[href^="mailto:"]')
    if email_link:
        data['Email'] = email_link['href'].replace('mailto:', '').strip()
    else:
        data['Email'] = "N/A"

    # 8. Web
    icon_web = soup.select_one('.ti-device-desktop.text-2xl')
    if icon_web:
        link = icon_web.find_next('a')
        if link:
             data['Web'] = link.get('href', "N/A").strip()
        else:
            data['Web'] = "N/A"
    else:
        data['Web'] = "N/A"
        
    return data

def main():
    print("--- Peneraju Selenium Scraper (V4) ---")
    try:
        start_id = int(input("Enter Start ID: "))
        end_id = int(input("Enter End ID: "))
    except ValueError:
        print("Error: IDs must be integers.")
        return

    print("\n[+] Launching Chrome...")
    options = webdriver.ChromeOptions()
    # options.add_argument("--headless") # Commented out so user can see/solve captcha
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # 1. Open Base URL so user can solve CAPTCHA
        print("\n[!] Navigating to https://peneraju.org...")
        driver.get("https://peneraju.org")
        
        print("\n" + "="*60)
        print("ACTION REQUIRED:")
        print("1. Check the opened Chrome window.")
        print("2. If you see a Cloudflare/CAPTCHA challenge, SOLVE IT manually.")
        print("3. Wait until you see the actual homepage.")
        print("="*60)
        input("Press ENTER here once the site is loaded and CAPTCHA is solved > ")

        step = 1 if start_id <= end_id else -1
        id_range = range(start_id, end_id + step, step)

        fieldnames = ['ID', 'Course Name', 'Method', 'Duration', 'ALTI Name', 'Issuer', 'Phone', 'Email', 'Web']
        output_file = "output.csv"
        file_exists = os.path.isfile(output_file)

        with open(output_file, "a", encoding="utf-8", newline='', buffering=1) as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            
            for current_id in id_range:
                url = f"https://peneraju.org/course-details?id={current_id}"
                try:
                    driver.get(url)
                    # Small wait for render
                    time.sleep(2) 
                    
                    html = driver.page_source
                    result = parse_html(html, current_id)
                    
                    if result == "CAPTCHA":
                        print(f"[-] ID {current_id}: Hit CAPTCHA again!")
                        print("    Please solve it in the browser window.")
                        input("    Press ENTER to continue after solving > ")
                        # Retry logic could go here, but for now just move on or retry once
                        result = parse_html(driver.page_source, current_id)
                    
                    if result and result != "CAPTCHA":
                        print(f"[+] ID {current_id}: Found '{result['Course Name']}'")
                        writer.writerow(result)
                    else:
                        print(f"[-] ID {current_id}: No info found")

                except Exception as e:
                    print(f"[-] ID {current_id}: Error - {e}")
                
                # Random delay to look human
                sleep_time = random.uniform(5, 10)
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        print("\nStopped by user.")
    finally:
        print("[+] Closing browser...")
        driver.quit()
        print("Done.")

if __name__ == "__main__":
    main()
