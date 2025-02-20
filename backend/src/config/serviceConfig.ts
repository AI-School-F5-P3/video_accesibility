import { GoogleAuth } from 'google-auth-library';

export const serviceConfig = {
  youtube: {
    apiKey: process.env.YOUTUBE_API_KEY,
    baseUrl: 'https://www.googleapis.com/youtube/v3',
  },
  vision: {
    projectId: process.env.GOOGLE_CLOUD_PROJECT,
    location: 'global',
  },
  vertex: {
    endpoint: process.env.VERTEX_AI_ENDPOINT,
    location: 'us-central1',
  },
  speechToText: {
    languageCode: 'es-ES',
    enableAutomaticPunctuation: true,
  }
};

export const auth = new GoogleAuth({
  scopes: [
    'https://www.googleapis.com/auth/cloud-platform',
    'https://www.googleapis.com/auth/youtube.readonly'
  ]
});
