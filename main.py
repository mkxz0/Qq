import os
import asyncio
import json
import websockets
from flask import Flask
from threading import Thread
import google.generativeai as genai
from datetime import datetime

# --- إعدادات ثابتة ---
DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_KEY  = "AIzaSyCwSzF1whPVcYA_ug6XRJFiaO7Z0c47KMg"
APP_ID      = "1089"

os.environ['PYTHONUNBUFFERED'] = '1'
app = Flask('')

@app.route('/')
def health(): return "📡 Stable Radar V5.0: Forced Close Protocol Active", 200

# تهيئة Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

async def secure_request(request_body):
    """
    هذه الدالة تفتح الاتصال، تنفذ الطلب، وتغلقه بقوة (Hard Close)
    لتجنب تحذير no close frame المستمر.
    """
    uri = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    ws = None
    try:
        # الاتصال مع تحديد ping_interval لإبقاء الاتصال منضبطاً
        ws = await websockets.connect(uri, ping_interval=None)
        await ws.send(json.dumps(request_body))
        
        # انتظار الرد مع مهلة زمنية
        response = await asyncio.wait_for(ws.recv(), timeout=10)
        
        # إغلاق الاتصال فوراً قبل معالجة البيانات
        await ws.close() 
        return json.loads(response)
    except Exception as e:
        if ws: await ws.close()
        print(f"⚠️ [Connection Logic Error]: {e}")
        return None

async def main_loop():
    symbols = {'R_75': 'Volatility 75', 'BOOM1000': 'Boom 1000', 'CRASH1000': 'Crash 1000'}
    print("\n✅ نظام البروتوكول المستقر V5 مفعّل.")
    print("🚀 جاري فحص الأسواق بدون تحذيرات اتصال...")

    while True:
        for sym_id, sym_name in symbols.items():
            # طلب السعر
            data = await secure_request({"ticks": sym_id, "subscribe": 0})
            price = data.get('tick', {}).get('quote') if data else None
            
            if price:
                print(f"📊 {sym_name}: {price}")
                # استشارة الذكاء الاصطناعي
                try:
                    prompt = f"Price of {sym_name} is {price}. Decision: BUY, SELL, or WAIT? (One word only)"
                    decision = model.generate_content(prompt).text.upper()
                    
                    if "BUY" in decision or "SELL" in decision:
                        side = "BUY" if "BUY" in decision else "SELL"
                        # تنفيذ الصفقة بطلب مستقل وإغلاق فوري
                        print(f"⚡ تنفيذ إشارة {side}...")
                        await secure_request({"authorize": DERIV_TOKEN})
                        trade_req = {
                            "buy": 1, "price": 10,
                            "parameters": {
                                "amount": 10, "basis": "stake", "contract_type": 'CALL' if side=="BUY" else 'PUT',
                                "currency": "USD", "duration": 1, "duration_unit": "m", "symbol": sym_id
                            }
                        }
                        await secure_request(trade_req)
                except Exception as e:
                    print(f"❌ خطأ في التحليل: {e}")
            
        await asyncio.sleep(60)

if __name__ == "__main__":
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()
    asyncio.run(main_loop())
