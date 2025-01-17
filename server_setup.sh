#!/bin/bash

# 確認所有參數是否提供
if [ "$#" -ne 6 ]; then
  echo "錯誤: 需要提供 6 個參數"
  echo "使用方式: $0 <zoom> <text_num> <audio_playlist> <audio_detach> <high_sync> <detect_interval>"
  exit 1
fi

ZOOM="$1"
TEXT_NUM="$2"
AUDIO_PLAYLIST="$3"
AUDIO_DETACH="$4"
HIGH_SYNC="$5"
DETECT_INTERVAL="$6"

# 動態生成 script B 的執行命令
# 取得當前路徑
CURRENT_PATH=$(pwd)
SCRIPT_B_PATH = "$CURRENT_PATH/server_activate.sh"

# 取得使用者的名稱，並依此將指令加入 .bashrc
USER_NAME=$(whoami)
BASHRC_PATH="/home/$USER_NAME/.bashrc"

# 將指令加入 .bashrc
EXEC_CMD="screen -L -dmS server bash $SCRIPT_B_PATH --zoom $ZOOM --text_num $TEXT_NUM --audio_playlist $AUDIO_PLAYLIST --audio_detach $AUDIO_DETACH --high_sync $HIGH_SYNC --detect_interval $DETECT_INTERVAL"

if ! grep -qF "$EXEC_CMD" "$BASHRC_PATH"; then
  echo "$EXEC_CMD" >> "$BASHRC_PATH"
  echo "已將執行指令加入 $BASHRC_PATH"
else
  echo "執行指令已存在於 $BASHRC_PATH"
fi

echo "script A 執行完成。"
