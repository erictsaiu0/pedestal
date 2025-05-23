# 藝術展台互動裝置

這是一個藝術展台的互動裝置系統，當有物品放置在展台上時，系統會自動辨識並以語音描述該物品是否為藝術品。

## 系統需求

- macOS 或 Linux 作業系統
- Python版本 3.8~3.12
- 網路攝影機
- 喇叭或音響設備

## 安裝步驟
0. 安裝python、git必要套件
   - 除了screen以外，樹莓派皆已安裝，可直接跳過，此步驟主要針對macOS
   - 建議安裝python版本: 3.12.5(目前測試3.13.1會有package問題)
      - 若是macOS，安裝homebrew
         ```bash
         /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
         ```
      - 以brew 安裝pyenv ，安裝指定版本python
         ```bash
         brew install pyenv
         pyenv install 3.12.5
         PATH="~/.pyenv/shims:${PATH}"
         pyenv global 3.12.5
         ```
      - 確認安裝成功
         ```bash
         python3 --version
         ```

   - 安裝git
      ```bash
      brew install git
      ```
   - 安裝screen(樹莓派也需安裝)
      在mac 上可以使用 brew 安裝
      ```bash
      brew install screen
      ```
      樹莓派以及其他linux 系統可以使用 apt 安裝
      ```bash
      sudo apt-get install screen
      ```
1. 下載程式碼
   - 先進到想放這個專案資料夾的資料夾，如Desktop、Documents等，亦可直接在原處建立資料夾，可輸入pwd確認當前資料夾
      ```bash
      cd Desktop
      ```
   - 下載專案程式碼
      ```bash
      git clone https://github.com/erictsaiu0/pedestal.git
      cd pedestal
      ```

2. 建立虛擬環境、安裝必要套件
   - 在專案根目錄建立 `venv` 虛擬環境
     ```bash
     python3 -m venv .pedestal
     ```
   - 將必要套件安裝到虛擬環境中
     ```bash
     source .pedestal/bin/activate
     pip install -r requirements.txt
     ```

3. 設定 OpenAI API 金鑰
   - 在專案根目錄建立 `KEYS.py` 檔案
   - 將您的 OpenAI API 金鑰填入該檔案:
     ```python
     OPENAI_KEY = "您的 OpenAI API 金鑰"
     ```

## 使用說明
0. 若是未設定過裝置 IP 或是換過基地台，請先確認裝置 IP(此步驟建議於該裝置上連接螢幕鍵鼠進行設定)
   - 樹莓派確認 IP 位址
      - 連上wifi後，將游標移動到wifi圖示上，會自動顯示該裝置的 IP 位址 
      - 或是在桌面打開 terminal 後，輸入 `ifconfig` 可以看到該裝置的 IP 位址
   - macOS確認 IP 位址
      － 在終端機中輸入 `ifconfig` 稍作尋找，可以看到該裝置的 IP 位址，通常為 `192.168.XX.XX`

1. ssh 登入樹莓派
   - 依照不同的樹莓派IP，在終端機輸入 `ssh raspberrypi@192.168.XX.XX`，系統會要求輸入密碼，若是第一次進行ssh，會詢問是否允許登入，輸入 `yes` 即可   

2. 進到pedestal目錄並進入虛擬環境
   ```bash
   cd pedestal
   source .pedestal/bin/activate
   ```

3. 若是未設定過裝置 IP 或是換過基地台，請更改device_ip.py中的IP位址
   - 打開 `device_ip.py`
   - 修改 `addr_dict` 中的 IP 位址對應關係

