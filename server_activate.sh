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

# 解析參數
while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --zoom) ZOOM="$2"; shift ;;
    --text_num) TEXT_NUM="$2"; shift ;;
    --audio_playlist) AUDIO_PLAYLIST="$2"; shift ;;
    --audio_detach) AUDIO_DETACH="$2"; shift ;;
    --high_sync) HIGH_SYNC="$2"; shift ;;
    --detect_interval) DETECT_INTERVAL="$2"; shift ;;
    *)
      echo "未知參數: $1"
      exit 1
      ;;
  esac
  shift
done

# 確認所有必要參數是否存在
if [ -z "$ZOOM" ] || [ -z "$TEXT_NUM" ] || [ -z "$AUDIO_PLAYLIST" ] || [ -z "$AUDIO_DETACH" ] || [ -z "$HIGH_SYNC" ] || [ -z "$DETECT_INTERVAL" ]; then
  echo "錯誤: 缺少必要參數。"
  echo "使用方式: $0 --zoom <value> --text_num <value> --audio_playlist <value> --audio_detach <value> --high_sync <value> --detect_interval <value>"
  exit 1
fi

# 定義監控與重啟的函數
monitor_and_restart() {
  while true; do
    echo "啟動 Python 腳本..."
    # 讓程式可以播放聲音
    export DISPLAY=:0
    export XDG_RUNTIME_DIR=/run/user/$(id -u)
    export PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native
    python sound.py 
    python run.py --zoom "$ZOOM" --text_num "$TEXT_NUM" --audio_playlist "$AUDIO_PLAYLIST" --audio_detach "$AUDIO_DETACH" --high_sync "$HIGH_SYNC" --detect_interval "$DETECT_INTERVAL"
    EXIT_CODE=$?
    
    # 判斷是否發生 Segmentation fault (退出碼為 139)
    if [ $EXIT_CODE -eq 139 ]; then
      echo "Segmentation fault 檢測到，重新啟動腳本中..."
    else
      echo "腳本正常退出 (退出碼 $EXIT_CODE)，停止監控。"
      break
    fi
    sleep 1 # 加入短暫延遲避免過快重啟
  done
}
# 執行監控函數
$(declare -f monitor_and_restart)
monitor_and_restart

# # 在 screen 中執行監控函數
# # echo "啟動 screen，會話名稱為: server"
# # screen -dmS server bash -c "$(declare -f monitor_and_restart); monitor_and_restart"
# if [ $? -eq 0 ]; then
#   echo "screen 啟動成功，執行並監控: python run.py --zoom $ZOOM --text_num $TEXT_NUM --audio_playlist $AUDIO_PLAYLIST --audio_detach $AUDIO_DETACH --high_sync $HIGH_SYNC --detect_interval $DETECT_INTERVAL"
#   screen -r
# else
#   echo "screen 啟動失敗！"
# fi
