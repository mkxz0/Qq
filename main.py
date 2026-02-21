import os
import asyncio
import logging
from flask import Flask
from threading import Thread
from deriv_api import DerivAPI 
import google.generativeai as genai
from datetime import datetime

# 1. تنظيف السجلات وإعداد السيرفر
os.environ['PYTHONUNBUFFERED'] = '1'
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')
@app.route('/')
def home(): return "🤖 Trading Bot is Executing..."

def run_web():
    app.run(host='0.0.0.0', port=8080)

# 2. الإعدادات (تأكد من صلاحيات Trade في الـ Token)
DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_API_KEY = "AIzaSyB_TvnVQ7ya2FrRhsmGJrtEpa-GK-M7VUg"
TRADE_AMOUNT = 10  # مبلغ الصفقة بالدولار
TRADE_DURATION = 1 # مدة الصفقة
DURATION_UNIT = 'm' # بالدقائق

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-pro')

STRICT_PROMPT = """
أنت محرك تنفيذ صفقات عالي الدقة. حلل السعر المعطى.
إذا كانت هناك فرصة ربح مؤكدة بنسبة 90% أو أكثر، أجب بكلمة واحدة فقط: "BUY" أو "SELL".
إذا لم تكن متأكداً، أجب بكلمة: "WAIT".
لا تشرح السبب، أريد كلمة واحدة فقط لاتخاذ القرار البرمجي.
"""

async def execute_trade(api, symbol, side):
    """وظيفة تنفيذ الصفقة في منصة Deriv"""
    contract_type = 'CALL' if side == 'BUY' else 'PUT'
    try:
        print(f"💰 [EXECUTING] جاري فتح صفقة {side} على {symbol} بمبلغ {TRADE_AMOUNT}$...")
        proposal = await api.buy({
            "buy": 1,
            "subscribe": 1,
            "price": TRADE_AMOUNT,
            "parameters": {
                "amount": TRADE_AMOUNT,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": TRADE_DURATION,
                "duration_unit": DURATION_UNIT,
                "symbol": symbol
            }
        })
        print(f"✅ [SUCCESS] تم فتح الصفقة بنجاح! رقم العملية: {proposal.get('buy', {}).get('contract_id')}")
    except Exception as e:
        print(f"❌ [FAILED] فشل تنفيذ الصفقة: {e}")

async def trading_engine():
    symbols = {'R_75': 'Volatility 75', 'BOOM1000': 'Boom 1000', 'CRASH1000': 'Crash 1000'}
    
    print("\n" + "🚀" * 10)
    print("نظام التنفيذ التلقائي بدأ العمل الآن")
    print("🚀" * 10 + "\n")

    while True:
        api = DerivAPI(app_id=1089)
        try:
            await api.authorize(DERIV_TOKEN)
            now = datetime.now().strftime('%H:%M:%S')
            
            for sym_id, sym_name in symbols.items():
                print(f"🕒 {now} | فحص {sym_name}...", end=" ", flush=True)
                
                tick = await asyncio.wait_for(api.ticks(sym_id), timeout=10)
                price = tick.get('tick', {}).get('quote')
                
                if price:
                    # استشارة Gemini
                    response = gemini_model.generate_content(f"{STRICT_PROMPT}\nالمؤشر: {sym_name}\nالسعر الحالي: {price}")
                    decision = response.text.strip().upper()
                    
                    if "BUY" in decision:
                        print("🟢 إشارة شراء!")
                        await execute_trade(api, sym_id, 'BUY')
                    elif "SELL" in decision:
                        print("🔴 إشارة بيع!")
                        await execute_trade(api, sym_id, 'SELL')
                    else:
                        print("🟡 انتظار...")
            
            await api.disconnect()
        except Exception as e:
            print(f"⚠️ خطأ في الدورة: {e}")
        
        # الفحص كل 60 ثانية لتجنب التكرار السريع جداً
        await asyncio.sleep(60)

if __name__ == "__main__":
    Thread(target=run_web, daemon=True).start()
    asyncio.run(trading_engine())
