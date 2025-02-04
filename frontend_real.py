import React, { useState } from 'react';
import { AlertCircle, Link, Video } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Progress } from '@/components/ui/progress';

const VideoProcessor = () => {
  const [videoUrl, setVideoUrl] = useState('');
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [subtitles, setSubtitles] = useState(null);
  const API_KEY = process.env.REACT_APP_API_KEY;

  const validateYouTubeUrl = (url) => {
    const youtubeRegex = /^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+$/;
    return youtubeRegex.test(url);
  };

  const processVideoUrl = async () => {
    // Validación de URL
    if (!videoUrl) {
      setError('Por favor ingrese una URL de video');
      return;
    }

    if (!validateYouTubeUrl(videoUrl)) {
      setError('Por favor ingrese una URL válida de YouTube');
      return;
    }

    setProcessing(true);
    setProgress(0);
    setError(null);

    try {
      const response = await fetch('http://localhost:8000/process-video-url/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': API_KEY,
        },
        body: JSON.stringify({ url: videoUrl })
      });

      if (!response.ok) {
        throw new Error('Error procesando el video');
      }

      const data = await response.json();
      setSubtitles(data.subtitles);
      setProgress(100);
    } catch (err) {
      setError(err.message);
    } finally {
      setProcessing(false);
    }
  };

  const displaySubtitles = () => {
    if (!subtitles) return null;

    return (
      <div className="mt-4 max-h-60 overflow-y-auto">
        {subtitles.map((subtitle, index) => (
          <div key={index} className="mb-2 p-2 bg-gray-100 rounded">
            <div className="text-sm text-gray-600">
              {subtitle.start_time} → {subtitle.end_time}
            </div>
            <div className="text-base">{subtitle.text}</div>
          </div>
        ))}
      </div>
    );
  };

  return (
    <Card className="w-full max-w-2xl mx-auto mt-8">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Video className="w-6 h-6" />
          Procesador de Video por URL
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <Input 
              type="text" 
              placeholder="Introduce la URL del video de YouTube" 
              value={videoUrl}
              onChange={(e) => setVideoUrl(e.target.value)}
              className="flex-grow"
            />
            <Button 
              onClick={processVideoUrl} 
              disabled={processing}
              className="flex items-center gap-2"
            >
              <Link className="w-4 h-4" />
              Procesar
            </Button>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {processing && (
            <Progress value={progress} className="w-full" />
          )}

          {subtitles && displaySubtitles()}
        </div>
      </CardContent>
    </Card>
  );
};

export default VideoProcessor;