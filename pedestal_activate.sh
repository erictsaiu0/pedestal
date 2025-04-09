#!/bin/bash
# -----------------------------------------------------------------------------
# pedestal_activate.sh
#
# 說明：
#  此腳本會根據使用者指定或自動偵測的平台（raspberrypi 或 macos）
#  啟動 run.py 並傳遞額外參數（例如 --dslr --printer_detach True --printer_list I)；
#  遇到 segmentation fault (退出碼 139) 時會自動重新啟動 run.py。
#
#  若未提供 --platform 參數，則自動偵測作業系統：
#    Darwin  → macos
#    Linux   → 如果 /proc/cpuinfo 中含 "Raspberry"，則設為 raspberrypi，
#              否則預設為 raspberrypi
#
#  注意：由於預計會由 launchd 在開機時啟動此腳本，因此在腳本開頭加入 cd 指令，
#       確保工作目錄切換至腳本所在資料夾，讓所有相對路徑正確運作。
#
#  此版本不再包含依據時間自動關閉的邏輯，關閉工作由 launchd 處理。
# -----------------------------------------------------------------------------

# 切換至腳本所在資料夾（launchd 啟動時會使用預設工作目錄）
cd "$(dirname "$0")" || exit 1

# 1. 解析參數：分離 --platform 參數，其餘參數存入 SERVER_ARGS 陣列
MODE=""
SERVER_ARGS=()

while [[ "$#" -gt 0 ]]; do
  case "$1" in
    --platform)
      MODE="$2"
      shift 2
      ;;
    *)
      SERVER_ARGS+=("$1")
      shift
      ;;
  esac
done

# 若未提供 --platform 則自動偵測
if [ -z "$MODE" ]; then
    OS_TYPE=$(uname -s)
    if [ "$OS_TYPE" = "Darwin" ]; then
        MODE="macos"
    elif [ "$OS_TYPE" = "Linux" ]; then
        if grep -qi "Raspberry" /proc/cpuinfo 2>/dev/null; then
            MODE="raspberrypi"
        else
            MODE="raspberrypi"
        fi
    else
        echo "不支援的作業系統：$OS_TYPE"
        exit 1
    fi
fi

echo "所選模式：$MODE"
echo "傳遞給 run.py 的額外參數：${SERVER_ARGS[*]}"

# 2. 根據平台設定必要的環境變數
if [ "$MODE" = "raspberrypi" ]; then
    echo "設定 Raspberry Pi 模式相關環境變數..."
    export DISPLAY=:0
    export XDG_RUNTIME_DIR=/run/user/$(id -u)
    export PULSE_SERVER=unix:/run/user/$(id -u)/pulse/native
elif [ "$MODE" = "macos" ]; then
    echo "macOS 模式，無需額外環境變數設定。"
fi

# 3. 啟動虛擬環境
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
echo "腳本所在路徑：$SCRIPT_DIR"
VENV_PATH="$SCRIPT_DIR/.pedestal/bin/activate"
if [ ! -f "$VENV_PATH" ]; then
  echo "錯誤：虛擬環境未找到！路徑：$VENV_PATH"
  exit 1
fi

source "$VENV_PATH"
if [[ -z "$VIRTUAL_ENV" ]]; then
  echo "虛擬環境啟動失敗！"
  exit 1
else
  echo "虛擬環境已啟動：$VIRTUAL_ENV"
fi

# 4. 將 SERVER_ARGS 陣列組合成一個字串（假設參數內無空白）
RUNPY_ARGS="${SERVER_ARGS[*]}"
echo "傳入 run.py 的參數字串：$RUNPY_ARGS"

# 5. 建立臨時腳本並利用 screen 執行 while 迴圈
#    ※ 此版本移除了自動關閉的時間檢查，由 launchd 控制關閉
TEMP_SCRIPT=$(mktemp)
chmod +x "$TEMP_SCRIPT"

cat > "$TEMP_SCRIPT" <<EOF
#!/bin/bash
while true; do
  echo "[\$(date '+%Y-%m-%d %H:%M:%S')] 播放啟動聲音..."
  sudo "\$VIRTUAL_ENV/bin/python" sound.py --path 'activate_sound.mp3'
  
  echo "[\$(date '+%Y-%m-%d %H:%M:%S')] 啟動 run.py..."
  sudo "\$VIRTUAL_ENV/bin/python" run.py $RUNPY_ARGS
  EXIT_CODE=\$?
  
  if [ \$EXIT_CODE -eq 139 ]; then
      echo "[\$(date '+%Y-%m-%d %H:%M:%S')] 檢測到 Segmentation fault，將重新啟動 run.py..."
  else
      echo "[\$(date '+%Y-%m-%d %H:%M:%S')] run.py 正常退出 (退出碼 \$EXIT_CODE)，停止監控。"
      break
  fi
  sleep 1
done
EOF

echo "啟動 screen 會話 (名稱：server) 以執行監控流程..."
screen -L -dmS server bash "$TEMP_SCRIPT"
if [ $? -eq 0 ]; then
    echo "screen 會話啟動成功。"
    screen -r
else
    echo "screen 會話啟動失敗！"
fi

rm "$TEMP_SCRIPT"
