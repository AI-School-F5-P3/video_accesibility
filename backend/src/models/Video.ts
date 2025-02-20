import { Storage } from '@google-cloud/storage';
import { YoutubeService } from '../services/youtube/YoutubeService';

export class Video {
  private youtubeService: YoutubeService;
  private storage: Storage;
  private bucketName: string = 'video-accessibility-uploads';
  private url: string;
  private videoId: string; // Añadir propiedad faltante
  private localPath: string; // Añadir propiedad faltante

  constructor(url: string) {
    this.url = url;
    this.videoId = extractVideoId(url);
    this.youtubeService = new YoutubeService();
    this.storage = new Storage();
    this.localPath = ''; // Inicializar
  }

  async download(): Promise<void> {
    // Implementar descarga
    return Promise.resolve();
  }

  async uploadToGCS(): Promise<string> {
    const bucket = this.storage.bucket(this.bucketName);
    const filename = `${this.videoId}_${Date.now()}.mp4`;
    
    await bucket.upload(this.localPath, {
      destination: filename,
      metadata: {
        contentType: 'video/mp4'
      }
    });

    return `gs://${this.bucketName}/${filename}`;
  }

  async getMetadata(): Promise<any> {
    return this.youtubeService.getVideoInfo(this.videoId);
  }
}

function extractVideoId(url: string): string {
  // Implementar extracción de ID desde URL de YouTube
  return url.split('v=')[1];
}
