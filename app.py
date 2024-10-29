import csv
import time
import streamlit as st
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
from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Function to check if the timestamp is today's date
def is_today(timestamp_str):
    try:
        message_date = datetime.strptime(timestamp_str, "%I:%M %p, %m/%d/%Y").date()
        return message_date == datetime.today().date()
    except ValueError:
        print(f"Error parsing timestamp: {timestamp_str}")
        return False

# WhatsApp scraper class
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

    def scrape_whatsapp_chat(self, chat_name):
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
            self.__scrollToView(stop_text)

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

                        if is_today(timestamp):
                            complete_chat.append(text)
                        else:
                            print(f"Skipping message from {timestamp} as it's not from today")
                    else:
                        print(f"No text found in message {idx}")

                except Exception as e:
                    print(f"Error extracting message {idx}: {e}")
                    continue

            print("Chat extraction done and saved in memory. Starting summarization...")

            return complete_chat  # Return the collected chat messages

        except Exception as e:
            print(f"An error occurred while scraping chat {chat_name}: {e}")

    def close(self):
        print("Closing WebDriver...")
        if hasattr(self, 'driver'):
            self.driver.quit()
        print("WebDriver closed.")

# Function to summarize messages
def summarize_messages(messages):
    system_prompt = '''
    You are a helpful assistant that summarizes WhatsApp messages effectively.
    '''

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            ("user", "Message: {message}")
        ]
    )

    combined_messages = "\n".join(messages)

    llm = OllamaLLM(model="llama3.1", temperature=0.7)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    answer = chain.invoke({"message": combined_messages})
    return answer

# Streamlit app
def main():
    st.title("WhatsApp Chat Scraper and Summarizer")

    st.sidebar.header("Settings")
    chat_name = st.sidebar.text_input("Enter the chat name:", value="Nov27")
    submit_button = st.sidebar.button("Start Scraping")

    if submit_button:
        with st.spinner("Scraping the chat..."):
            scraper = WhatsAppScraper()
            messages = scraper.scrape_whatsapp_chat(chat_name)
            scraper.close()

            if messages:
                st.success("Chat extraction done!")
                st.write("Messages extracted:")
                for msg in messages:
                    st.write(f"- {msg}")

                st.write("Summarizing messages...")
                summary = summarize_messages(messages)
                st.success("Summarization complete!")
                st.write("Summary of messages:")
                st.write(summary)
            else:
                st.warning("No messages found or an error occurred during scraping.")

if __name__ == "__main__":
    main()