4. 校正zoom參數
   - 可用其他macOS電腦進行測試，請參考章節[其他](#其他)
   - 執行test.py可以測試攝影機的zoom參數
      ```bash
      python test.py
      ```
   執行後會開啟攝影機預覽視窗，可以透過調整zoom參數來找到最適合的縮放程度。
   按下 'q' 鍵可以關閉預覽視窗，關閉後終端機畫面會呈現最終需要的zoom參數

5. screen使用以及更新程式碼（optional）
   - screen是一個終端機管理工具，可以讓程式在背景執行，即使關閉終端機視窗也不會中斷程式
      ```bash
      # 建立新的screen session
      screen -S [session名稱 如isart]
      
      # 列出所有screen session
      screen -ls
      
      # 重新連接screen session
      screen -r [前面取過的session名稱 如isart]
      
      # 結束screen session（在session中輸入）
      exit
      ```
   - 如果程式有需要更新，或已經經過修改，請先更新後再執行
      ```bash
      git pull
      ```

6. 啟動展台系統
   ```bash
   python run.py --zoom 5 --text_num 50 --audio_playlist I
   ```
   參數說明：
   - zoom: 攝影機縮放程度 (預設為 5)
   - text_num: 描述文字長度 (預設為 50)
   - audio_playlist: 播放內容，可依照希望的播放順序設定，如I(僅播放Isart)、DIN（依序播放Describe、Isart、Notart）
   - audio_detach: 聲音分離，若設定為True，則會將聲音播放到其他設備上，若設定為False，則會將聲音播放到本設備上，若要在其他設備上播放聲音，須在其他裝置先行執行web_socket.py，見後方說明。
   - high_sync: 預設為False，低延遲模式，多語音分離播放時若啟動，裝置間播放的間隔時間會比較接近。
   - detect_interval: 預設為5，檢測頻率，越高的話會隔越久才會觸發一次。

7. 聲音分離使用
   - 若要使用聲音分離功能，需要在播放聲音的設備上執行web_socket.py
   - 首先確認device_ip.py中的IP設定正確
   - 在各個播放聲音的設備上執行web_socket.py
      ```bash
      # 在isart設備上
      python web_socket.py --id isart
      
      # 在notart設備上
      python web_socket.py --id notart
      
      # 在describe設備上
      python web_socket.py --id describe
      ```
   
   - 執行展台程式時加上audio_detach參數
      ```bash
      python run.py --zoom 5 --text_num 50 --audio_playlist DIN --audio_detach True
      ```

8. 使用方式
   - 將物品放置在展台上
   - 系統會自動偵測物品並進行辨識
   - 透過語音播放辨識結果

## 自動化設置
   - 先執行更改權限的指令
      ```bash
      chmod +x pi_activate.sh pi_setup.sh server_activate.sh server_setup.sh
      ```
   - 對於各台作為聲音分離播放的樹莓派，執行以下指令即完成設置，注意<id>請自行更改為isart、notart、describe中的一個
      ```bash
      ./pi_activate.sh <id>
      ```
      - 確認設置是否成功，重開機後登入screen並輸入 `screen -r <id>`

   - 對於作為server的樹莓派，執行以下指令即完成設置，注意<zoom>等參數請自行更改為最終設置的參數，因此請先行用前方的執行方式完成測試取得參數後再執行此設定指令
      ```bash
      ./server_setup.sh <zoom> <text_num> <audio_playlist> <audio_detach> <high_sync> <detect_interval>
      ```
      - 確認設置是否成功，重開機後登入screen並輸入 `screen -r server`
   
## 其他
1. 以其他MacOS系統之電腦進行webcam測試(test.py)
   - 直接進到pedestal目錄，直接點兩下test.command程式即可，過程中程式會詢問要攝影機編號，請從0開始測試直到選到正確的攝影機。
2. 樹莓派遠端調整音量
   - ssh進入樹莓派，並執行以下程式即可調整音量
      ```bash
      amixer set Master 100%
      ```
      

## 注意事項

1. 確保網路攝影機正確連接且運作正常
2. 確保音響設備已連接並可正常播放
3. 系統需要穩定的網路連線以使用 OpenAI API
4. 請確保環境光線充足，以利系統進行物品辨識

## 常見問題

1. 如果無法偵測到攝影機：
   - 確認攝影機是否正確連接
   - 重新啟動程式

2. 如果沒有聲音輸出：
   - 檢查音響設備連接
   - 確認系統音量設定

3. 如果辨識結果不準確：
   - 調整環境光線
   - 確保物品放置位置正確
   - 調整 text_num 參數以獲得更詳細的描述


