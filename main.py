import os, asyncio, httpx
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="EX-PRO")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

TELEGRAM_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

async def get_btc():
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("https://api.binance.com/api/v3/ticker/price?symbol=BTCUSDT")
            return float(r.json()["price"])
    except:
        return 0

async def get_gold():
    # Gold via Yahoo Finance XAUUSD
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get("https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X", headers={"User-Agent":"Mozilla/5.0"})
            return float(r.json()["chart"]["result"][0]["meta"]["regularMarketPrice"])
    except:
        try:
            async with httpx.AsyncClient(timeout=5) as c:
                r = await c.get("https://api.metals.dev/v1/latest?api_key=demo&currency=USD&unit=toz")
                return float(r.json()["metals"]["gold"])
        except:
            return 0

@app.get("/api/live")
async def live():
    btc, gold = await asyncio.gather(get_btc(), get_gold())
    return {"BTC": {"price": btc, "symbol": "BTCUSDT"}, "GOLD": {"price": gold, "symbol": "XAUUSD"}, "status": "live"}

@app.get("/api/test-telegram")
async def test_telegram():
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return {"ok": False, "error": "Telegram not configured - add env vars in Render"}
    async with httpx.AsyncClient(timeout=10) as c:
        r = await c.post(f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage", json={"chat_id": TELEGRAM_CHAT_ID, "text": "✅ EX-PRO is LIVE on Render - Telegram works!"})
        return {"ok": r.status_code == 200, "telegram": r.json()}

@app.get("/", response_class=HTMLResponse)
async def home():
    return """
    <!DOCTYPE html><html><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
    <title>EX-PRO LIVE</title>
    <style>body{background:#0a0a0a;color:#fff;font-family:sans-serif;text-align:center;padding:20px}
    .card{background:#1a1a1a;border:1px solid #333;border-radius:16px;padding:20px;margin:15px auto;max-width:400px}
    .price{font-size:32px;font-weight:bold;color:#00ff88}.gold{color:#ffd700}
    button{background:#00ff88;border:0;padding:12px 20px;border-radius:10px;font-weight:bold;cursor:pointer}
    </style></head><body>
    <h1>🚀 EX-PRO <span style='color:#00ff88'>LIVE</span></h1>
    <div class='card'><h2>₿ BITCOIN</h2><div class='price' id='btc'>Loading...</div><div id='btc-time'></div></div>
    <div class='card'><h2>🥇 GOLD</h2><div class='price gold' id='gold'>Loading...</div><div id='gold-time'></div></div>
    <button onclick="testTg()">📩 Test Telegram</button><p id='tg'></p>
    <script>
    async function load(){try{let r=await fetch('/api/live');let d=await r.json();
    document.getElementById('btc').innerText='$'+Number(d.BTC.price).toLocaleString();
    document.getElementById('gold').innerText='$'+Number(d.GOLD.price).toLocaleString();
    let t=new Date().toLocaleTimeString();document.getElementById('btc-time').innerText=t;document.getElementById('gold-time').innerText=t;
    }catch(e){}} load(); setInterval(load,5000);
    async function testTg(){let r=await fetch('/api/test-telegram');let d=await r.json();document.getElementById('tg').innerText=JSON.stringify(d)}
    </script></body></html>
    """

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", 8000)))
