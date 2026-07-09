'use client';
import { useState, useEffect } from 'react';
import { getPendingVideos, approveVideo, publishVideo } from '../../lib/api';

export default function Admin() {
  const [videos, setVideos] = useState([]);

  const fetchPending = () => {
    getPendingVideos().then(data => setVideos(data));
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const handleApprove = async (id) => {
    await approveVideo(id);
    fetchPending();
  };

  const handlePublish = async (id) => {
    await publishVideo(id);
    fetchPending();
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial' }}>
      <h1>🛠️ అడ్మిన్ డాష్బోర్డ్</h1>
      <h3>Pending (Draft) వీడియోలు</h3>
      {videos.length === 0 && <p>🎉 ప్రస్తుతం పెండింగ్ వీడియోలు లేవు.</p>}
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {videos.map((video) => (
          <li key={video.id} style={{ border: '1px solid #ccc', margin: '10px 0', padding: '15px' }}>
            <p><strong>ID:</strong> {video.id}</p>
            <p><strong>న్యూస్:</strong> {video.news_text}</p>
            <p><strong>స్క్రిప్ట్:</strong> {video.script || 'రాదు'}</p>
            <div style={{ display: 'flex', gap: '10px' }}>
              <button onClick={() => handleApprove(video.id)} style={{ background: 'orange', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '5px' }}>
                ✅ Approve
              </button>
              <button onClick={() => handlePublish(video.id)} style={{ background: 'green', color: 'white', border: 'none', padding: '8px 15px', borderRadius: '5px' }}>
                🚀 Publish
              </button>
            </div>
          </li>
        ))}
      </ul>
      <button onClick={fetchPending} style={{ marginTop: '20px', padding: '10px', background: '#eee', border: '1px solid #ccc' }}>
        ⟳ రిఫ్రెష్
      </button>
    </div>
  );
}
