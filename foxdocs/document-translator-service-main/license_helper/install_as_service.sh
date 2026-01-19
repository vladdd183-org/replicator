#!/bin/bash
# ============================================
# Установка License Helper как systemd service
# ============================================

echo "============================================"
echo "License Helper Service Installation"
echo "============================================"

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo "ERROR: This script must be run as root (use sudo)"
   exit 1
fi

# Определяем путь к бинарнику
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
EXE_PATH="${SCRIPT_DIR}/dist/license-helper"

# Проверяем существование файла
if [ ! -f "$EXE_PATH" ]; then
    echo "ERROR: license-helper not found at $EXE_PATH"
    echo "Please build the executable first using: ./build.sh"
    exit 1
fi

# Создаем директорию для логов
LOG_DIR="/var/log/license-helper"
mkdir -p "$LOG_DIR"

# Копируем бинарник в /usr/local/bin
echo ""
echo "Installing executable to /usr/local/bin..."
cp "$EXE_PATH" /usr/local/bin/license-helper
chmod +x /usr/local/bin/license-helper

# Создаем systemd service файл
SERVICE_FILE="/etc/systemd/system/license-helper.service"

echo ""
echo "Creating systemd service..."
cat > "$SERVICE_FILE" << 'EOF'
[Unit]
Description=License Helper Service for Document Translator
After=network.target

[Service]
Type=simple
User=root
ExecStart=/usr/local/bin/license-helper
Restart=always
RestartSec=5
StandardOutput=append:/var/log/license-helper/license-helper.log
StandardError=append:/var/log/license-helper/license-helper-error.log

# Environment variables (если нужно)
# Environment="LICENSE_SERVER_URL=https://your-license-server.com"

[Install]
WantedBy=multi-user.target
EOF

# Перезагружаем systemd
echo ""
echo "Reloading systemd..."
systemctl daemon-reload

# Включаем автозапуск
echo "Enabling service..."
systemctl enable license-helper.service

# Запускаем сервис
echo "Starting service..."
systemctl start license-helper.service

# Ждем немного
sleep 2

# Проверяем статус
echo ""
echo "============================================"
echo "Service status:"
echo "============================================"
systemctl status license-helper.service --no-pager

echo ""
echo "============================================"
echo "Installation complete!"
echo "============================================"
echo ""
echo "Service name: license-helper"
echo "Logs: /var/log/license-helper/"
echo ""
echo "Useful commands:"
echo "  - Check status:  sudo systemctl status license-helper"
echo "  - View logs:     sudo journalctl -u license-helper -f"
echo "  - Restart:       sudo systemctl restart license-helper"
echo "  - Stop:          sudo systemctl stop license-helper"
echo "  - Uninstall:     sudo ./uninstall_service.sh"
echo ""





