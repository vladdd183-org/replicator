#!/bin/bash
# ============================================
# Удаление License Helper Service
# ============================================

echo "============================================"
echo "License Helper Service Uninstallation"
echo "============================================"

# Проверка прав root
if [[ $EUID -ne 0 ]]; then
   echo "ERROR: This script must be run as root (use sudo)"
   exit 1
fi

# Останавливаем сервис
echo ""
echo "Stopping service..."
systemctl stop license-helper.service 2>/dev/null || true

# Отключаем автозапуск
echo "Disabling service..."
systemctl disable license-helper.service 2>/dev/null || true

# Удаляем service файл
echo "Removing service file..."
rm -f /etc/systemd/system/license-helper.service

# Перезагружаем systemd
echo "Reloading systemd..."
systemctl daemon-reload
systemctl reset-failed

# Удаляем бинарник
echo "Removing executable..."
rm -f /usr/local/bin/license-helper

# Спрашиваем об удалении логов
echo ""
read -p "Remove logs from /var/log/license-helper? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    rm -rf /var/log/license-helper
    echo "Logs removed."
else
    echo "Logs preserved at /var/log/license-helper"
fi

echo ""
echo "============================================"
echo "Uninstallation complete!"
echo "============================================"
echo ""





