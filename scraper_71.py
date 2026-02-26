# ==============================================================================
# PENERAJU SCRAPER SCRIPT
# ==============================================================================
# This script is designed to automatically visit web pages, read the information
# on those pages, and save the information into an Excel-friendly file (CSV).
# It uses a settings file called 'config.kml' to know which website to visit,
# what information to look for, and how many pages to scan.
# ==============================================================================

# ------------------------------------------------------------------------------
# 1. IMPORTING REQUIRED TOOLKITS
# ------------------------------------------------------------------------------
# These "import" statements bring in pre-built tools that help our script work.
import csv          # Helps us create and save an Excel-friendly output file
import os           # Helps us work with files and folders on your computer
import time         # Helps us add pauses/delays so we don't overwhelm the website
import random       # Helps us choose random numbers (for random delays)
import json         # Helps us read the 'config.kml' file which is written in JSON format
from bs4 import BeautifulSoup   # Helps us read and search through the website's text
from selenium import webdriver  # Helps us control the Chrome browser automatically
from selenium.webdriver.chrome.service import Service  # Connects Python to Chrome
from webdriver_manager.chrome import ChromeDriverManager # Automatically gets the right Chrome tool

# ------------------------------------------------------------------------------
# 2. DEFINING HELPER FUNCTIONS (Mini-tasks)
# ------------------------------------------------------------------------------

def load_config(config_file="config.kml"):
    """
    This function looks for your settings file (config.kml) and reads the instructions inside it.
    If it can't find the file or the file is broken, it will let you know.
    """
    try:
        # Open the settings file in "read" mode
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f) # Convert the file's text into an organized setting our script can use
    except Exception as e:
        # If something goes wrong, print an error message on the screen
        print(f"[-] Error loading {config_file}: {e}")
        return None

def parse_html(html_content, course_id, config):
    """
    This function takes the raw webpage code (HTML) and uses your settings to find
    the specific pieces of information you want (like 'Programme Name', 'Duration', etc.).
    """
    # Load the webpage code into BeautifulSoup, making it easy to search
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # First, check if the page actually has the right content by looking for a hidden title box
    title_tag = soup.select_one('h5.card-title')
    if not title_tag:
        # If we can't find a title, check if the website thinks we are a robot (CAPTCHA/Validation)
        if "Validation request" in str(soup):
            return "CAPTCHA" # Let the main script know we hit a robot-check
        return None # Let the main script know this page is empty/invalid

    # Create an empty dictionary (like a bucket) to store the data we find
    data = {}
    data['ID'] = str(course_id) # Save the current ID number first
    
    # Get the list of information we want to find from the settings file
    fields_to_extract = config.get('fields', [])
    
    # If the settings file uses an older format ('labels' instead of 'fields'), fix it
    if not fields_to_extract:
        old_labels = config.get('labels', [])
        for l in old_labels:
            fields_to_extract.append({"name": l, "extract": "generic_label"})
            
    # Now, go through each piece of information we want (like "Programme Name", "Phone")
    for field in fields_to_extract:
        label_name = field.get("name") # The name of the information (e.g., "Email")
        extract_type = field.get("extract", "generic_label") # The method we use to find it
        selector = field.get("selector") # The specific hidden code block to look inside
        
        found_val = "N/A" # Assume we won't find it at first
        
        # Method 1: finding straight text inside a specific code block
        if extract_type == "text" and selector:
            element = soup.select_one(selector)
            if element:
                t = element.find(string=True, recursive=False)
                found_val = t.strip() if t and t.strip() else element.get_text(strip=True)
                
        # Method 2: finding text slightly outside the specific code block
        elif extract_type == "parent_text" and selector:
            element = soup.select_one(selector)
            if element and element.parent:
                found_val = element.parent.get_text(strip=True)
                
        # Method 3: finding hidden links or attributes (like website addresses or mailto links)
        elif extract_type == "attribute" and selector:
            element = soup.select_one(selector)
            if element:
                attr = field.get("attribute", "href")
                val = element.get(attr, "")
                if val:
                    prefix = field.get("remove_prefix") # E.g., removing "mailto:" from an email link
                    if prefix:
                        val = val.replace(prefix, "")
                    found_val = val.strip()
                    
        # Method 4: finding a link directly after a specific block
        elif extract_type == "next_tag_attribute" and selector:
            element = soup.select_one(selector)
            if element:
                next_tag = field.get("next_tag", "a")
                link = element.find_next(next_tag)
                if link:
                    attr = field.get("attribute", "href")
                    found_val = link.get(attr, "N/A").strip()
                    
        # Method 5: finding data matching a standard label block on the website
        elif extract_type == "generic_label":
            # Search for a block with class 'label' that matches our label_name
            label_div = soup.find('div', class_='label', string=lambda t: t and label_name.lower() in t.lower())
            if label_div:
                value_div = label_div.find_next_sibling('div', class_='value')
                if value_div:
                    found_val = value_div.get_text(strip=True)
            
            # Search for a standard paragraph <p> tag
            if found_val == "N/A":
                label_p = soup.find(lambda tag: tag.name == 'p' and label_name.lower() == tag.get_text(strip=True).lower())
                if label_p:
                   value_p = label_p.find_next_sibling('p')
                   if value_p:
                       found_val = value_p.get_text(strip=True)
                       
            # Search for a <label> tag
            if found_val == "N/A":
                label_tag = soup.find('label', string=lambda t: t and label_name.lower() in t.lower())
                if label_tag:
                    value_span = label_tag.find_next_sibling('span')
                    if value_span:
                        found_val = value_span.get_text(strip=True)
                    else:
                        value_div = label_tag.find_next_sibling('div')
                        if value_div:
                            found_val = value_div.get_text(strip=True)
                            
        # Save whatever we found (or "N/A" if nothing) into our bucket
        data[label_name] = found_val

    # Return the bucket of data back to the main script
    return data

