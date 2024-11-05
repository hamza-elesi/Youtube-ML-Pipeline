import os
import logging
from openai import OpenAI
from dotenv import load_dotenv
import tiktoken
from functools import lru_cache

class OpenAIAnalyzer:
    def __init__(self, api_key=None, model="gpt-3.5-turbo"):
        self.load_env()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        if not self.api_key:
            raise ValueError("OpenAI API key is missing. Please check the .env file or pass it directly.")
        self.client = OpenAI(api_key=self.api_key)
        self.logger = logging.getLogger(__name__)

    @staticmethod
    def load_env():
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.abspath(os.path.join(current_dir, '../../'))
        env_path = os.path.join(project_root, '.env')
        if os.path.exists(env_path):
            load_dotenv(dotenv_path=env_path)
        else:
            logging.warning(f".env file not found at {env_path}")

    def count_tokens(self, text):
        encoding = tiktoken.encoding_for_model(self.model)
        return len(encoding.encode(text))

    def truncate_input(self, text, max_tokens=3500):
        encoding = tiktoken.encoding_for_model(self.model)
        tokens = encoding.encode(text)
        if len(tokens) > max_tokens:
            return encoding.decode(tokens[:max_tokens]) + '...'
        return text

    @lru_cache(maxsize=100)
    def analyze_comment_sentiment(self, comments_text):
        truncated_text = self.truncate_input(comments_text)
        total_tokens = self.count_tokens(truncated_text)
        
        messages = [
            {"role": "system", "content": 'You are an SEO expert analyzing YouTube comments.'},
            {"role": "user", "content": f"Analyze the sentiment and SEO relevance of the following YouTube comments and provide suggestions for SEO optimization: '{truncated_text}'"}
        ]

        try:
            self.logger.info(f"Sending request to OpenAI using model: {self.model}")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.5
            )
            
            if response and response.choices:
                response_message = response.choices[0].message.content.strip()
                self.logger.info("OpenAI response received successfully.")
                return f"\u200B\n\n{response_message}"
            else:
                self.logger.error("No valid response received from OpenAI.")
                return "Error: Unable to generate analysis."
        except Exception as e:
            self.logger.error(f"Error in analyzing comment sentiment: {e}")
            return f"Error: {str(e)}"

    def set_model(self, model):
        self.model = model
        self.logger.info(f"Model changed to: {model}")