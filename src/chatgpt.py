import requests
from config import Settings
import json
class gpt():
    """
        THIS IS LEGACY CODE BECAUSE CHAT GPT IS A PAID API
    
    
    """
    def __init__(self, api_key) -> None:
        self.headers = {
    'User-Agent': 'My User Agent',
    'Authorization': f'Bearer {api_key}',
    'Content-Type': 'application/json'
        }
        self.endpoint = 'https://api.openai.com/v1/chat/completions'

    def get_chat_response(self, message):
        print(self.headers)
        # data = {
        #     'model': 'gpt-3.5-turbo',
        #     'prompt': message,
        #     'temperature': 0.6,
        #     'max_tokens': 100
        # }
        data = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello!"}]
            }
        response = requests.post(self.endpoint, headers=self.headers, data=json.dumps(data))

        # Extract the response from the API call
        response_data = response.json()
        print(response_data)
        return response_data
        answer = response_data['choices'][0]['text'].strip()

    









settings = Settings()
gpttest = gpt(settings.GPTAPI)
gpttest.get_chat_response("Give me a League of Legends team comp")