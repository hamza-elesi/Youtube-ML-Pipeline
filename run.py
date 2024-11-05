import os
import argparse
import logging
from dotenv import load_dotenv
from src.etl.youtube_api import YouTubeAPI
from src.etl.s3_upload import S3Uploader
from src.ml.openai_integration import OpenAIAnalyzer
from src.ml.seo_suggestions import SEOSuggestions

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
aws_access_key = os.getenv("AWS_ACCESS_KEY")
aws_secret_key = os.getenv("AWS_SECRET_KEY")
s3_bucket = os.getenv("S3_BUCKET")
developer_key = os.getenv("DEVELOPER_KEY")
openai_key = os.getenv("OPENAI_API_KEY")

def process_video(video_id, output_format='csv'):
    # Initialize components
    youtube_api = YouTubeAPI(developer_key)
    s3_uploader = S3Uploader(aws_access_key, aws_secret_key, s3_bucket)

    try:
        logger.info(f"Processing video ID: {video_id}")

        # Fetch video details
        video_details = youtube_api.get_video_details(video_id)
        logger.info(f"Video details retrieved for {video_id}")

        # Fetch comments
        comments_df = youtube_api.get_video_comments(video_id)
        logger.info(f"Retrieved {len(comments_df)} comments for video {video_id}")

        # Save comments to file
        file_name = f"{video_id}_YouTube_Comments.{output_format}"
        if output_format == 'csv':
            comments_df.to_csv(file_name, index=False)
        elif output_format == 'json':
            comments_df.to_json(file_name, orient='records')
        logger.info(f"Saved comments to {file_name}")

        # Upload file to S3
        s3_uploader.upload_file(file_name)
        logger.info(f"Uploaded {file_name} to S3")

        return video_details, comments_df

    except Exception as e:
        logger.error(f"Error processing video {video_id}: {str(e)}")
        raise

def main(video_ids, output_format='csv'):
    for video_id in video_ids:
        process_video(video_id, output_format)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="YouTube SEO Analysis Pipeline")
    parser.add_argument("video_ids", nargs="+", help="YouTube video IDs to analyze")
    parser.add_argument("--output", choices=['csv', 'json'], default='csv', help="Output format for comments data")
    args = parser.parse_args()

    main(args.video_ids, args.output)