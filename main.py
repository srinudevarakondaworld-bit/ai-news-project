import yt_dlp
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from groq import Groq
from sqlalchemy import create_engine, Column, String, DateTime, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from datetime import datetime
import uuid
import feedparser
import requests
from apscheduler.schedulers.background import BackgroundScheduler

# .env ఫైల్ ను లోడ్ చేయడం
load_dotenv()

# --- 1. SQLite డేటాబేస్ సెటప్ ---
SQLALCHEMY_DATABASE_URL = "sqlite:///./videos.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# డేటాబేస్ మోడల్ (టేబుల్)
class VideoDB(Base):
    __tablename__ = "videos"

    id = Column(String, primary_key=True, index=True)
    url = Column(String)
    news_text = Column(String)
    video_path = Column(String, nullable=True)
    script = Column(Text, nullable=True)
    status = Column(String, default="draft")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# డేటాబేస్ టేబుల్‌ను సృష్టించండి
Base.metadata.create_all(bind=engine)

# --- 2. FastAPI యాప్ ---
app = FastAPI(docs_url="/docs", redoc_url=None)

@app.api_route("/", methods=["GET", "HEAD"])
async def root():
    return {"message": "Hello World! FastAPI is running on Render."}

@app.get("/health")
async def health():
    return {"status": "ok"}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- 3. వీడియో డౌన్లోడ్ ఫంక్షన్ (format = 'best') ---
def download_video(url: str):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'cookiefile': 'cookies.txt',
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return f"downloads/{info['title']}.{info['ext']}"
    except Exception as e:
        return f"Error downloading video: {e}"

# --- 4. AI స్క్రిప్ట్ జనరేషన్ (Groq) ---
def generate_script(news_text: str):
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        return "GROQ_API_KEY not found. Please set it in .env file."
    try:
        client = Groq(api_key=api_key)
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "You are a professional news anchor. Write a very short, engaging news script in Telugu (తెలుగు) based on the given news text."
                },
                {
                    "role": "user",
                    "content": f"Here is the news text: {news_text}. Write a 30-second news script."
                }
            ],
            model="llama-3.3-70b-versatile",
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"Error generating script: {e}"

# --- 5. Pydantic మోడల్స్ ---
class VideoRequest(BaseModel):
    url: str
    news_text: str

class VideoResponse(BaseModel):
    id: str
    url: str
    news_text: str
    video_path: str = None
    script: str = None
    status: str
    created_at: datetime

# --- 6. API ఎండ్పాయింట్స్ ---

@app.post("/process-video/", response_model=VideoResponse)
async def process_video(request: VideoRequest, db: Session = Depends(get_db)):
    video_path = download_video(request.url)
    script = generate_script(request.news_text)

    video_id = str(uuid.uuid4())
    db_video = VideoDB(
        id=video_id,
        url=request.url,
        news_text=request.news_text,
        video_path=video_path,
        script=script,
        status="draft"
    )
    db.add(db_video)
    db.commit()
    db.refresh(db_video)

    return VideoResponse(
        id=db_video.id,
        url=db_video.url,
        news_text=db_video.news_text,
        video_path=db_video.video_path,
        script=db_video.script,
        status=db_video.status,
        created_at=db_video.created_at
    )

@app.get("/videos/pending/", response_model=list[VideoResponse])
async def get_pending_videos(db: Session = Depends(get_db)):
    videos = db.query(VideoDB).filter(VideoDB.status == "draft").all()
    return videos

@app.post("/videos/{video_id}/approve/")
async def approve_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(VideoDB).filter(VideoDB.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    video.status = "approved"
    db.commit()
    return {"message": "Video approved successfully!", "status": video.status}

@app.post("/videos/{video_id}/publish/")
async def publish_video(video_id: str, db: Session = Depends(get_db)):
    video = db.query(VideoDB).filter(VideoDB.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != "approved":
        raise HTTPException(status_code=400, detail="Video must be approved first before publishing")
    video.status = "published"
    db.commit()
    return {"message": "Video published successfully!", "status": video.status}

@app.get("/videos/published/", response_model=list[VideoResponse])
async def get_published_videos(db: Session = Depends(get_db)):
    videos = db.query(VideoDB).filter(VideoDB.status == "published").all()
    return videos

# --- 7. ఆటోమేటిక్ న్యూస్ ఫెచ్ (RSS + షెడ్యూలర్) ---
def auto_fetch_and_process():
    print("🔄 ఆటోమేటిక్ న్యూస్ ఫెచ్ ప్రారంభం...")
    try:
        news_feed = feedparser.parse('https://news.google.com/rss?hl=te&gl=IN&ceid=IN:te')
        if news_feed.entries:
            latest_news = news_feed.entries[0]
            title = latest_news.title
            article_link = latest_news.link
            
            print(f"📰 కనుగొన్న న్యూస్: {title}")
            
            # 1. ఆర్టికల్ నుండి ఇమేజ్ మరియు టెక్స్ట్ తీయండి
            image_url, article_text = fetch_article_image_and_text(article_link)
            
            # 2. AI తో రీరైట్ చేయండి
            rewritten_text = rewrite_and_save_news(article_text if article_text else title)
            
            # 3. Draft వీడియో క్రియేట్ చేయండి (డిఫాల్ట్ YouTube URL తో)
            default_video_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
            db = SessionLocal()
            try:
                video_path = download_video(default_video_url)
                script = rewritten_text if rewritten_text else "No content available"
                video_id = str(uuid.uuid4())
                db_video = VideoDB(
                    id=video_id,
                    url=default_video_url,
                    news_text=title,
                    video_path=video_path,
                    script=script,
                    status="draft"
                )
                db.add(db_video)
                db.commit()
                db.refresh(db_video)
                print(f"✅ Draft క్రియేట్ అయింది! ID: {video_id}")
                if image_url:
                    print(f"🖼️ ఇమేజ్ URL: {image_url}")
            except Exception as e:
                print(f"❌ డేటాబేస్ ఎర్రర్: {e}")
            finally:
                db.close()
    except Exception as e:
        print(f"❌ ఆటోమేటిక్ ఫెచ్ ఎర్రర్: {e}")