// frontend/lib/api.js
const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "https://ai-news-project-3pje.onrender.com";

export async function getPublishedVideos() {
  const res = await fetch(`${API_BASE_URL}/videos/published/`);
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