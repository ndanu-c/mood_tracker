import requests
import json
from config import Config
import logging

class SentimentAnalyzer:
    def __init__(self):
        self.config = Config()
        self.api_url = "https://api-inference.huggingface.co/models/j-hartmann/emotion-english-distilroberta-base"
        self.headers = {
            "Authorization": f"Bearer {self.config.HUGGINGFACE_API_KEY}",
            "Content-Type": "application/json"
        }
    
    def analyze_emotion(self, text):
        """Analyze emotions in text using Hugging Face API"""
        try:
            payload = {"inputs": text}
            response = requests.post(self.api_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                results = response.json()
                
                # Handle the response format from Hugging Face
                if isinstance(results, list) and len(results) > 0:
                    emotions = results[0]
                    
                    # Convert to our expected format
                    emotion_scores = {}
                    overall_sentiment = "neutral"
                    max_score = 0
                    
                    for emotion in emotions:
                        label = emotion['label'].lower()
                        score = emotion['score']
                        
                        # Map emotion labels to our database fields
                        if label in ['joy', 'happiness']:
                            emotion_scores['happiness'] = score
                        elif label in ['sadness']:
                            emotion_scores['sadness'] = score
                        elif label in ['anger']:
                            emotion_scores['anger'] = score
                        elif label in ['fear']:
                            emotion_scores['fear'] = score
                        elif label in ['surprise']:
                            emotion_scores['surprise'] = score
                        elif label in ['disgust']:
                            emotion_scores['disgust'] = score
                        
                        # Determine overall sentiment
                        if score > max_score:
                            max_score = score
                            if label in ['joy', 'happiness']:
                                overall_sentiment = "positive"
                            elif label in ['sadness', 'fear', 'anger', 'disgust']:
                                overall_sentiment = "negative"
                            else:
                                overall_sentiment = "neutral"
                    
                    # Ensure all emotion scores are present
                    emotion_scores.setdefault('happiness', 0)
                    emotion_scores.setdefault('sadness', 0)
                    emotion_scores.setdefault('anger', 0)
                    emotion_scores.setdefault('fear', 0)
                    emotion_scores.setdefault('surprise', 0)
                    emotion_scores.setdefault('disgust', 0)
                    
                    emotion_scores['overall_sentiment'] = overall_sentiment
                    emotion_scores['confidence'] = max_score
                    
                    return emotion_scores
                
            else:
                logging.error(f"Hugging Face API error: {response.status_code} - {response.text}")
                return self._get_default_sentiment()
                
        except Exception as e:
            logging.error(f"Sentiment analysis error: {e}")
            return self._get_default_sentiment()
    
    def _get_default_sentiment(self):
        """Return default sentiment when API fails"""
        return {
            'happiness': 0.5,
            'sadness': 0.1,
            'anger': 0.1,
            'fear': 0.1,
            'surprise': 0.1,
            'disgust': 0.1,
            'overall_sentiment': 'neutral',
            'confidence': 0.5
        }
    
    def get_mood_summary(self, entries_with_sentiment):
        """Generate mood summary from multiple entries"""
        if not entries_with_sentiment:
            return None
        
        total_entries = len(entries_with_sentiment)
        mood_totals = {
            'happiness': 0,
            'sadness': 0,
            'anger': 0,
            'fear': 0,
            'surprise': 0,
            'disgust': 0
        }
        
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        for entry in entries_with_sentiment:
            if entry.get('happiness_score'):
                mood_totals['happiness'] += float(entry['happiness_score'])
            if entry.get('sadness_score'):
                mood_totals['sadness'] += float(entry['sadness_score'])
            if entry.get('anger_score'):
                mood_totals['anger'] += float(entry['anger_score'])
            if entry.get('fear_score'):
                mood_totals['fear'] += float(entry['fear_score'])
            if entry.get('surprise_score'):
                mood_totals['surprise'] += float(entry['surprise_score'])
            if entry.get('disgust_score'):
                mood_totals['disgust'] += float(entry['disgust_score'])
            
            sentiment = entry.get('overall_sentiment', 'neutral')
            sentiment_counts[sentiment] = sentiment_counts.get(sentiment, 0) + 1
        
        # Calculate averages
        mood_averages = {k: v / total_entries for k, v in mood_totals.items()}
        
        return {
            'mood_averages': mood_averages,
            'sentiment_distribution': sentiment_counts,
            'total_entries': total_entries
        }
