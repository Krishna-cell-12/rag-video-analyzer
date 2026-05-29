import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from app.models.video import VideoMetadata

class VideoExtractor:
    
    @staticmethod
    def calculate_engagement(likes: int, comments: int, views: int) -> float:
        if views == 0:
            return 0.0
        return round(((likes + comments) / views) * 100, 2)

    def extract_youtube(self, url: str) -> VideoMetadata:
        # 1. Setup yt-dlp to extract metadata without downloading the video
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'extract_flat': False
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        video_id = info.get('id')
        views = info.get('view_count', 0)
        likes = info.get('like_count', 0)
        comments = info.get('comment_count', 0)
        
        # 2. Extract Transcript
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            transcript_text = " ".join([t['text'] for t in transcript_list])
        except Exception as e:
            print(f"Transcript failed for {video_id}: {e}")
            transcript_text = "Transcript unavailable or disabled."

        # 3. Return strictly typed model
        return VideoMetadata(
            video_id=video_id,
            platform="youtube",
            creator=info.get('uploader', 'Unknown'),
            follower_count=info.get('channel_follower_count', 0),
            views=views,
            likes=likes,
            comments=comments,
            engagement_rate=self.calculate_engagement(likes, comments, views),
            transcript=transcript_text
        )
        
    def extract_instagram(self, url: str) -> VideoMetadata:
        # Note: Instagram blocks scrapers heavily. For a production demo,
        ydl_opts = {'quiet': True, 'skip_download': True}
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
        views = info.get('view_count', 1) # Prevent division by zero
        likes = info.get('like_count', 0)
        comments = info.get('comment_count', 0)
        
        return VideoMetadata(
            video_id=info.get('id', 'insta_video'),
            platform="instagram",
            creator=info.get('uploader', 'Unknown'),
            views=views,
            likes=likes,
            comments=comments,
            engagement_rate=self.calculate_engagement(likes, comments, views),
            transcript="Instagram audio extraction requires local Whisper setup. Skipping for test." 
        )