import os
import asyncio
from flask import Flask
from threading import Thread
from deriv_api import DerivAPI
import google.generativeai as genai

# --- إعداد سيرفر الويب لقبول Koyeb النسخة المجانية ---
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل والتحليل مستمر للمركز الأول بنسبة 99%!"

def run_web_server():
    # Koyeb يستخدم بورت 8080 بشكل افتراضي للنسخة المجانية
    app.run(host='0.0.0.0', port=8080)

# --- إعداد المفاتيح التي قدمتها ---
DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_API_KEY = "AIzaSyB_TvnVQ7ya2FrRhsmGJrtEpa-GK-M7VUg"

# إعداد ذكاء Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# بروتوكول التعليمات الصارمة الخاص بك
STRICT_PROMPT = """
أنت خبير تداول متخصص في الخيارات الثنائية على منصة Deriv.
قواعد مطلقة:
1. لا تعطي أي إشارة (اشترِ أو بِع) إلا إذا كنت متأكدًا 99% من نجاح الصفقة.
2. إذا لم تكن هناك صفقة مضمونة -> الرد الوحيد المسموح هو: "لا توجد صفقة مضمونة حالياً".
3. لا تشرح، لا تعتذر، لا تعطي نصائح عامة.
"""

async def trading_loop():
    try:
        # الاتصال بـ Deriv (App ID 1089 هو الافتراضي للاختبار)
        api = DerivAPI(app_id=1089)
        await api.authorize(DERIV_TOKEN)
        print("✅ تم الاتصال بنجاح.. بدأ البحث عن صفقات الـ 99%")

        while True:
            # قائمة المؤشرات المختارة للمنافسة
            symbols = ['R_75', 'R_100', 'BOOM1000', 'CRASH1000']
            
            for symbol in symbols:
                try:
                    # سحب آخر سعر (Tick)
                    ticks = await api.get_ticks(symbol)
                    price = ticks.get('tick', {}).get('quote')
                    
                    if price:
                        # طلب التحليل من جيميناي
                        analysis_request = f"{STRICT_PROMPT}\nالمؤشر الحالي: {symbol}\nالسعر اللحظي: {price}"
                        response = model.generate_content(analysis_request)
                        
                        # طباعة النتيجة في سجلات (Logs) Koyeb
                        print(f"فحص {symbol}: {response.text.strip()}")
                        
                        # إذا صدرت إشارة، سيتم طباعتها بوضوح في السجلات
                        if "إشارة:" in response.text:
                            print(f"🚀🚀 فرصة ذهبية وجدت: {response.text}")
                
                except Exception as inner_e:
                    print(f"خطأ أثناء فحص {symbol}: {inner_e}")
            
            # الانتظار 15 ثانية قبل الفحص التالي لتجنب ضغط الـ API
            await asyncio.sleep(15)
            
    except Exception as e:
        print(f"❌ خطأ رئيسي في الاتصال: {e}")
        await asyncio.sleep(30)

if __name__ == "__main__":
    # 1. تشغيل واجهة الويب في الخلفية
    t = Thread(target=run_web_server)
    t.start()
    
    # 2. تشغيل عقل البوت (التحليل والتداول)
    asyncio.run(trading_loop())