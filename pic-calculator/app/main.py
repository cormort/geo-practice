import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

from table_ocr import extract_table

app = FastAPI(title="圖片計算器")

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/", response_class=HTMLResponse)
async def root():
    index_path = os.path.join(STATIC_DIR, "index.html")
    with open(index_path, "r", encoding="utf-8") as f:
        return f.read()


@app.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not (file.content_type or "").startswith("image/"):
        raise HTTPException(status_code=400, detail="請上傳圖片檔案")

    image_bytes = await file.read()
    if len(image_bytes) > 20 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="圖片過大，請上傳 20MB 以下的檔案")

    try:
        result = extract_table(image_bytes)
        table_data = result["data"]
        method = result["method"]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"表格辨識失敗：{e}")

    if not table_data:
        raise HTTPException(status_code=422, detail="未能從圖片中辨識出表格內容")

    return {
        "success": True,
        "method": method,
        "table": table_data,
    }


if __name__ == "__main__":
    import ssl
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)