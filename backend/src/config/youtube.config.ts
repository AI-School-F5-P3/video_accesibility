export const youtubeConfig = {
    apiKey: process.env.YOUTUBE_API_KEY,
    maxDuration: parseInt(process.env.MAX_VIDEO_DURATION || '3600'),
    supportedFormats: (process.env.SUPPORTED_FORMATS || 'mp4,mp3,srt,vtt').split(','),
    downloadPath: process.env.TEMP_STORAGE_PATH || './temp'
};