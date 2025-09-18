module.exports = {
  apps: [
    {
      name: "videobot",
      script: "run.py",
      interpreter: "/opt/videobot/venv/bin/python",
      cwd: "/opt/videobot",
      instances: "max", // Использовать все доступные CPU ядра
      exec_mode: "cluster", // Кластерный режим для параллельности
      autorestart: true,
      watch: false,
      max_memory_restart: "2G", // Увеличено с 1G
      min_uptime: "10s",
      max_restarts: 15, // Увеличено с 10
      restart_delay: 4000, // Задержка между перезапусками
      error_file: "./logs/err.log",
      out_file: "./logs/out.log",
      log_file: "./logs/combined.log",
      time: true,
      merge_logs: true, // Объединение логов от всех инстансов
      instance_var: "INSTANCE_ID",
      env: {
        NODE_ENV: "production",
        PYTHONPATH: "/opt/videobot",
        PYTHONUNBUFFERED: "1",
        // Оптимизация для FFmpeg
        FFMPEG_THREADS: "0", // Использовать все доступные ядра
        OMP_NUM_THREADS: "0", // Для OpenMP оптимизации
      },
      env_production: {
        NODE_ENV: "production",
      },
      // Дополнительные настройки для производительности
      node_args: "--max-old-space-size=4096",
      kill_timeout: 5000,
      listen_timeout: 8000,
      // Мониторинг производительности
      pmx: false,
      // Настройки для обработки видео
      source_map_support: false,
      // Автоматическая очистка логов
      log_date_format: "YYYY-MM-DD HH:mm:ss Z",
      // Graceful shutdown
      shutdown_with_message: true,
    },
  ],
};
