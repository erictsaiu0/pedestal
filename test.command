#!/bin/bash

# 自動以 sudo 執行
if [[ $EUID -ne 0 ]]; then
  echo "需要 sudo 權限來執行此腳本..."
  exec sudo "$0"
fi

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

# 提示用戶選擇是否使用 DSLR 模式
while true; do
  read -p "是否使用 DSLR 模式？(y/n): " dslr_choice
  case "$dslr_choice" in
    [Yy]* ) DSLR_MODE="--dslr"; break;;
    [Nn]* ) DSLR_MODE=""; break;;
    * ) echo "請輸入 y 或 n";;
  esac
done

# 提示用戶輸入攝影機編號
read -p "請輸入攝影機編號（可從0開始測試，若使用 DSLR 可跳過）: " user_input

# 驗證輸入是否為數字，若未輸入則默認為 DSLR 模式
if [[ "$dslr_choice" =~ ^[Yy]$ ]]; then
  user_input=""
elif ! [[ "$user_input" =~ ^[0-9]+$ ]]; then
  echo "錯誤：輸入必須是一個數字！"
  read -p "按任意鍵退出..."
  exit 1
fi

# 確認是否以 sudo 執行
if [[ $EUID -ne 0 ]]; then
  echo "警告：gphoto2 需要使用 sudo 執行。"
  echo "請使用 sudo 重新運行此腳本，或手動執行以下指令："
  echo "sudo python \"$SCRIPT_DIR/test.py\" $DSLR_MODE --camera \"$user_input\""
  read -p "按任意鍵退出..."
  exit 1
fi

# 執行 Python 腳本
if [[ "$dslr_choice" =~ ^[Yy]$ ]]; then
  sudo python "$SCRIPT_DIR/test.py" $DSLR_MODE
else
  sudo python "$SCRIPT_DIR/test.py" --camera "$user_input"
fi

# 等待用戶按鍵後退出
read -p "按任意鍵退出..."
