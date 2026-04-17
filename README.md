# 高等統計品質報告 — 牛仔褲腰圍製程管制

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/你的GitHub帳號/你的Repo名稱/HEAD?labpath=高等統計品質報告.ipynb)

## 說明

本報告模擬牛仔褲生產線的腰圍量測數據，並使用 **X-bar R** 與 **X-bar S** 管制圖進行製程品質分析。

### 內容涵蓋
- 模擬 40 批 × 5 件 = 200 筆腰圍量測資料
- SQLite 資料庫儲存與讀取
- X̄-R 管制圖分析
- X̄-S 管制圖分析
- 互動式 GUI（僅限本地執行）

### 使用方式

**線上互動執行（Binder）：**  
點擊上方 `launch binder` 徽章，等待環境啟動後即可在瀏覽器中執行所有 cell。

> ⚠️ **注意**：最後的 tkinter GUI 介面需要本地桌面環境，在 Binder 中無法啟動視窗，但所有計算與圖表 cell 均可正常執行。

**本地執行：**
```bash
pip install numpy pandas matplotlib
jupyter notebook 高等統計品質報告.ipynb
```
