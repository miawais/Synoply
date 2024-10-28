from langchain_ollama import OllamaLLM
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.prompts import ChatPromptTemplate
import json

system_prompt = '''
You are a helpful assistant that summarizes WhatsApp messages effectively.
'''

prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system_prompt),
        ("user", "Message: {message}")
    ]
)

def generate_response(message, llm, temperature):
    llm = OllamaLLM(model=llm, temperature=temperature)
    output_parser = StrOutputParser()
    chain = prompt | llm | output_parser
    answer = chain.invoke({"message": message})
    return answer

def summarize_messages_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        messages = file.readlines()

    # Remove leading/trailing whitespace characters from each message
    messages = [message.strip() for message in messages if message.strip()]

    # Combine messages into a single string for summarization
    combined_messages = "\n".join(messages)

    # Generate summary
    response = generate_response(combined_messages, llm="llama3.1", temperature=0.7)
    return response

if __name__ == '__main__':
    # Path to the WhatsApp messages text file
    file_path = 'whatsapp_chat.txt'
    
    # Summarize messages
    summary = summarize_messages_from_file(file_path)
    print("Summary of messages:")
    print(summary)
