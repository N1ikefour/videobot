module.exports = {
  apps: [
    {
      name: "videobot",
      script: "run.py",
      interpreter: "/opt/videobot/venv/bin/python",
      cwd: "/opt/videobot",
      instances: 1,
      exec_mode: "fork",
      autorestart: true,
      watch: false,
      max_memory_restart: "1G",
      min_uptime: "10s",
      max_restarts: 10,
      error_file: "./logs/err.log",
      out_file: "./logs/out.log",
      log_file: "./logs/combined.log",
      time: true,
      env: {
        NODE_ENV: "production",
        PYTHONPATH: "/opt/videobot",
        PYTHONUNBUFFERED: "1",
      },
      env_production: {
        NODE_ENV: "production",
      },
    },
  ],
};
