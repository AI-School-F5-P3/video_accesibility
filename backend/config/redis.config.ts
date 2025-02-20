export const redisConfig = {
    host: process.env.REDIS_HOST || 'localhost',
    port: parseInt(process.env.REDIS_PORT || '6379'),
    password: process.env.REDIS_PASSWORD || '',
    retryStrategy: (times: number) => {
        if (times > 3) {
            console.error('No se pudo conectar a Redis después de 3 intentos');
            return null;
        }
        return Math.min(times * 100, 3000);
    }
};