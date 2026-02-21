import os
import asyncio
import sys
from flask import Flask
from threading import Thread
from deriv_api import DerivAPI 
import google.generativeai as genai
from datetime import datetime

# إعداد المخرجات الفورية لضمان ظهور كل سطر فور حدوثه
os.environ['PYTHONUNBUFFERED'] = '1'

app = Flask('')
@app.route('/')
def home():
    return "✅ Trading Bot Dashboard is Live!"

def run_web_server():
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    app.run(host='0.0.0.0', port=8080)

# --- الإعدادات الفنية ---
DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_API_KEY = "AIzaSyB_TvnVQ7ya2FrRhsmGJrtEpa-GK-M7VUg"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# برومبت احترافي ليعطيك Gemini تحليل دقيق وليس فقط إشارة
STRICT_PROMPT = """
أنت محلل تقني محترف. حلل السعر المعطى بناءً على سلوك السعر (Price Action).
يجب أن يتضمن ردك:
1. اتجاه السوق (صاعد/هابط/متذبذب).
2. مستوى الدعم أو المقاومة القريب.
3. التوصية: (دخول شراء/دخول بيع/انتظار) مع ذكر السبب بنسبة ثقة.
اجعل التحليل دقيقاً ومختصراً في سطرين كحد أقصى.
"""

async def check_market():
    symbols = {'R_75': 'Volatility 75', 'BOOM1000': 'Boom 1000', 'CRASH1000': 'Crash 1000'}
    
    print(f"\n{'#'*60}")
    print(f"⏰ بدء دورة فحص جديدة: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'#'*60}")
    
    try:
        print("🔗 [1/3] محاولة الاتصال بخادم Deriv...", end=" ", flush=True)
        api = DerivAPI(app_id=1089)
        await api.authorize(DERIV_TOKEN)
        print("✅ تم الاتصال.")

        for sym_id, sym_name in symbols.items():
            print(f"\n🔍 [2/3] تحليل مؤشر {sym_name} ({sym_id}):")
            try:
                # جلب السعر
                ticks = await api.ticks(sym_id)
                price = ticks.get('tick', {}).get('quote')
                
                if price:
                    print(f"   📈 السعر اللحظي: {price}")
                    print(f"   🧠 جاري استشارة الذكاء الاصطناعي (Gemini Pro)...", end=" ", flush=True)
                    
                    # تحليل Gemini
                    prompt = f"{STRICT_PROMPT}\nالمؤشر: {sym_name}\nالسعر الحالي: {price}"
                    response = model.generate_content(prompt)
                    analysis = response.text.strip()
                    
                    print("✅ اكتمل التحليل.")
                    
                    # تنسيق العرض المرئي للنتيجة
                    border = "-" * 50
                    print(f"   {border}")
                    if "دخول" in analysis:
                        print(f"   🚨 [إشارة ذهبية]: {analysis}")
                    else:
                        print(f"   ⏳ [مراقبة]: {analysis}")
                    print(f"   {border}")
                
            except Exception as e:
                print(f"   ❌ فشل تحليل {sym_name}: {str(e)}")
        
        print("\n📤 [3/3] إغلاق الجلسة لتوفير الموارد...", end=" ", flush=True)
        await api.disconnect()
        print("✅ في انتظار الدورة القادمة.")

    except Exception as e:
        print(f"\n🛑 خطأ عام في النظام: {e}")

async def main_loop():
    print("\n" + "╔" + "═"*58 + "╗")
    print("║" + " "*15 + "نظام الرادار التحليلي الشامل V2.0" + " "*12 + "║")
    print("╚" + "═"*58 + "╝" + "\n")
    
    while True:
        await check_market()
        print(f"\n💤 استراحة لمدة 40 ثانية لتجنب الحظر...")
        await asyncio.sleep(40)

if __name__ == "__main__":
    Thread(target=run_web_server, daemon=True).start()
    try:
        asyncio.run(main_loop())
    except Exception as e:
        print(f"FATAL ERROR: {e}")
