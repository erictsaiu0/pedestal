#!/bin/bash

# 確認使用者是否提供了參數
if [ -z "$1" ]; then
  echo "錯誤: 請提供 id 參數。"
  echo "使用方式: $0 <id>"
  exit 1
fi

ID="$1"

# 動態生成 script B 的執行命令
SCRIPT_B_PATH="pi_setup.sh"  # 替換為 script B 的實際路徑
BASHRC_PATH="/home/raspberrypi/.bashrc"

# 在 .bashrc 中添加執行 script B 的命令
if ! grep -q "$SCRIPT_B_PATH --id $ID" "$BASHRC_PATH"; then
  echo "screen -dmS $ID bash $SCRIPT_B_PATH --id $ID" >> "$BASHRC_PATH"
  echo "已將執行指令加入 $BASHRC_PATH"
else
  echo "執行指令已存在於 $BASHRC_PATH"
fi

echo "script A 執行完成。"
