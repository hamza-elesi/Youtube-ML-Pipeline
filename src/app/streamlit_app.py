import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from wordcloud import WordCloud
import os
import sys
from dotenv import load_dotenv
from io import BytesIO
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from src.etl.youtube_api import YouTubeAPI
from src.etl.s3_upload import S3Uploader
from src.ml.openai_integration import OpenAIAnalyzer
from src.ml.seo_suggestions import SEOSuggestions
from run import process_video

# Load environment variables
load_dotenv()
aws_access_key = os.getenv("AWS_ACCESS_KEY")
aws_secret_key = os.getenv("AWS_SECRET_KEY")
s3_bucket = os.getenv("S3_BUCKET")
openai_key = os.getenv("OPENAI_API_KEY")
youtube_api_key = os.getenv("DEVELOPER_KEY")

# PDF Generation Function
def generate_pdf(content):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    flowables = []

    for line in content.split('\n'):
        para = Paragraph(line, styles['Normal'])
        flowables.append(para)

    doc.build(flowables)
    buffer.seek(0)
    return buffer

# Initialize components with error handling
try:
    if not youtube_api_key:
        raise ValueError("YouTube API key (DEVELOPER_KEY) is missing. Please check your .env file.")
    
    if not aws_access_key or not aws_secret_key or not s3_bucket:
        raise ValueError("AWS credentials or S3 bucket name is missing. Please check your .env file.")
    
    if not openai_key:
        raise ValueError("OpenAI API key is missing. Please check your .env file.")
    
    s3_uploader = S3Uploader(aws_access_key, aws_secret_key, s3_bucket)
    openai_analyzer = OpenAIAnalyzer(api_key=openai_key)
    seo_generator = SEOSuggestions(openai_analyzer)
    youtube_api = YouTubeAPI(api_key=youtube_api_key)
    
except ValueError as ve:
    st.error(f"Error initializing components: {str(ve)}")
    st.stop()
except Exception as e:
    st.error(f"Unexpected error initializing components: {str(e)}")
    st.stop()

# Streamlit app
st.set_page_config(page_title="YouTube SEO Analyzer", layout="wide")

# Session state
if 'video_ids' not in st.session_state:
    st.session_state['video_ids'] = []
if 'analysis_results' not in st.session_state:
    st.session_state['analysis_results'] = {}

# Sidebar
st.sidebar.title("YouTube SEO Analyzer")
video_id = st.sidebar.text_input("Enter YouTube Video ID")
if st.sidebar.button("Add Video"):
    if video_id and video_id not in st.session_state['video_ids']:
        try:
            with st.spinner(f"Processing and analyzing video {video_id}..."):
                # Process the video using the function from run.py
                video_details, comments_df = process_video(video_id)
                
                # Perform immediate SEO analysis
                all_comments_text = " ".join(comments_df['textDisplay'])
                seo_report = seo_generator.comprehensive_analysis(all_comments_text)
                
                st.session_state['video_ids'].append(video_id)
                st.session_state['analysis_results'][video_id] = {
                    'details': video_details,
                    'comments': comments_df,
                    'seo_report': seo_report
                }
            st.sidebar.success(f"Added and analyzed video: {video_details['title']}")
        except Exception as e:
            st.sidebar.error(f"Error processing video {video_id}: {str(e)}")
    elif video_id in st.session_state['video_ids']:
        st.sidebar.warning("This video ID is already added.")
    else:
        st.sidebar.warning("Please enter a valid video ID.")

# Main content
st.title("YouTube SEO Analysis Dashboard")

# Re-Analyze button
if st.button("Re-Analyze All Videos"):
    with st.spinner("Re-analyzing all videos..."):
        for video_id in st.session_state['video_ids']:
            try:
                # Re-fetch comments in case there are new ones
                _, comments_df = process_video(video_id)
                all_comments_text = " ".join(comments_df['textDisplay'])
                seo_report = seo_generator.comprehensive_analysis(all_comments_text)
                
                # Update results
                st.session_state['analysis_results'][video_id]['comments'] = comments_df
                st.session_state['analysis_results'][video_id]['seo_report'] = seo_report
                st.success(f"Re-analysis completed for: {st.session_state['analysis_results'][video_id]['details']['title']}")
            except Exception as e:
                st.error(f"Error re-analyzing video {video_id}: {str(e)}")

# Display results
if st.session_state['analysis_results']:
    for video_id, results in st.session_state['analysis_results'].items():
        st.header(f"Analysis for: {results['details']['title']}")
        
        # Video details
        st.subheader("Video Details")
        st.json(results['details'])
        
        # Comments wordcloud
        st.subheader("Comments Word Cloud")
        wordcloud = WordCloud(width=800, height=400, background_color='white').generate(" ".join(results['comments']['textDisplay']))
        fig, ax = plt.subplots()
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis('off')
        st.pyplot(fig)
        
        # SEO Report
        st.subheader("SEO Analysis Report")
        if 'seo_report' in results and results['seo_report']:
            st.markdown(results['seo_report'])
            
            # Generate PDF
            pdf_buffer = generate_pdf(results['seo_report'])
            
            # Download button for SEO report
            st.download_button(
                label="Download SEO Report",
                data=pdf_buffer,
                file_name=f"SEO_Report_{results['details']['title']}.pdf",
                mime="application/pdf"
            )
        else:
            st.warning("SEO report not found for this video. Please click 'Re-Analyze All Videos' to generate the report.")

# Comparison feature
if len(st.session_state['video_ids']) > 1:
    st.header("Video Comparison")
    video_titles = {video_id: results['details']['title'] for video_id, results in st.session_state['analysis_results'].items()}
    videos_to_compare = st.multiselect("Select videos to compare", options=list(video_titles.keys()), format_func=lambda x: video_titles[x])
    if len(videos_to_compare) > 1:
        comparison_data = []
        for video_id in videos_to_compare:
            results = st.session_state['analysis_results'][video_id]
            comparison_data.append({
                'Video Title': results['details']['title'],
                'Views': results['details']['views'],
                'Likes': results['details']['likes'],
                'Comments': len(results['comments']),
                'Sentiment': seo_generator.analyze_sentiment(" ".join(results['comments']['textDisplay']))
            })
        comparison_df = pd.DataFrame(comparison_data)
        st.table(comparison_df)

        # Visualization
        fig, ax = plt.subplots(figsize=(12, 6))
        comparison_df.plot(x='Video Title', y=['Views', 'Likes', 'Comments'], kind='bar', ax=ax)
        plt.title("Video Performance Comparison")
        plt.ylabel("Count")
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        st.pyplot(fig)

# Clear data button
if st.button("Clear All Data"):
    st.session_state['video_ids'] = []
    st.session_state['analysis_results'] = {}
    st.success("All data has been cleared.")