import requests
from bs4 import BeautifulSoup
import sys
import csv

def get_text_or_none(element):
    """Helper to extract stripped text if element exists."""
    if element:
        return element.get_text(strip=True)
    return "N/A"

def scrape_course(course_id):
    url = f"https://peneraju.org/course-details?id={course_id}"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code != 200:
            print(f"[-] ID {course_id}: HTTP {response.status_code}")
            return None
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Check if page has content (sometimes ID exists but page is empty/redirect)
        title_tag = soup.select_one('h5.card-title')
        if not title_tag:
            print(f"[-] ID {course_id}: No course found (empty page)")
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

    # Determine step direction
    step = 1 if start_id <= end_id else -1
    # Adjust range to be inclusive of end_id
    id_range = range(start_id, end_id + step, step)

    fieldnames = ['ID', 'Course Name', 'Method', 'Duration', 'ALTI Name', 'Issuer', 'Phone', 'Email', 'Web']

    # Use buffering=1 for line-buffered writing so data is saved even if script stops
    with open("output.csv", "w", encoding="utf-8", newline='', buffering=1) as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        
        for current_id in id_range:
            info = scrape_course(current_id)
            if info:
                writer.writerow(info)
    
    print("\nDone! Results saved to output.csv")

if __name__ == "__main__":
    main()
