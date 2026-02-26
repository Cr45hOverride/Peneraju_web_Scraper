# line 169 set delay for 5 seconds
import requests
from bs4 import BeautifulSoup
import sys
import csv
import os
import time

def get_text_or_none(element):
    """Helper to extract stripped text if element exists."""
    if element:
        return element.get_text(strip=True)
    return "N/A"

def scrape_course(course_id, session, base_headers):
    url = f"https://peneraju.org/course-details?id={course_id}"
    try:
        response = session.get(url, headers=base_headers, timeout=10)
        if response.status_code != 200:
            print(f"[-] ID {course_id}: HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if page has content (sometimes ID exists but page is empty/redirect)
        title_tag = soup.select_one('h5.card-title')
        if not title_tag:
            print(f"[-] ID {course_id}: No course found (might be blocked/captcha or empty)")
            return None

        data = {}
        data['ID'] = str(course_id)
        
        # 1. Course Name
        if title_tag:
            # Get text only from the h5 itself, ignoring children
            course_name = title_tag.find(string=True, recursive=False)
            if course_name:
                data['Course Name'] = course_name.strip()
            else:
                data['Course Name'] = title_tag.get_text(strip=True)
        else:
            data['Course Name'] = "N/A"

        # Helper to find values based on labels
        def find_value_by_label(label_text):
            # Try type A: .label -> .value
            label_div = soup.find('div', class_='label', string=lambda t: t and label_text.lower() in t.lower())
            if label_div:
                value_div = label_div.find_next_sibling('div', class_='value')
                if value_div:
                    return value_div.get_text(strip=True)
            
            # Try type B: p text -> p next sibling
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
        # The icon for Web has specific classes 'text-2xl' unlike the one used for Method
        icon_web = soup.select_one('.ti-device-desktop.text-2xl')
        if icon_web:
            # The link is usually in a sibling span following the icon
            link = icon_web.find_next('a')
            if link:
                 data['Web'] = link.get('href', "N/A").strip()
            else:
                data['Web'] = "N/A"
        else:
            data['Web'] = "N/A"
            
        print(f"[+] ID {course_id}: Found '{data['Course Name']}'")
        return data

    except Exception as e:
        print(f"[-] ID {course_id}: Error - {e}")
        return None

def main():
    print("--- Peneraju Course Scraper ---")
    try:
        start_id = int(input("Enter Start ID: "))
        end_id = int(input("Enter End ID: "))
    except ValueError:
        print("Error: IDs must be integers.")
        return
    
    # Prompt for Cookie to bypass captcha
    print("\n[!] If you are hitting CAPTCHA blocks:")
    print("1. Go to https://peneraju.org in your browser.")
    print("2. Solve the CAPTCHA manually.")
    print("3. Open Developer Tools (F12) -> Application -> Cookies.")
    print("4. Copy the entire 'Cookie' value (or just PHPSESSID=...).")
    cookie_input = input("Enter Cookie String (Press Enter to skip): ").strip()

    # Determine step direction
    step = 1 if start_id <= end_id else -1
    # Adjust range to be inclusive of end_id
    id_range = range(start_id, end_id + step, step)

    fieldnames = ['ID', 'Course Name', 'Method', 'Duration', 'ALTI Name', 'Issuer', 'Phone', 'Email', 'Web']
    output_file = "output.csv"
    
    # Check if file exists to decide whether to write header
    file_exists = os.path.isfile(output_file)

    # Setup Session and Headers
    session = requests.Session()
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Referer': 'https://peneraju.org/',
        'Upgrade-Insecure-Requests': '1',
        'Connection': 'keep-alive'
    }
    
    if cookie_input:
        headers['Cookie'] = cookie_input

    # Use buffering=1 for line-buffered writing; 'a' for append
    with open(output_file, "a", encoding="utf-8", newline='', buffering=1) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for current_id in id_range:
            info = scrape_course(current_id, session, headers)
            if info:
                writer.writerow(info)
            # Delay to avoid rate limiting
            time.sleep(15)
    
    print("\nDone! Results saved to output.csv")

if __name__ == "__main__":
    main()
