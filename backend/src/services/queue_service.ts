import Queue from 'bull';
import Redis from 'ioredis';

interface QueueJob {
  taskId: string;
  processor: () => Promise<any>;
  status: string;
  result?: any;
  error?: string;
}

export class QueueService {
  private videoQueue: Queue.Queue<QueueJob>;
  private redis: Redis;

  constructor() {
    this.redis = new Redis({
      host: process.env.REDIS_HOST || 'localhost',
      port: Number(process.env.REDIS_PORT) || 6379,
      maxRetriesPerRequest: 3,
      retryStrategy(times) {
        if (times > 3) {
          console.error('No se pudo conectar a Redis después de 3 intentos');
          return null;
        }
        return Math.min(times * 100, 3000);
      }
    });

    this.redis.on('error', (err) => {
      console.error('Error de conexión Redis:', err);
    });

    this.videoQueue = new Queue<QueueJob>('video-processing', {
      redis: {
        host: process.env.REDIS_HOST || 'localhost',
        port: Number(process.env.REDIS_PORT) || 6379
      }
    });

    this.setupQueueHandlers();
  }

  private setupQueueHandlers(): void {
    this.videoQueue.on('completed', async (job) => {
      await this.redis.hset(`task:${job.id}`, 'status', 'completed');
    });

    this.videoQueue.on('failed', async (job, error) => {
      await this.redis.hset(`task:${job.id}`, 'status', 'failed', 'error', error.message);
    });
  }

  async enqueue_task(taskId: string, processor: () => Promise<any>): Promise<string> {
    const job = await this.videoQueue.add({
      taskId,
      processor,
      status: 'pending'
    });

    await this.redis.hset(`task:${taskId}`, 'status', 'pending');
    return taskId;
  }

  async get_task_status(taskId: string): Promise<string> {
    const status = await this.redis.hget(`task:${taskId}`, 'status');
    return status || 'not_found';
  }

  async cleanup(): Promise<void> {
    await this.videoQueue.clean(1000);
    await this.redis.quit();
  }
}