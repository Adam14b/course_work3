import os
import json
import requests

from dotenv import load_dotenv
load_dotenv()

def get_chat_completion(prompt, model="gpt-4o"):
    url = "https://gptunnel.ru/v1/chat/completions"
    api_key = ""

    if not api_key:
        raise ValueError("API key not found. Please set the GPT_TUNNEL_KEY environment variable.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": """You are a financial assistant AI model designed to provide specific financial predictions based on the latest financial news data.
                              Your task is to analyze the retrieved financial news articles and generate precise predictions with probable numerical intervals.
                              Your responses should be in Russian and should include detailed reasoning based on the data provided.
                              The first line should be a short summari of your answer, and write your very full detailed answer in a line below.
                              YOU HAVE TO CHECK THE INFORMATION IN QUESTION PROMT FOR TRUTH, CORRESPONDING WITH THE SOURCES! If it is not truth - tell user that he is not right and provide correct info!
                              Please, provide links for all sited information in your answer in such markdown way: "[information](link_source_of_information)"
                              
                              Example Prompt:
                              
                              User:
                              "Какие прогнозы по курсу акций компании XYZ на следующую неделю?"
                              
                              Example Response:
                              "Курс акций XYZ будет находится между 120 и 130 рублей на следующей неделе.
                              
                              На основе последних [новостей](https://ru.investing.com/equities), курс акций компании XYZ, вероятно, будет находиться в диапазоне от 120 до 130 рублей за акцию на следующей неделе. Это связано с [положительными отчетами о доходах](link_to_info) и [увеличением спроса на продукцию компании](link_to_info)."
                """
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")

def get_chat_completion_with_history(prompt, chat_history, model="gpt-4o"):
    """
    Get chat completion with conversation history for context.
    
    Args:
        prompt (str): Current user prompt
        chat_history (list): List of previous messages in format [{"role": "user/assistant", "content": "..."}]
        model (str): Model to use
    
    Returns:
        str: Assistant response
    """
    url = "https://gptunnel.ru/v1/chat/completions"
    api_key = "shds-MDQXkzA5cvis2wULFY55ZSH1T8j"

    if not api_key:
        raise ValueError("API key not found. Please set the GPT_TUNNEL_KEY environment variable.")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Build messages array with system prompt, history, and current prompt
    messages = [
        {
            "role": "system",
            "content": """You are a financial assistant AI model designed to provide specific financial predictions based on the latest financial news data.
                          Your task is to analyze the retrieved financial news articles and generate precise predictions with probable numerical intervals.
                          Your responses should be in Russian and should include detailed reasoning based on the data provided.
                          The first line should be a short summary of your answer, and write your very full detailed answer in a line below.
                          YOU HAVE TO CHECK THE INFORMATION IN QUESTION PROMPT FOR TRUTH, CORRESPONDING WITH THE SOURCES! If it is not truth - tell user that he is not right and provide correct info!
                          Please, provide links for all cited information in your answer in such markdown way: "[information](link_source_of_information)"
                          
                          You are having a conversation with the user. Use the conversation history to provide contextual and relevant responses.
                          If the user refers to previous questions or topics, acknowledge them and build upon the conversation.
                          
                          Example Prompt:
                          
                          User:
                          "Какие прогнозы по курсу акций компании XYZ на следующую неделю?"
                          
                          Example Response:
                          "Курс акций XYZ будет находится между 120 и 130 рублей на следующей неделе.
                          
                          На основе последних [новостей](https://ru.investing.com/equities), курс акций компании XYZ, вероятно, будет находиться в диапазоне от 120 до 130 рублей за акцию на следующей неделе. Это связано с [положительными отчетами о доходах](link_to_info) и [увеличением спроса на продукцию компании](link_to_info)."
            """
        }
    ]
    
    # Add conversation history (limit to avoid token limits)
    for msg in chat_history[-8:]:  # Last 8 messages to keep context manageable
        if msg["role"] in ["user", "assistant"]:
            messages.append({
                "role": msg["role"],
                "content": msg["content"]
            })
    
    # Add current prompt
    messages.append({
        "role": "user",
        "content": prompt
    })
    
    data = {
        "model": model,
        "messages": messages,
        "max_tokens": 2000,
        "temperature": 0.7
    }

    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.json()['choices'][0]['message']['content']
    else:
        raise Exception(f"Request failed with status code {response.status_code}: {response.text}")
    
