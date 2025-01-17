#!/bin/bash

# 確認所有參數是否提供
if [ "$#" -ne 6 ]; then
    echo "錯誤: 需要提供 6 個參數"
    echo "使用方式: $0 <zoom> <text_num> <audio_playlist> <audio_detach> <high_sync> <detect_interval>"
    exit 1
fi

# 設定參數
ZOOM="$1"
TEXT_NUM="$2"
AUDIO_PLAYLIST="$3"
AUDIO_DETACH="$4"
HIGH_SYNC="$5"
DETECT_INTERVAL="$6"

# 設定腳本路徑
SCRIPT_B_PATH = "server_activate.sh"
CURRENT_DIR = $(pwd)

# 取得使用者名稱和 .bashrc 路徑
USER_NAME = $(whoami)
BASHRC_PATH = "/home/$USER_NAME/.bashrc"

# 建立要執行的命令
EXEC_CMD="cd $CURRENT_DIR && screen -L -dmS server bash ./$SCRIPT_B_PATH --zoom $ZOOM --text_num $TEXT_NUM --audio_playlist $AUDIO_PLAYLIST --audio_detach $AUDIO_DETACH --high_sync $HIGH_SYNC --detect_interval $DETECT_INTERVAL"

# 檢查命令是否已存在於 .bashrc
if ! grep -qF "$EXEC_CMD" "$BASHRC_PATH"; then
    # 在 .bashrc 的最後加入一個空行（如果不存在的話）
    if [ -s "$BASHRC_PATH" ] && [ "$(tail -c1 "$BASHRC_PATH")" != "" ]; then
        echo "" >> "$BASHRC_PATH"
    fi
    
    # 加入命令
    echo "# 自動啟動服務器" >> "$BASHRC_PATH"
    echo "$EXEC_CMD" >> "$BASHRC_PATH"
    echo "已將執行指令加入 $BASHRC_PATH"
else
    echo "執行指令已存在於 $BASHRC_PATH"
fi

# 立即執行命令（可選）
eval "$EXEC_CMD"

echo "腳本設置完成。系統重啟後會自動執行服務器。"