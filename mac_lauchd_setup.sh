#!/bin/bash
# mac_lauchd_setup.sh
# 本 script 會根據使用者輸入內容建立啟動與關閉的 LaunchDaemon plist 檔案，
# 並將其複製到 /Library/LaunchDaemons/ 內，載入後即可依預定時間以 root 權限執行，
# 其中啟動命令會依據使用者輸入的完整呼叫指令（例如：sudo ./pedestal_activate.sh --dslr --printer_detach True --printer_list I）
# 自動拆解成各個參數（若指令前有 sudo 則自動移除）。

# 請以 root 權限執行本 script
if [[ $EUID -ne 0 ]]; then
  echo "請以 root 權限執行此 script (例如: sudo ./mac_lauchd_setup.sh)"
  exit 1
fi

#############################
# 1. 詢問啟動與關閉時間
#############################
read -p "請輸入啟動時間 (格式 HH:MM): " start_time
read -p "請輸入關閉時間 (格式 HH:MM): " stop_time

# 從時間字串解析小時與分鐘
start_hour=${start_time%%:*}
start_minute=${start_time##*:}
stop_hour=${stop_time%%:*}
stop_minute=${stop_time##*:}

#############################
# 2. 詢問啟動與關閉 script 的路徑
#############################
read -p "請輸入啟動 script 的完整路徑: " start_script
read -p "請輸入關閉 script 的完整路徑: " stop_script

# 簡單檢查檔案是否存在
if [[ ! -f "$start_script" ]]; then
  echo "錯誤：找不到啟動 script，請檢查路徑：$start_script"
  exit 1
fi

if [[ ! -f "$stop_script" ]]; then
  echo "錯誤：找不到關閉 script，請檢查路徑：$stop_script"
  exit 1
fi

#############################
# 3. 詢問呼叫啟動 script 的完整指令
#############################
read -p "請輸入呼叫啟動 script 的完整指令 (例如: sudo ./pedestal_activate.sh --dslr --printer_detach True --printer_list I): " call_command

# 若輸入內容以 "sudo " 開頭，則移除前綴 (plist 內以 root 身份執行即可)
if [[ "$call_command" =~ ^sudo[[:space:]]+ ]]; then
  call_command="${call_command#sudo }"
fi

# 將 call_command 拆解為陣列，假設以空白區隔
read -r -a call_args <<< "$call_command"

#############################
# 4. 修改啟動與關閉 script 權限（使其可執行）
#############################
chmod +x "$start_script"
chmod +x "$stop_script"
echo "已設定啟動及關閉 script 為可執行"

#############################
# 5. 建構 plist 檔案內容
#############################
start_plist="com.user.start.plist"
stop_plist="com.user.stop.plist"

# --- 建立啟動用 plist ---
cat <<EOF > "$start_plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.user.start</string>
    <key>ProgramArguments</key>
    <array>
EOF

# 將 call_args 陣列依序寫入 plist 的 <string> 元素中
for arg in "${call_args[@]}"; do
  echo "      <string>${arg}</string>" >> "$start_plist"
done

cat <<EOF >> "$start_plist"
    </array>
    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>${start_hour}</integer>
      <key>Minute</key>
      <integer>${start_minute}</integer>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/start_script.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/start_script.err</string>
    <key>UserName</key>
    <string>root</string>
  </dict>
</plist>
EOF

# --- 建立關閉用 plist ---
cat <<EOF > "$stop_plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
  <dict>
    <key>Label</key>
    <string>com.user.stop</string>
    <key>ProgramArguments</key>
    <array>
      <string>${stop_script}</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
      <key>Hour</key>
      <integer>${stop_hour}</integer>
      <key>Minute</key>
      <integer>${stop_minute}</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/tmp/stop_script.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/stop_script.err</string>
    <key>UserName</key>
    <string>root</string>
  </dict>
</plist>
EOF

echo "已建立 plist 檔案： $start_plist 與 $stop_plist"

#############################
# 6. 複製 plist 檔案到 /Library/LaunchDaemons/
#############################
# DEST_DIR="/Library/LaunchDaemons"
# cp "$start_plist" "$DEST_DIR/"
# cp "$stop_plist" "$DEST_DIR/"
# echo "已複製 plist 檔案到 $DEST_DIR"

# # 設定 plist 擁有權與權限：owner 為 root:wheel，權限 644
# chown root:wheel "$DEST_DIR/$start_plist" "$DEST_DIR/$stop_plist"
# chmod 644 "$DEST_DIR/$start_plist" "$DEST_DIR/$stop_plist"
# echo "已設定 plist 檔案的擁有權與權限 (root:wheel, 644)"

# #############################
# # 7. 載入 plist 檔案
# #############################
# launchctl unload "$DEST_DIR/$start_plist" 2>/dev/null
# launchctl unload "$DEST_DIR/$stop_plist" 2>/dev/null
# launchctl load "$DEST_DIR/$start_plist"
# launchctl load "$DEST_DIR/$stop_plist"
# echo "LaunchDaemon 已載入： $start_plist 與 $stop_plist"

echo "設定完成。"
