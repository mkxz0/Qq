import os
import asyncio
from flask import Flask
from threading import Thread
from deriv_api import api as DerivAPI # التعديل هنا ليتوافق مع المكتبة المستقرة
import google.generativeai as genai

# بقية الكود كما هو تماماً (الذي يحتوي على مفاتيحك)
app = Flask('')
@app.route('/')
def home(): return "البوت يعمل والتحليل مستمر!"
def run_web_server(): app.run(host='0.0.0.0', port=8080)

DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_API_KEY = "AIzaSyB_TvnVQ7ya2FrRhsmGJrtEpa-GK-M7VUg"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# بروتوكول التعليمات الصارمة
STRICT_PROMPT = "أنت خبير تداول.. لا تعطي إشارة إلا بنسبة 99% وإلا قل: لا توجد صفقة مضمونة حالياً."

async def trading_loop():
    try:
        # الاتصال بالمكتبة المستقرة
        api = DerivAPI(app_id=1089)
        await api.authorize(DERIV_TOKEN)
        print("✅ متصل بنجاح بالمكتبة المستقرة!")

        while True:
            symbols = ['R_75', 'BOOM1000', 'CRASH1000']
            for symbol in symbols:
                ticks = await api.get_ticks(symbol)
                price = ticks.get('tick', {}).get('quote')
                if price:
                    analysis = model.generate_content(f"{STRICT_PROMPT}\nالمؤشر: {symbol}\nالسعر: {price}")
                    print(f"فحص {symbol}: {analysis.text.strip()}")
            await asyncio.sleep(15)
    except Exception as e:
        print(f"❌ خطأ: {e}")
        await asyncio.sleep(20)

if __name__ == "__main__":
    Thread(target=run_web_server).start()
    asyncio.run(trading_loop())
