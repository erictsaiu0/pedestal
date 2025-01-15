#!/bin/bash

# 獲取當前腳本所在的路徑
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "腳本所在路徑: $SCRIPT_DIR"

# 拼接虛擬環境的路徑
VENV_PATH="$SCRIPT_DIR/.pedestal/bin/activate"

# 檢查虛擬環境是否存在
if [ ! -f "$VENV_PATH" ]; then
  echo "錯誤：虛擬環境未找到！路徑: $VENV_PATH"
  read -p "按任意鍵退出..."
  exit 1
fi

# 啟動虛擬環境
source "$VENV_PATH"

# 確認虛擬環境是否成功啟動
if [[ "$VIRTUAL_ENV" != "" ]]; then
  echo "虛擬環境已成功啟動: $VIRTUAL_ENV"
else
  echo "虛擬環境啟動失敗！"
  read -p "按任意鍵退出..."
  exit 1
fi

# 確認是否提供 id 參數
if [ -z "$1" ]; then
  echo "錯誤: 請提供 id 參數。"
  echo "使用方式: $0 --id <id>"
  exit 1
fi

# 提取 id 參數
if [ "$1" == "--id" ] && [ -n "$2" ]; then
  ID="$2"
else
  echo "錯誤: 未提供有效的 --id 參數。"
  exit 1
fi

# 在 screen 中執行 python web_socket.py
echo "啟動 screen，會話名稱為: $ID"
screen -dmS "$ID" bash -c "python web_socket.py --id $ID"
if [ $? -eq 0 ]; then
  echo "screen 啟動成功，執行: python web_socket.py --id $ID"
else
  echo "screen 啟動失敗！"
fi
