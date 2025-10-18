import openai
import os
from typing import List, Dict, Optional
import json

class OpenAIClassifier:
    """
    A text classifier using OpenAI's GPT models for various classification tasks.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-3.5-turbo"):
        """
        Initialize the classifier with OpenAI API key and model.
        
        Args:
            api_key: OpenAI API key. If None, will try to get from environment variable.
            model: OpenAI model to use for classification.
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        openai.api_key = self.api_key
        self.model = model
    
    def sentiment_classification(self, text: str) -> Dict[str, str]:
        """
        Classify sentiment of the given text.
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary with classification result and confidence
        """
        prompt = f"""
        Classify the sentiment of the following text as either 'positive', 'negative', or 'neutral'.
        Provide your answer in JSON format with 'sentiment' and 'confidence' fields.
        
        Text: "{text}"
        
        Response format:
        {{"sentiment": "positive/negative/neutral", "confidence": "high/medium/low"}}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a sentiment analysis expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
            
        except Exception as e:
            return {"error": f"Classification failed: {str(e)}"}
    
    def topic_classification(self, text: str, categories: List[str]) -> Dict[str, str]:
        """
        Classify text into predefined topic categories.
        
        Args:
            text: Text to classify
            categories: List of possible categories
            
        Returns:
            Dictionary with classification result
        """
        categories_str = ", ".join(categories)
        
        prompt = f"""
        Classify the following text into one of these categories: {categories_str}
        Provide your answer in JSON format with 'category' and 'confidence' fields.
        
        Text: "{text}"
        
        Response format:
        {{"category": "selected_category", "confidence": "high/medium/low"}}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a topic classification expert. Always respond with valid JSON and only use the provided categories."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
            
        except Exception as e:
            return {"error": f"Classification failed: {str(e)}"}
    
    def spam_classification(self, text: str) -> Dict[str, str]:
        """
        Classify if text is spam or not spam.
        
        Args:
            text: Text to classify
            
        Returns:
            Dictionary with classification result
        """
        prompt = f"""
        Determine if the following text is 'spam' or 'not_spam'.
        Consider promotional content, suspicious links, excessive capitalization, and urgency tactics.
        Provide your answer in JSON format with 'classification' and 'confidence' fields.
        
        Text: "{text}"
        
        Response format:
        {{"classification": "spam/not_spam", "confidence": "high/medium/low"}}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a spam detection expert. Always respond with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=100
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
            
        except Exception as e:
            return {"error": f"Classification failed: {str(e)}"}
    
    def custom_classification(self, text: str, task_description: str, categories: List[str]) -> Dict[str, str]:
        """
        Perform custom classification based on user-defined task and categories.
        
        Args:
            text: Text to classify
            task_description: Description of the classification task
            categories: List of possible categories
            
        Returns:
            Dictionary with classification result
        """
        categories_str = ", ".join(categories)
        
        prompt = f"""
        Task: {task_description}
        
        Classify the following text into one of these categories: {categories_str}
        Provide your answer in JSON format with 'category' and 'confidence' fields.
        
        Text: "{text}"
        
        Response format:
        {{"category": "selected_category", "confidence": "high/medium/low"}}
        """
        
        try:
            response = openai.ChatCompletion.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a classification expert. Always respond with valid JSON and only use the provided categories."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=150
            )
            
            result = response.choices[0].message.content.strip()
            return json.loads(result)
            
        except Exception as e:
            return {"error": f"Classification failed: {str(e)}"}

def main():
    """
    Example usage of the OpenAI classifier.
    """
    # Initialize classifier (make sure to set your OpenAI API key)
    try:
        classifier = OpenAIClassifier()
    except ValueError as e:
        print(f"Error: {e}")
        print("Please set your OpenAI API key as an environment variable: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Example texts for classification
    examples = [
        "I absolutely love this product! It's amazing and works perfectly.",
        "This is the worst service I've ever experienced. Completely disappointed.",
        "The weather today is quite normal, nothing special.",
        "URGENT!!! Click here to win $1000000 NOW!!! Limited time offer!!!",
        "Meeting scheduled for tomorrow at 2 PM in conference room A.",
        "The latest developments in artificial intelligence are fascinating and show great promise for the future."
    ]
    
    print("=== OpenAI Text Classification Examples ===\n")
    
    # Sentiment Classification
    print("1. SENTIMENT CLASSIFICATION:")
    print("-" * 40)
    for i, text in enumerate(examples[:3], 1):
        result = classifier.sentiment_classification(text)
        print(f"Text {i}: {text[:50]}...")
        print(f"Result: {result}")
        print()
    
    # Spam Classification
    print("2. SPAM CLASSIFICATION:")
    print("-" * 40)
    for i, text in enumerate(examples[3:5], 1):
        result = classifier.spam_classification(text)
        print(f"Text {i}: {text[:50]}...")
        print(f"Result: {result}")
        print()
    
    # Topic Classification
    print("3. TOPIC CLASSIFICATION:")
    print("-" * 40)
    topics = ["technology", "business", "sports", "entertainment", "science", "politics"]
    result = classifier.topic_classification(examples[5], topics)
    print(f"Text: {examples[5][:50]}...")
    print(f"Categories: {topics}")
    print(f"Result: {result}")
    print()
    
    # Custom Classification Example
    print("4. CUSTOM CLASSIFICATION:")
    print("-" * 40)
    custom_task = "Classify the urgency level of customer support requests"
    urgency_levels = ["low", "medium", "high", "critical"]
    
    support_requests = [
        "My password reset email hasn't arrived yet.",
        "The entire system is down and we can't process any orders!",
        "I have a question about billing cycles."
    ]
    
    for i, request in enumerate(support_requests, 1):
        result = classifier.custom_classification(request, custom_task, urgency_levels)
        print(f"Request {i}: {request}")
        print(f"Urgency: {result}")
        print()

if __name__ == "__main__":
    main()
