# Peneraju_web_Scraper
This script is designed to automatically visit web pages, read the information  on those pages, and save the information into an Excel-friendly file (CSV).  It uses a settings file called 'config.kml' to know which website to visit,  what information to look for, and how many pages to scan.

# Peneraju Web Scraper - User Guide

This guide is designed for individuals with little to no IT experience. It explains exactly what this script does, what you need to have to make it work, and the step-by-step process to run it on your computer.

---

## 📅 What is this tool?
The **Peneraju Web Scraper** (`scraper_71.py`) is an automated program. It acts as an invisible human helper that:
1. Opens up a web browser automatically.
2. Goes to multiple specific pages on a website (like courses numbered from 100 to 105).
3. Reads important information off the screen (like Programme Name, Duration, and Email).
4. Copies that information and organizes it neatly into a spreadsheet file (`output.csv`).

Instead of you sitting for hours copying and pasting data, this tool does it automatically for you and takes breaks in between (so the website doesn't block it).

---

## 🛠️ What do you need before starting?
Before you run this tool, ensure your computer has the following things prepared:

1. **Python Installed**: This script is written in a language called Python. You must have Python installed. If you don't, go to [python.org](https://www.python.org/) and download it.
2. **Google Chrome**: The script uses Google Chrome to look at web pages. Make sure Chrome is installed on your computer.
3. **The Files**: You must have two files sitting in the same folder:
   - `scraper_71.py` (The script itself).
   - `config.kml` (The settings file that tells the script what to look for).

---

## ⚙️ How to change the settings (`config.kml`)
The `config.kml` file is the instruction manual for the tool. You can open it using any text editor (like **Notepad**). 

Here is what it looks like inside:
```json
{
    "base_url": "https://peneraju.org",
    "url_template": "https://peneraju.org/course-details?id={var_id}",
    "start_id": 100,
    "end_id": 105,
    "fields": [
        ...
```

### Things you can safely change:
- `"start_id"`: The first page number you want to look at. For example, if you want to start from course number 100, set this to `100`.
- `"end_id"`: The last page number you want to look at. For example, if you want to stop at course number 105, set this to `105`.
- `"fields"`: This tells the script what pieces of information you want. *(If you are not comfortable reading code, it's best to leave this section alone).*

Make sure you **Save** the file if you make any changes!

---

## 🚀 How to run the tool

### Step 1: Open the command window
1. Open the folder containing the files (`scraper_71.py` and `config.kml`).
2. If you are using Windows, click on the address bar at the top of the folder window.
3. Type `cmd` and press **Enter**. This will open a black window (the Command Prompt).

### Step 2: Install toolkits (Only needed the first time)
The bot needs some extra tools to operate the mouse and keyboard. In the black window, type the following and press **Enter**:
```bash
pip install beautifulsoup4 selenium webdriver-manager
```
*Wait for the text to finish scrolling before moving on.*

### Step 3: Start the scraper
In the black window, type:
```bash
python scraper_71.py
```
Press **Enter**. 

---

## 🚦 What happens next? (The Scraping Process)

Once you press enter, the script will start giving you updates on the black screen. Here is what will happen:

1. **Chrome will open up by itself**. The tool will open Google Chrome and navigate to the main website homepage.
2. **You might need to help it!** Many websites try to block robots. If the website asks "Are you human?" or shows a puzzle (called a CAPTCHA):
   - Simply click the box or solve the puzzle using your mouse.
   - Wait until the actual website finishes loading completely.
   - Go back to your black text window, and **Press ENTER** to let the script know you fixed it.
3. **The tool works its magic.** The tool will now navigate to page 100, get data, navigate to page 101, etc.
   - *Note: The tool waits between 5 to 10 seconds between each page. This makes it look like a human reading a page slowly.*
4. **Completion.** Once it reaches the end number you set, it will close Google Chrome automatically and say "Done."

---

## 📂 Where is my data?
Once the script has finished or is stopped, go back to the folder where `scraper_71.py` is saved. 
You will see a newly created file called **`output.csv`**. 

- You can double-click `output.csv` to open it in **Microsoft Excel**.
- Every row contains data belonging to one webpage/ID.
- The columns will be neatly labeled with headers like `ID`, `Programme Name`, `Duration`, `Email`, etc.

**Important Note regarding `output.csv`**:
- The tool will never delete old data. If you run the tool again tomorrow, it will add the new data onto the *bottom* of your existing `output.csv` file. 
- If you want a fresh list, you should delete or rename the old `output.csv` file before running the tool again.

