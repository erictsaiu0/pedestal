#!/bin/bash

# 安裝 runit
echo "Installing runit..."
sudo apt-get update
sudo apt-get install -y runit

# 創建 pedestal_service 目錄
echo "Creating pedestal_service directory..."
sudo mkdir -p /etc/service/pedestal_service

# 創建 run 腳本
echo "Creating run script for pedestal_service..."
sudo bash -c 'cat > /etc/service/pedestal_service/run <<EOL
#!/bin/bash

# 獲取當前腳本所在的路徑
SCRIPT_DIR="\$(cd "\$(dirname "\$0")" && pwd)"
echo "腳本所在路徑: \$SCRIPT_DIR"

# 拼接虛擬環境的路徑
VENV_PATH="\$SCRIPT_DIR/.pedestal/bin/activate"

# 檢查虛擬環境是否存在
if [ ! -f "\$VENV_PATH" ]; then
  echo "錯誤：虛擬環境未找到！路徑: \$VENV_PATH"
  exit 1
fi

# 啟動虛擬環境
source "\$VENV_PATH"

# 確認虛擬環境是否成功啟動
if [[ "\$VIRTUAL_ENV" != "" ]]; then
  echo "虛擬環境已成功啟動: \$VIRTUAL_ENV"
else
  echo "虛擬環境啟動失敗！"
  exit 1
fi

# 解析參數
while [[ "\$#" -gt 0 ]]; do
  case "\$1" in
    --zoom) ZOOM="\$2"; shift ;;
    --text_num) TEXT_NUM="\$2"; shift ;;
    --audio_playlist) AUDIO_PLAYLIST="\$2"; shift ;;
    --audio_detach) AUDIO_DETACH="\$2"; shift ;;
    --high_sync) HIGH_SYNC="\$2"; shift ;;
    --detect_interval) DETECT_INTERVAL="\$2"; shift ;;
    *)
      echo "未知參數: \$1"
      exit 1
      ;;
  esac
  shift
done

# 確認所有必要參數是否存在
if [ -z "\$ZOOM" ] || [ -z "\$TEXT_NUM" ] || [ -z "\$AUDIO_PLAYLIST" ] || [ -z "\$AUDIO_DETACH" ] || [ -z "\$HIGH_SYNC" ] || [ -z "\$DETECT_INTERVAL" ]; then
  echo "錯誤: 缺少必要參數。"
  echo "使用方式: \$0 --zoom <value> --text_num <value> --audio_playlist <value> --audio_detach <value> --high_sync <value> --detect_interval <value>"
  exit 1
fi

# 轉換$AUDIO_DETACH 和 $HIGH_SYNC 為布林值
if [ "\$AUDIO_DETACH" = "True" ] || [ "\$AUDIO_DETACH" = "true" ] || [ "\$AUDIO_DETACH" = "1" ]; then
  AUDIO_DETACH="True"
else
  AUDIO_DETACH="False"
fi

if [ "\$HIGH_SYNC" = "True" ] || [ "\$HIGH_SYNC" = "true" ] || [ "\$HIGH_SYNC" = "1" ]; then
  HIGH_SYNC="True"
else
  HIGH_SYNC="False"
fi

# 啟動 Python 腳本
echo "python run.py --zoom \$ZOOM --text_num \$TEXT_NUM --audio_playlist \$AUDIO_PLAYLIST --audio_detach \$AUDIO_DETACH --high_sync \$HIGH_SYNC --detect_interval \$DETECT_INTERVAL"

# 讓程式可以播放聲音
export DISPLAY=:0
export XDG_RUNTIME_DIR=/run/user/\$(id -u)
export PULSE_SERVER=unix:/run/user/\$(id -u)/pulse/native
python sound.py
python run.py --zoom "\$ZOOM" --text_num "\$TEXT_NUM" --audio_playlist "\$AUDIO_PLAYLIST" --audio_detach "\$AUDIO_DETACH" --high_sync "\$HIGH_SYNC" --detect_interval "\$DETECT_INTERVAL"
EOL'

# 設置 run 腳本為可執行
echo "Setting run script as executable..."
sudo chmod +x /etc/service/pedestal_service/run

# 啟動服務
echo "Starting pedestal_service..."
sudo sv start pedestal_service

echo "Installation completed. The pedestal_service is now running."
