# 🚀 VideoBot - Инструкция по деплою

Пошаговое руководство по развертыванию VideoBot на production сервере.

## 📋 Системные требования

### Минимальные требования:

- **CPU:** 2 ядра
- **RAM:** 4 GB
- **Storage:** 20 GB SSD
- **OS:** Ubuntu 20.04+ или Debian 11+

### Рекомендуемые требования:

- **CPU:** 4 ядра
- **RAM:** 8 GB
- **Storage:** 40 GB SSD
- **OS:** Ubuntu 22.04 LTS

## 🔧 Автоматическая установка (Cloud-init)

### Для Timeweb Cloud:

```bash
#!/bin/sh

# Cloud-init скрипт для VideoBot
set -e

# Обновление системы
apt-get update && apt-get upgrade -y

# Установка базовых пакетов
apt-get install -y \
    curl wget git nano htop ufw \
    python3 python3-pip python3-venv python3-dev \
    build-essential pkg-config \
    ffmpeg \
    software-properties-common

# Установка Node.js LTS
curl -fsSL https://deb.nodesource.com/setup_lts.x | bash -
apt-get install -y nodejs

# Установка PM2
npm install -g pm2

# Создание пользователя videobot
useradd -m -s /bin/bash videobot
usermod -aG sudo videobot

# Создание рабочих директорий
mkdir -p /opt/videobot/temp
mkdir -p /opt/videobot/output
mkdir -p /opt/videobot/logs
chown -R videobot:videobot /opt/videobot

# Настройка файрвола
ufw allow ssh
ufw allow 22
ufw --force enable

echo "🎉 VideoBot сервер готов к деплою!"
```

## 📥 Ручная установка

### 1. Подготовка сервера

```bash
# Подключение к серверу
ssh root@YOUR_SERVER_IP

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка базовых пакетов
sudo apt install -y curl wget git nano htop ufw python3 python3-pip python3-venv python3-dev build-essential ffmpeg

# Установка Node.js
curl -fsSL https://deb.nodesource.com/setup_lts.x | sudo -E bash -
sudo apt-get install -y nodejs

# Установка PM2
sudo npm install -g pm2
```

### 2. Создание пользователя

```bash
# Создание пользователя videobot
sudo useradd -m -s /bin/bash videobot
sudo usermod -aG sudo videobot

# Создание рабочих директорий
sudo mkdir -p /opt/videobot/{temp,output,logs}
sudo chown -R videobot:videobot /opt/videobot
```

### 3. Деплой проекта

```bash
# Переключение на пользователя videobot
sudo su - videobot
cd /opt/videobot

# Клонирование проекта
git clone https://github.com/N1ikefour/videobot.git .

# Создание виртуальной среды
python3 -m venv venv
source venv/bin/activate

# Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Конфигурация

```bash
# Создание .env файла
cp .env.template .env
nano .env
```

**Содержимое .env:**

```env
BOT_TOKEN=ваш_токен_от_botfather
MAX_FILE_SIZE_MB=50
```

### 5. Запуск через PM2

```bash
# Запуск в production режиме
pm2 start ecosystem.config.js --env production

# Проверка статуса
pm2 status

# Сохранение конфигурации
pm2 save

# Автозапуск при перезагрузке
pm2 startup
# Выполните команду которую выдаст PM2
```

## 🔄 Обновление проекта

### Стандартное обновление:

```bash
cd /opt/videobot
git pull origin main
pm2 restart videobot
```

### Обновление с зависимостями:

```bash
cd /opt/videobot
git pull origin main
source venv/bin/activate
pip install -r requirements.txt
pm2 restart videobot
```

## 📊 Мониторинг

### Основные команды:

```bash
# Статус процессов
pm2 status

# Логи в реальном времени
pm2 logs videobot

# Мониторинг ресурсов
pm2 monit

# Детальная информация
pm2 describe videobot
```

### Системный мониторинг:

```bash
# Использование ресурсов
htop

# Место на диске
df -h

# Память
free -h

# Процессы FFmpeg
ps aux | grep ffmpeg
```

## 🛠️ Оптимизация производительности

### Настройка PM2 для высокой нагрузки:

```javascript
// ecosystem.config.js
module.exports = {
  apps: [
    {
      name: "videobot",
      script: "run.py",
      interpreter: "/opt/videobot/venv/bin/python",
      instances: "max", // Использовать все CPU ядра
      exec_mode: "cluster",
      max_memory_restart: "2G",
      // ... остальные настройки
    },
  ],
};
```

### Оптимизация FFmpeg:

```python
# В video_processor.py можно изменить preset
# Для максимальной скорости:
preset='ultrafast'

# Для баланса скорость/качество:
preset='fast'

# Для лучшего качества:
preset='medium'
```

## 🔧 Устранение проблем

### Логи и диагностика:

```bash
# Логи PM2
pm2 logs videobot --lines 100

# Логи приложения
tail -f /opt/videobot/logs/combined.log

# Системные логи
journalctl -u pm2-videobot
```

### Частые проблемы:

#### 1. Бот не отвечает

```bash
# Проверить статус
pm2 status

# Перезапустить
pm2 restart videobot

# Проверить логи
pm2 logs videobot
```

#### 2. Медленная обработка

```bash
# Проверить нагрузку CPU
htop

# Проверить место на диске
df -h

# Очистить временные файлы
find /opt/videobot/temp -type f -mmin +60 -delete
find /opt/videobot/output -type f -mmin +120 -delete
```

#### 3. Ошибки памяти

```bash
# Увеличить лимит памяти в PM2
pm2 restart videobot --max-memory-restart 4G

# Проверить swap
swapon --show
```

## 🔒 Безопасность

### Базовые настройки:

```bash
# Настройка файрвола
sudo ufw allow ssh
sudo ufw allow 22
sudo ufw enable

# Обновление системы
sudo apt update && sudo apt upgrade -y

# Настройка автообновлений
sudo apt install unattended-upgrades
sudo dpkg-reconfigure unattended-upgrades
```

### Ограничение доступа:

```bash
# Запрет root логина по SSH (опционально)
sudo nano /etc/ssh/sshd_config
# PermitRootLogin no

# Перезапуск SSH
sudo systemctl restart ssh
```

## 📈 Масштабирование

### Для высокой нагрузки:

1. **Увеличьте ресурсы сервера:**

   - CPU: 8+ ядер
   - RAM: 16+ GB
   - SSD: быстрый NVMe

2. **Настройте PM2 кластер:**

   ```javascript
   instances: 'max',
   exec_mode: 'cluster'
   ```

3. **Используйте балансировщик нагрузки** для нескольких серверов

4. **Добавьте Redis** для очередей между серверами

## 🎯 Чеклист деплоя

- [ ] Сервер настроен и обновлен
- [ ] Python 3.8+ установлен
- [ ] FFmpeg установлен и работает
- [ ] Node.js и PM2 установлены
- [ ] Пользователь videobot создан
- [ ] Проект клонирован в /opt/videobot
- [ ] Виртуальная среда создана
- [ ] Зависимости установлены
- [ ] .env файл настроен с токеном
- [ ] PM2 запущен и работает
- [ ] Автозапуск PM2 настроен
- [ ] Логи работают корректно
- [ ] Бот отвечает в Telegram
- [ ] Обработка видео работает

## 📞 Поддержка

При проблемах с деплоем:

1. Проверьте логи: `pm2 logs videobot`
2. Проверьте статус: `pm2 status`
3. Проверьте системные ресурсы: `htop`
4. Создайте issue в GitHub с детальным описанием

---

**Успешного деплоя! 🚀**
