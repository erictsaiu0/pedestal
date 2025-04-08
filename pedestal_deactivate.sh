#!/bin/bash
# kill_pythonrun.sh
# 此腳本會根據 screen 會話名稱來終止執行中的程式
# 使用方法：直接執行該腳本，或傳入自定義的 session 名稱作為參數
# 例如：./kill_pythonrun.sh my_session

# 若未指定 session 名稱，預設為 "server"
SESSION_NAME="${1:-server}"

# 檢查是否存在符合名稱的 screen 會話
if screen -list | grep -q "[[:space:]]\+${SESSION_NAME}[[:space:]]"; then
  echo "找到 screen 會話 '${SESSION_NAME}'，正在關閉..."
  screen -S "${SESSION_NAME}" -X quit
  # 等待一段時間確認會話是否已關閉
  sleep 1
  if screen -list | grep -q "[[:space:]]\+${SESSION_NAME}[[:space:]]"; then
    echo "會話 '${SESSION_NAME}' 無法關閉，請檢查狀態。"
    exit 1
  else
    echo "會話 '${SESSION_NAME}' 已成功關閉。"
    exit 0
  fi
else
  echo "找不到名稱為 '${SESSION_NAME}' 的 screen 會話。"
  exit 0
fi
