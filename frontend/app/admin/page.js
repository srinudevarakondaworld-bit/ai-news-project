'use client';
import { useState, useEffect } from 'react';
import { getPublishedVideos } from '../lib/api';

export default function Home() {
  const [videos, setVideos] = useState([]);

  useEffect(() => {
    getPublishedVideos().then(data => setVideos(data));
  }, []);

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>📺 తెలుగు న్యూస్ వీడియోలు</h1>
      {videos.length === 0 && <p>😕 ప్రస్తుతం వీడియోలు లేవు.</p>}
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '20px' }}>
        {videos.map((video) => (
          <div key={video.id} style={{ border: '1px solid #ddd', padding: '15px', width: '300px' }}>
            <h3>{video.news_text}</h3>
            <p><strong>స్టేటస్:</strong> {video.status}</p>
            {video.video_path && <p>✅ వీడియో: {video.video_path}</p>}
            {video.script && <details><summary>📝 స్క్రిప్ట్</summary><p>{video.script}</p></details>}
          </div>
        ))}
      </div>
    </div>
  );
}