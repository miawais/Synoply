import csv
import time
from collections import defaultdict
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime
import tkinter as tk
from tkinter import filedialog

def is_today(timestamp_str):
    # New format: "10:06 PM, 10/14/2024"
    try:
        message_date = datetime.strptime(timestamp_str, "%I:%M %p, %m/%d/%Y").date()
        return message_date == datetime.today().date()
    except ValueError:
        print(f"Error parsing timestamp: {timestamp_str}")
        return False

class WhatsAppScraper:
    def __init__(self):
        self.chrome_options = Options()
        self.chrome_options.add_argument("--no-sandbox")
        self.chrome_options.add_argument("--disable-dev-shm-usage")
        self.chrome_options.add_argument("--start-maximized")
        self.contact_name = ''

        print("Starting WebDriver...")
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=self.chrome_options)
            self.driver.get('https://web.whatsapp.com')
            self.action = ActionChains(self.driver)

            print("Please scan the QR code to log in to WhatsApp Web.")
            WebDriverWait(self.driver, 120).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'div[role="textbox"]'))
            )
            print("WhatsApp Web is loaded successfully.")
        except Exception as e:
            print(f"Error initializing WebDriver: {e}")
            if hasattr(self, 'driver'):
                self.driver.quit()
            exit(1)

    def __scrollToView(self, stop_text):
        while True:
            try:
                element = self.driver.find_element(By.XPATH, f"//span[@class='_ao3e' and contains(text(),'{stop_text}')]")
                if element.is_displayed():
                    print("Element found!")
                    break
            except:
                pass
            ActionChains(self.driver).send_keys(Keys.PAGE_UP).perform()
            time.sleep(2)
        print(f"Scrolled up until the text '{stop_text}' was found.")

    def get_sender_name(self, message):
        try:
            name_element = message.find_element(By.XPATH, './/span[contains(@class, "_ao3e")]')
            return name_element.text
        except:
            return None

    def scrape_whatsapp_chat(self, chat_name, senders):
        complete_chat = []
        print(f"Starting scraping for chat: {chat_name}")

        try:
            search_box = WebDriverWait(self.driver, 20).until(
                EC.presence_of_element_located(
                    (By.XPATH, '//div[@contenteditable="true"][@data-tab="3"]'))
            )
            search_box.click()
            search_box.send_keys(chat_name)
            time.sleep(3)

            try:
                groups_button = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, '//button[.//div[text()="Groups"]]'))
                )
                groups_button.click()
                print("Groups button clicked.")
                time.sleep(3)

                chat = WebDriverWait(self.driver, 20).until(
                    EC.presence_of_element_located((By.XPATH, f'//span[@title="{chat_name}"]'))
                )
                chat.click()
                print(f"Chat '{chat_name}' selected.")
            except Exception as e:
                print(f"Error: {e}")
                return

            time.sleep(3)
            stop_text = 'YESTERDAY'
            self.__scrollToView(stop_text)  # Scroll to find 'YESTERDAY'

            print("Extracting messages...")
            messages = self.driver.find_elements(
                By.XPATH, '//div[contains(@class, "message-in") or contains(@class, "message-out")]')

            for idx, message in enumerate(messages, start=1):
                try:
                    text_elements = message.find_elements(
                        By.XPATH, './/span[@class="_ao3e selectable-text copyable-text"]//span')

                    if text_elements:
                        text = " ".join([element.text for element in text_elements])
                        timestamp_element = message.find_element(By.XPATH, './/div[@data-pre-plain-text]')
                        timestamp_full = timestamp_element.get_attribute('data-pre-plain-text')
                        timestamp = timestamp_full.split(']')[0].strip('[')

                        contact_name = self.get_sender_name(message)  # Get sender name

                        # Check if the message is from today
                        if is_today(timestamp):
                            complete_chat.append(text)
                        else:
                            print(f"Skipping message from {timestamp} as it's not from today")
                    else:
                        print(f"No text found in message {idx}")

                except Exception as e:
                    print(f"Error extracting message {idx}: {e}")
                    continue

            # Open the file in write mode
            with open('whatsapp_chat.txt', 'w', encoding='utf-8') as file:
                # Write each string in the data list to the file
                for msg in complete_chat:
                    file.write(msg + '\n')  # Adding a newline character after each line

            print("Chat has been saved to whatsapp_chat.txt")
            print(f"Scraping completed and saved for chat: {chat_name}")

        except Exception as e:
            print(f"An error occurred while scraping chat {chat_name}: {e}")

    def close(self):
        print("Closing WebDriver...")
        if hasattr(self, 'driver'):
            self.driver.quit()
        print("WebDriver closed.")

# Main function for starting the scraping process
def start_scraping_for_meetings_and_sales(senders):
    scraper = WhatsAppScraper()
    chat_names = ["Nov27"]

    for chat_name in chat_names:
        scraper.scrape_whatsapp_chat(chat_name, senders)
        
    print("Data processing and saving complete.")

# GUI for selecting files
def open_file_dialog():
    root = tk.Tk()
    root.withdraw()
    return filedialog.askopenfilename()

def save_file_dialog():
    root = tk.Tk()
    root.withdraw()
    return filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])

def main():
    senders = ["+44 7440 443324", "+44 7888 318045"]  # Add the list of contacts that send "NEW SALE" messages
    start_scraping_for_meetings_and_sales(senders)

if __name__ == "__main__":
    main()
