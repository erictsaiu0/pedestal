#!/bin/bash

# 獲取當前 .command 文件的路徑
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

# 提示用戶輸入參數
read -p "請輸入攝影機編號（可從0開始測試）: " user_input

# 驗證輸入是否為數字
if ! [[ "$user_input" =~ ^[0-9]+$ ]]; then
  echo "錯誤：輸入必須是一個數字！"
  read -p "按任意鍵退出..."
  exit 1
fi

# 執行 Python 腳本
python "$SCRIPT_DIR/test.py" --camera "$user_input"

# 等待用戶按鍵後退出
read -p "按任意鍵退出..."
