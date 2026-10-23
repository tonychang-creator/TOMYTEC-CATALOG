# Tomica Limited Vintage 前端

此專案採用 Vite + React + Tailwind CSS，完全在瀏覽器端載入 `tomytec_data.json`，不使用後端或資料庫。

## 開發與建置

```powershell
npm install
npm run dev
```

正式靜態建置：

```powershell
npm run build
```

建置結果位於 `dist/`，可直接部署到 GitHub Pages、Netlify 或任何靜態網站主機。

## 長期公開網址：GitHub Pages

本專案已包含 `.github/workflows/deploy.yml`。建立 GitHub repository 後，將這個 `outputs/` 資料夾的內容作為 repository 根目錄推送到 `main` 分支；在 GitHub 的 **Settings → Pages** 將 Source 設為 **GitHub Actions**。每次推送 `main` 都會自動建置並部署，完成後即可從手機以 HTTPS 網址開啟。

部署前請先在本機執行 `npm install`，並將產生的 `package-lock.json` 一併提交，讓 GitHub Actions 的 `npm ci` 能穩定安裝相同依賴版本。

`src/App.jsx` 使用 `useState` 管理搜尋文字、系列頁籤、上市年份及已顯示筆數；再以 `useMemo` 即時過濾 JSON 資料，並依上市年月由新到舊排列（缺少日期的項目置底）。卡片圖片使用原生 `loading="lazy"` 與 `decoding="async"`，每次只建立 20 張產品卡片的 DOM；按「載入更多」才會再加入下一批 20 張。

產品卡片若有 `productUrl` 欄位，點選會在新分頁開啟 Tomytec 的官方產品詳情頁。

## 收藏標記

收藏狀態只從 `tomytec_data.json` 讀取，以確保所有裝置看見相同標記。請在目標物件加入：

```json
"collectionStatus": "owned"
```

可用值為 `"owned"` 和 `"planned"`。`scrape_tomytec.py` 也會依官方圖片網址保留既有的這兩種標記，避免更新爬蟲資料時遺失。

## 增量更新

首次執行新版爬蟲時，請進行完整爬取，以補上每個項目的 `productUrl`：

```powershell
python scrape_tomytec.py --delay 1.5 --output tomytec_data.json
```

之後可使用增量模式；它仍會讀取官方清單頁，卻只會造訪未出現在現有 JSON 的新產品詳情頁，因此可大幅縮短更新時間：

```powershell
python scrape_tomytec.py --delay 1.5 --incremental --output tomytec_data.json
```
