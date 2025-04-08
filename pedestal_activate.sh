#!/bin/bash
# -----------------------------------------------------------------------------
# pedestal_activate.sh
#
# 功能：
#  1. 根據使用者指定或自動偵測的平台（raspberrypi 或 macos）啟動 run.py，
#     並將其他參數（例如 --dslr --printer_detach True --printer_list I）
#     原封不動地傳給 run.py。
#  2. 若未提供 --platform，則根據 uname 自動偵測：
#       Darwin  → macos
#       Linux   → 若 /proc/cpuinfo 中含 "Raspberry"，則設為 raspberrypi，
#                 否則預設為 raspberrypi
#  3. 使用 sudo 執行 run.py（滿足 USB 相機操作需求），
#     並從 .pedestal 虛擬環境中啟動 python。
#  4. 若 run.py 因 segmentation fault (退出碼 139) 結束，則自動重啟。
#
# 注意：
#  此版本不再檢查時間自動關閉，由 launchd 負責啟動與終止。
# -----------------------------------------------------------------------------

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

# 若未提供 --platform，則自動偵測
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
#    ※ 本版本移除了自動關閉的時間檢查，由 launchd 控制關閉
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
