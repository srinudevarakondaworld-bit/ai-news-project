// lib/api.js - పూర్తి కోడ్
const API_BASE_URL = "http://127.0.0.1:8000";

export async function createVideo(url, newsText) {
  const res = await fetch(`${API_BASE_URL}/process-video/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url, news_text: newsText }),
  });
  return res.json();
}

export async function getPendingVideos() {
  const res = await fetch(`${API_BASE_URL}/videos/pending/`);
  return res.json();
}

export async function approveVideo(videoId) {
  const res = await fetch(`${API_BASE_URL}/videos/${videoId}/approve/`, {
    method: "POST",
  });
  return res.json();
}

export async function publishVideo(videoId) {
  const res = await fetch(`${API_BASE_URL}/videos/${videoId}/publish/`, {
    method: "POST",
  });
  return res.json();
}

export async function getPublishedVideos() {
  const res = await fetch(`${API_BASE_URL}/videos/published/`);
  return res.json();
}