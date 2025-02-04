import React, { useState, useRef } from 'react';
import { AlertCircle, Upload, Video } from 'lucide-react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Progress } from '@/components/ui/progress';

const VideoProcessor = () => {
  const [file, setFile] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [error, setError] = useState(null);
  const [subtitles, setSubtitles] = useState(null);
  const videoRef = useRef(null);
  const API_KEY = process.env.REACT_APP_API_KEY;

  const handleFileChange = (event) => {
    const selectedFile = event.target.files[0];
    if (selectedFile && selectedFile.type.startsWith('video/')) {
      setFile(selectedFile);
      setError(null);
    } else {
      setError('Please select a valid video file');
    }
  };

  const uploadVideo = async () => {
    if (!file) return;

    setProcessing(true);
    setProgress(0);
    
    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch('http://localhost:8000/upload-video/', {
        method: 'POST',
        headers: {
          'X-API-Key': API_KEY,
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Upload failed');
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
          Video Processor
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <div className="flex justify-center items-center w-full">
            <label className="flex flex-col items-center justify-center w-full h-64 border-2 border-dashed rounded-lg cursor-pointer bg-gray-50 hover:bg-gray-100">
              <div className="flex flex-col items-center justify-center pt-5 pb-6">
                <Upload className="w-8 h-8 mb-4 text-gray-500" />
                <p className="mb-2 text-sm text-gray-500">
                  <span className="font-semibold">Click to upload</span> or drag and drop
                </p>
                <p className="text-xs text-gray-500">MP4, AVI, MOV (MAX. 800MB)</p>
              </div>
              <input
                type="file"
                className="hidden"
                onChange={handleFileChange}
                accept="video/*"
              />
            </label>
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Error</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {file && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm font-medium">Selected file: {file.name}</span>
                <Button
                  onClick={uploadVideo}
                  disabled={processing}
                >
                  {processing ? 'Processing...' : 'Process Video'}
                </Button>
              </div>

              {processing && (
                <Progress value={progress} className="w-full" />
              )}
            </div>
          )}

          {subtitles && displaySubtitles()}
        </div>
      </CardContent>
    </Card>
  );
};

export default VideoProcessor;