from youtube_transcript_api import YouTubeTranscriptApi

def get_full_transcript(video_id):
    # Get the transcript data
    transcript_data = YouTubeTranscriptApi.get_transcript(video_id)

    # Extract and concatenate all text items
    full_transcript = ' '.join(item['text'] for item in transcript_data)

    return full_transcript

# Usage
video_id = "TWINrTppUl4"
transcript_text = get_full_transcript(video_id)

# Print the full transcript
print(transcript_text)