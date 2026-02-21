import os
import asyncio
import logging
from flask import Flask
from threading import Thread
from deriv_api import DerivAPI 
import google.generativeai as genai
from datetime import datetime

# إعداد السجلات لتكون نظيفة وواضحة
os.environ['PYTHONUNBUFFERED'] = '1'
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

app = Flask('')
@app.route('/')
def home(): return "🤖 Bot is Trading on VRTC Account..."

def run_web():
    app.run(host='0.0.0.0', port=8080)

# --- الإعدادات الفنية ---
DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_API_KEY = "AIzaSyDPmfBeSvL9PbVDWWix6HbiaFIiynAu5II"
TRADE_AMOUNT = 10  # مبلغ الصفقة
TRADE_DURATION = 1 # مدة الصفقة (دقيقة واحدة)

genai.configure(api_key=GEMINI_API_KEY)
gemini_model = genai.GenerativeModel('gemini-1.5-pro')

# التعليمات البرمجية للذكاء الاصطناعي
STRICT_PROMPT = """
أنت خبير تداول سكالبينج (Scalping). حلل السعر الحالي للمؤشر.
إذا كان الاتجاه صاعداً بوضوح، أجب بـ: BUY.
إذا كان الاتجاه هابطاً بوضوح، أجب بـ: SELL.
إذا كان السوق متذبذباً أو غير واضح، أجب بـ: WAIT.
ممنوع كتابة أي كلمة أخرى غير هذه الكلمات الثلاث.
"""

async def execute_trade(api, symbol, side):
    """تنفيذ الصفقة على منصة Deriv"""
    contract_type = 'CALL' if side == 'BUY' else 'PUT'
    try:
        print(f"💰 [EXECUTING] إشارة {side} مؤكدة على {symbol}...")
        # إرسال طلب الشراء للمنصة
        result = await api.buy({
            "buy": 1,
            "subscribe": 1,
            "price": TRADE_AMOUNT,
            "parameters": {
                "amount": TRADE_AMOUNT,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": TRADE_DURATION,
                "duration_unit": "m",
                "symbol": symbol
            }
        })
        contract_id = result.get('buy', {}).get('contract_id')
        print(f"✅ [SUCCESS] تم فتح الصفقة! رقم العقد: {contract_id}")
    except Exception as e:
        print(f"❌ [ERROR] فشل التنفيذ: {e}")

async def trading_engine():
    # المؤشرات التي طلبتها
    symbols = {'R_75': 'Volatility 75', 'BOOM1000': 'Boom 1000', 'CRASH1000': 'Crash 1000'}
    
    print("\n" + "╔" + "═"*40 + "╗")
    print("║" + "   نظام التداول الآلي (حساب ديمو)   " + "║")
    print("╚" + "═"*40 + "╝\n")

    while True:
        api = DerivAPI(app_id=1089)
        try:
            # الاتصال والتفويض
            account = await api.authorize(DERIV_TOKEN)
            
            # طباعة معلومات الحساب للتأكد أنه ديمو
            vrtc_login = account.get('authorize', {}).get('loginid')
            balance = account.get('authorize', {}).get('balance')
            print(f"👤 متصل بالحساب: {vrtc_login} | الرصيد: {balance}$")

            for sym_id, sym_name in symbols.items():
                print(f"📡 فحص {sym_name}...", end=" ", flush=True)
                
                # جلب السعر اللحظي
                tick = await asyncio.wait_for(api.ticks(sym_id), timeout=10)
                price = tick.get('tick', {}).get('quote')
                
                if price:
                    # استشارة Gemini لاتخاذ القرار
                    response = gemini_model.generate_content(f"{STRICT_PROMPT}\nالمؤشر: {sym_name}\nالسعر: {price}")
                    decision = response.text.strip().upper()
                    
                    if decision in ["BUY", "SELL"]:
                        print(f"🚀 إشارة {decision}!")
                        await execute_trade(api, sym_id, decision)
                    else:
                        print("⏳ انتظار الفرصة المناسبة...")
            
            await api.disconnect()
        except Exception as e:
            print(f"⚠️ خطأ مؤقت في الاتصال: {e}")
            await asyncio.sleep(5)
        
        # انتظار دقيقة قبل دورة الفحص القادمة (لتجنب فتح صفقات كثيرة جداً)
        print(f"\n💤 استراحة لمدة 60 ثانية...\n{'-'*30}")
        await asyncio.sleep(60)

if __name__ == "__main__":
    # تشغيل سيرفر الويب في الخلفية
    Thread(target=run_web, daemon=True).start()
    # تشغيل محرك التداول
    asyncio.run(trading_engine())
