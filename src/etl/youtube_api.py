import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

class YouTubeAPI:
    def __init__(self, api_key):
        if not api_key:
            raise ValueError("API key is required")
        self.youtube = googleapiclient.discovery.build(
            "youtube", "v3", developerKey=api_key
        )
        self.logger = logging.getLogger(__name__)

    @retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _execute_request(self, request):
        try:
            return request.execute()
        except googleapiclient.errors.HttpError as e:
            if e.resp.status in [429, 500, 503]:  # Rate limiting or server errors
                self.logger.warning(f"YouTube API request failed with status {e.resp.status}. Retrying...")
                raise  # This will trigger a retry
            else:
                self.logger.error(f"YouTube API request failed: {e}")
                raise

    def get_video_comments(self, video_id, max_results=None):
        comments = []
        next_page_token = None

        try:
            while True:
                self.logger.info(f"Fetching comments for video ID: {video_id} (pageToken: {next_page_token})")
                
                request = self.youtube.commentThreads().list(
                    part="snippet",
                    videoId=video_id,
                    textFormat="plainText",
                    maxResults=100,
                    pageToken=next_page_token
                )
                
                response = self._execute_request(request)

                for item in response.get('items', []):
                    comment = item['snippet']['topLevelComment']['snippet']
                    comments.append({
                        'channelId': comment.get('authorChannelId', {}).get('value', 'Unknown'),
                        'textDisplay': comment.get('textDisplay', ''),
                        'likeCount': comment.get('likeCount', 0),
                        'publishedAt': comment.get('publishedAt', 'Unknown'),
                        'updatedAt': comment.get('updatedAt', 'Unknown')
                    })

                next_page_token = response.get('nextPageToken')
                
                if not next_page_token or (max_results and len(comments) >= max_results):
                    break

        except Exception as e:
            self.logger.error(f"Error fetching comments for video {video_id}: {e}")
            raise

        self.logger.info(f"Retrieved {len(comments)} comments for video ID: {video_id}")
        return pd.DataFrame(comments)

    def get_video_details(self, video_id):
        try:
            request = self.youtube.videos().list(
                part="snippet,statistics",
                id=video_id
            )
            response = self._execute_request(request)

            if 'items' in response and len(response['items']) > 0:
                video = response['items'][0]
                return {
                    'title': video['snippet'].get('title', ''),
                    'views': video['statistics'].get('viewCount', 0),
                    'likes': video['statistics'].get('likeCount', 0),
                    'dislikes': video['statistics'].get('dislikeCount', 0),
                    'comments': video['statistics'].get('commentCount', 0)
                }
            else:
                self.logger.warning(f"No details found for video ID: {video_id}")
                return None

        except Exception as e:
            self.logger.error(f"Error fetching video details for {video_id}: {e}")
            raise