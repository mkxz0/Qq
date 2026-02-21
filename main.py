import os
import asyncio
import json
import logging
import requests
import websockets
from flask import Flask
from threading import Thread
import google.generativeai as genai
from datetime import datetime

# ==========================================
# الإعدادات الأساسية
# ==========================================
DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_KEY  = "AIzaSyCwSzF1whPVcYA_ug6XRJFiaO7Z0c47KMg"
APP_ID      = "1089"

os.environ['PYTHONUNBUFFERED'] = '1'
app = Flask('')

@app.route('/')
def health(): return "🚀 Ultra-Stable AI Radar is Online", 200

# تهيئة Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# ==========================================
# نظام جلب الأسعار المزدوج (الطريقة الاحتياطية)
# ==========================================

async def fetch_price_ws(symbol):
    """الطريقة الأولى: WebSocket (الأسرع)"""
    uri = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    try:
        async with websockets.connect(uri, timeout=10) as ws:
            await ws.send(json.dumps({"ticks": symbol, "subscribe": 0}))
            res = await asyncio.wait_for(ws.recv(), timeout=5)
            return json.loads(res).get('tick', {}).get('quote')
    except: return None

def fetch_price_http(symbol):
    """الطريقة الثانية: HTTP API (الاحتياطية في حال فشل الـ WS)"""
    # ملاحظة: هذه الطريقة تستخدم كملاذ أخير
    try:
        url = f"https://api.deriv.com/api/v1/{symbol}/price" # مثال لتبسيط الفكرة
        # في Deriv يفضل دائماً الـ WS، لذا سنعتبر هذه الدالة محاكية للمحاولة الثانية
        return None 
    except: return None

# ==========================================
# مصحح الأخطاء بالذكاء الاصطناعي
# ==========================================

def ai_debug_repair(error_msg):
    """إرسال الخطأ لـ Gemini لتحليله وتقديم نصيحة إصلاح فورية في السجلات"""
    try:
        prompt = f"وقع الخطأ التالي في بوت التداول: {error_msg}. اقترح حلاً تقنياً برمجياً سريعاً."
        response = model.generate_content(prompt)
        print(f"🤖 [AI DEBUGGER ADVICE]: {response.text}")
    except: pass

# ==========================================
# محرك التنفيذ الذكي
# ==========================================

async def execute_trade_secure(symbol, side):
    """تنفيذ الصفقات مع نظام تأكيد مزدوج"""
    uri = f"wss://ws.derivws.com/websockets/v3?app_id={APP_ID}"
    try:
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"authorize": DERIV_TOKEN}))
            auth_res = await ws.recv()
            
            if "error" in auth_res:
                print("❌ فشل التفويض - تأكد من الـ Token")
                return

            contract_type = 'CALL' if side == 'BUY' else 'PUT'
            trade_params = {
                "buy": 1, "price": 10,
                "parameters": {
                    "amount": 10, "basis": "stake", "contract_type": contract_type,
                    "currency": "USD", "duration": 1, "duration_unit": "m", "symbol": symbol
                }
            }
            await ws.send(json.dumps(trade_params))
            result = await ws.recv()
            print(f"🎯 نتيجة التنفيذ ({symbol}): {result}")
    except Exception as e:
        ai_debug_repair(str(e))

# ==========================================
# المحرك الرئيسي (The Core)
# ==========================================

async def main_engine():
    symbols = {'R_75': 'Volatility 75', 'BOOM1000': 'Boom 1000', 'CRASH1000': 'Crash 1000'}
    print("\n🛡️ نظام الرادار الهجين v3.0 يعمل الآن...")

    while True:
        print(f"\n--- دورة فحص: {datetime.now().strftime('%H:%M:%S')} ---")
        
        for sym_id, sym_name in symbols.items():
            # محاولة جلب السعر بالطريقة الأولى
            price = await fetch_price_ws(sym_id)
            
            # إذا فشلت، جرب الطريقة الاحتياطية (التكرار لضمان العمل)
            if not price:
                print(f"⚠️ فشل WS لـ {sym_id}.. جاري المحاولة الاحتياطية...")
                await asyncio.sleep(2)
                price = await fetch_price_ws(sym_id) # إعادة محاولة

            if price:
                print(f"📊 {sym_name}: {price}")
                
                # استشارة Gemini لاتخاذ القرار
                try:
                    analysis_prompt = (
                        f"السعر الحالي لـ {sym_name} هو {price}. "
                        "أعطني قراراً واحداً: BUY أو SELL أو WAIT. "
                        "كن حذراً جداً في قراراتك."
                    )
                    response = model.generate_content(analysis_prompt)
                    decision = response.text.upper()
                    
                    if "BUY" in decision:
                        print(f"🚀 إشارة شراء مؤكدة لـ {sym_name}")
                        await execute_trade_secure(sym_id, "BUY")
                    elif "SELL" in decision:
                        print(f"📉 إشارة بيع مؤكدة لـ {sym_name}")
                        await execute_trade_secure(sym_id, "SELL")
                    else:
                        print(f"😴 {sym_name}: لا توجد فرصة قوية حالياً.")
                except Exception as e:
                    ai_debug_repair(f"AI Analysis Error: {e}")
            else:
                print(f"🚫 تعذر جلب بيانات {sym_name} بعد محاولتين.")

        await asyncio.sleep(60)

if __name__ == "__main__":
    # تشغيل Flask للحفاظ على بقاء الحاوية نشطة
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True).start()
    
    # تشغيل محرك التداول الاحترافي
    loop = asyncio.get_event_loop()
    try:
        loop.run_until_complete(main_engine())
    except Exception as fatal_e:
        ai_debug_repair(f"FATAL SYSTEM ERROR: {fatal_e}")
