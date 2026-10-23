# Tomytec TLV 資料爬蟲

`scrape_tomytec.py` 會從以下官方系列頁所使用的官方產品搜尋 API 取得全部產品卡片，依序造訪詳情頁，並輸出 JSON 陣列：

- `https://minicar.tomytec.co.jp/lineup/tlv/`
- `https://minicar.tomytec.co.jp/lineup/tlvneo/`

每筆資料為：

```json
{
  "series": "TLV",
  "modelNumber": "LV-198a",
  "name": "マツダ ポーターキャブ 三方開（緑）フィギュア付",
  "releaseDate": "2021年12月",
  "imageUrl": "https://..."
}
```

## 執行方式

請在本目錄開啟終端機後執行：

```powershell
python -m pip install -r requirements.txt
python scrape_tomytec.py --delay 1.5 --output tomytec_data.json
```

首次執行可先用下列指令驗證（每個系列只讀取第一頁）：

```powershell
python scrape_tomytec.py --delay 1.5 --max-pages-per-series 1 --output tomytec_data_test.json
```

預設每次 HTTP 請求之間會等待 1.5 秒；可用 `--delay 2` 加長間隔。程式不會平行請求、也不會下載圖片。官方的系列頁以 JavaScript 載入產品，因此此版本改讀取該網站本身使用的 `/product/api/search.php` 端點，而非假設系列頁 HTML 已包含產品連結。

輸出的 `tomytec_data.json` 可直接放進純前端網站，例如以 `fetch('./tomytec_data.json')` 載入。

若官方搜尋結果包含未標示 `LV` 或 `LV-N` 型號的相關項目，程式會保留該筆資料並標示為 `"series": "Other"`，其 `modelNumber` 為空字串。
