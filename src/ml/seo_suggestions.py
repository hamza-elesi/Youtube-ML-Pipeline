import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
import logging
from functools import lru_cache

class SEOSuggestions:
    def __init__(self, openai_analyzer):
        self.openai_analyzer = openai_analyzer
        self.logger = logging.getLogger(__name__)
        
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            self.stop_words = set(stopwords.words('english'))
        except Exception as e:
            self.logger.warning(f"Failed to load NLTK data: {e}")
            self.stop_words = set(['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with'])

    @lru_cache(maxsize=100)
    def generate_overall_suggestions(self, comments_text):
        return self.openai_analyzer.analyze_comment_sentiment(comments_text)

    def extract_keywords(self, text, top_n=10):
        try:
            words = word_tokenize(text.lower())
        except Exception as e:
            self.logger.warning(f"Error in tokenization: {e}. Falling back to simple split.")
            words = text.lower().split()
        
        words = [word for word in words if word.isalnum() and word not in self.stop_words]
        word_freq = Counter(words)
        return word_freq.most_common(top_n)

    def analyze_sentiment(self, comments_text):
        positive_words = set(['good', 'great', 'excellent', 'amazing', 'love', 'best'])
        negative_words = set(['bad', 'poor', 'terrible', 'worst', 'hate', 'awful'])
        
        try:
            words = word_tokenize(comments_text.lower())
        except Exception as e:
            self.logger.warning(f"Error in tokenization: {e}. Falling back to simple split.")
            words = comments_text.lower().split()
        
        positive_count = sum(1 for word in words if word in positive_words)
        negative_count = sum(1 for word in words if word in negative_words)
        
        total_words = len(words)
        sentiment_score = (positive_count - negative_count) / total_words if total_words > 0 else 0
        
        if sentiment_score > 0.05:
            return "Positive"
        elif sentiment_score < -0.05:
            return "Negative"
        else:
            return "Neutral"

    def comprehensive_analysis(self, comments_text):
        keywords = self.extract_keywords(comments_text)
        sentiment = self.analyze_sentiment(comments_text)
        topics = self.analyze_topic_modeling(comments_text)
        content_ideas = self.generate_content_ideas(topics)
        openai_suggestions = self.generate_overall_suggestions(comments_text)

        report = f"""
# Comprehensive SEO and Content Analysis

## 1. Top Keywords
{', '.join([f'**{word}** ({count})' for word, count in keywords])}

## 2. Overall Sentiment
{sentiment}

## 3. Main Topics of Discussion
{', '.join(topics)}

## 4. Content Ideas
{' '.join(f'- {idea}' for idea in content_ideas)}

## 5. SEO Recommendations
- Incorporate top keywords and topics into video titles, descriptions, and tags.
- {"Highlight positive aspects in your marketing." if sentiment == "Positive" else "Address concerns in future content." if sentiment == "Negative" else "Encourage more specific feedback in future videos."}
- Create a content series based on the main topics of discussion.
- Use timestamps in video descriptions to highlight sections related to popular topics.

## 6. Engagement Strategies
- Respond to comments discussing the main topics to foster community engagement.
- Create polls or surveys based on the identified topics to gather more specific viewer preferences.
- {"Encourage viewers to share their positive experiences." if sentiment == "Positive" else "Ask for constructive feedback on how to improve." if sentiment == "Negative" else "Prompt viewers to share more detailed opinions on the content."}

## 7. OpenAI-Generated Insights
{openai_suggestions}

## 8. Next Steps
- Prioritize content ideas based on keyword frequency and sentiment.
- Develop a content calendar incorporating the suggested topics and ideas.
- Regularly review and update SEO strategies based on changing viewer interests and comments.

Remember, the goal is to create valuable, engaging content for your audience while optimizing for search and discovery on YouTube.
"""

        return report

    def analyze_topic_modeling(self, comments_text, num_topics=5):
        try:
            words = word_tokenize(comments_text.lower())
        except Exception as e:
            self.logger.warning(f"Error in tokenization: {e}. Falling back to simple split.")
            words = comments_text.lower().split()
        
        words = [word for word in words if word.isalnum() and word not in self.stop_words]
        word_freq = Counter(words)
        topics = word_freq.most_common(num_topics)
        return [topic for topic, _ in topics]

    def generate_content_ideas(self, topics):
        return [f"Create a video expanding on the topic of '{topic}' based on viewer interest." for topic in topics]