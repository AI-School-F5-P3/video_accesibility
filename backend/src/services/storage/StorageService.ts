import { Storage } from '@google-cloud/storage';
import { serviceConfig } from '../../config/serviceConfig';
import { Readable } from 'stream';

export class StorageService {
  private storage: Storage;
  private bucketName: string;

  constructor() {
    this.storage = new Storage({
      keyFilename: process.env.GOOGLE_APPLICATION_CREDENTIALS
    });
    this.bucketName = process.env.STORAGE_BUCKET || 'video-accessibility';
  }

  async createBucketIfNotExists() {
    const [exists] = await this.storage.bucket(this.bucketName).exists();
    if (!exists) {
      await this.storage.createBucket(this.bucketName);
    }
  }

  async uploadFile(filePath: string, destination: string): Promise<string> {
    await this.createBucketIfNotExists();
    await this.storage.bucket(this.bucketName).upload(filePath, {
      destination
    });
    return `gs://${this.bucketName}/${destination}`;
  }

  async saveAudio(audioContent: Buffer, filename: string): Promise<string> {
    try {
      const bucket = this.storage.bucket(this.bucketName);
      const file = bucket.file(`audio/${filename}`);

      // Crear un stream desde el buffer
      const stream = new Readable();
      stream.push(audioContent);
      stream.push(null);

      // Guardar el archivo
      await new Promise((resolve, reject) => {
        stream
          .pipe(file.createWriteStream({
            metadata: {
              contentType: 'audio/mp3'
            }
          }))
          .on('error', reject)
          .on('finish', resolve);
      });

      // Retornar la URI del archivo guardado
      return `gs://${this.bucketName}/audio/${filename}`;
    } catch (error) {
      console.error('Error guardando audio:', error);
      throw new Error('Error al guardar el archivo de audio');
    }
  }
}