# ------------------------------------------------------------------------------
# 3. THE MAIN SCRIPT PROCESS
# ------------------------------------------------------------------------------
def main():
    # Print a welcome title on the black terminal screen
    print("--- Dynamic Configurable Selenium Scraper (App 71) ---")
    
    # Find exactly where this script is saved on your computer, 
    # so we know where to look for the 'config.kml' file
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.kml")
    
    # 1. READ THE CONFIGURATION
    config = load_config(config_path)
    if not config:
        # If there's no config file, script cannot run. Stop here.
        print("[-] Exiting because config.kml is missing or invalid.")
        return
        
    # Read settings like the webpage address, start ID, and end ID
    url_template = config.get("url_template", "https://peneraju.org/course-details?id={var_id}")
    base_url = config.get("base_url", "https://peneraju.org")
    fields = config.get("fields", [])
    if fields:
        labels = [f.get("name") for f in fields]
    else:
        labels = config.get("labels", [])
    
    start_id = config.get("start_id")
    end_id = config.get("end_id")

    # If the Start and End IDs aren't in the settings file, ask the user to type them in
    if start_id is None or end_id is None:
        try:
            start_id = int(input("Enter Start ID (e.g., 100): "))
            end_id = int(input("Enter End ID (e.g., 105): "))
        except ValueError:
            print("Error: IDs must be numbers only.")
            return

    # 2. OPEN GOOGLE CHROME
    print("\n[+] Launching Chrome...")
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    
    # This automatically downloads and uses the correct Chrome driver
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

    try:
        # Before we start scraping fast, go to the homepage slowly
        # This helps the website think we are a real human, not a robot
        print(f"\n[!] Navigating to {base_url}...")
        driver.get(base_url)
        
        # Display an instruction box for the user
        print("\n" + "="*60)
        print("ACTION REQUIRED:")
        print("1. Check the opened Chrome window.")
        print("2. If you see a 'Cloudflare' or 'Verify you are human' box, click to SOLVE IT.")
        print("3. Wait until you see the actual homepage loaded completely.")
        print("="*60)
        # The script will pause here until the user presses ENTER key
        input("Press ENTER here once the site is loaded and the security check is passed > ")

        # 3. PREPARE TO SAVE THE DATA
        # Figure out if we are counting upwards (e.g., 100 to 105) or backwards
        step = 1 if start_id <= end_id else -1
        id_range = range(start_id, end_id + step, step)

        # Create the column headers for our Excel/CSV file (e.g., ID, Programme Name, Email)
        fieldnames = ['ID'] + labels
        output_file = os.path.join(script_dir, "output.csv")
        file_exists = os.path.isfile(output_file)

        # Open the 'output.csv' file in "append" mode (so we don't erase old data)
        with open(output_file, "a", encoding="utf-8", newline='', buffering=1) as f:
            
            # Make sure we don't have duplicate headers (like having two 'Phone' columns)
            unique_fieldnames = []
            for field in fieldnames:
                if field not in unique_fieldnames:
                    unique_fieldnames.append(field)
                    
            # Setup our "writer" whose job is to put data nicely into the file columns
            writer = csv.DictWriter(f, fieldnames=unique_fieldnames)
            
            # If the CSV file is brand new, write the header row at the very top
            if not file_exists:
                writer.writeheader()
            
            # 4. START VISITING EACH PAGE
            for current_id in id_range:
                # Replace the '{var_id}' in the link with our current number (e.g., 100, 101...)
                url = url_template.replace("{var_id}", str(current_id))
                try:
                    # Tell Chrome to go to the page
                    driver.get(url)
                    time.sleep(2) # Give it 2 seconds to load
                    
                    # Grab everything written on the page
                    html = driver.page_source
                    
                    # Send this raw page to our helper function to extract only the good stuff
                    result = parse_html(html, current_id, config)
                    
                    # Sometimes the website randomly throws up another robot check
                    if result == "CAPTCHA":
                        print(f"[-] ID {current_id}: Hit a security check (CAPTCHA)!")
                        print("    Please look at Chrome and solve it.")
                        input("    Press ENTER here to continue after you solved it > ")
                        # Now grab the page again since we solved the problem
                        result = parse_html(driver.page_source, current_id, config)
                    
                    # If we found real data
                    if result and result != "CAPTCHA":
                        # Find a nice name to display on the screen (so we know it worked)
                        display_name = result.get('Programme Name', result.get('Course Name', result.get(labels[0] if labels else 'ID', 'Found')))
                        print(f"[+] ID {current_id}: '{display_name}'")
                        
                        # Tell our writer to save this data as a new row in the CSV file
                        writer.writerow(result)
                    else:
                        # If page was empty or broken
                        print(f"[-] ID {current_id}: No info found")

                except Exception as e:
                    # If something breaks (like internet connection lost)
                    print(f"[-] ID {current_id}: Error - {e}")
                
                # IMPORTANT: Wait random amount of time (5 to 10 seconds) before going to the next page
                # This makes the script act like a slow human, keeping us from getting banned!
                sleep_time = random.uniform(5, 10)
                time.sleep(sleep_time)

    except KeyboardInterrupt:
        # If the user presses "Ctrl+C", stop things safely
        print("\nStopped by user.")
    finally:
        # When all IDs are done (or if an error happens), close Chrome to clean up
        print("[+] Closing browser...")
        driver.quit()
        print("Done. Check the output.csv file for your data.")

# Set up the script to automatically run the 'main()' function when opened
if __name__ == "__main__":
    main()
