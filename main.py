import os
import asyncio
import sys
from flask import Flask
from threading import Thread
# الاستيراد الصحيح للمكتبة الرسمية
from deriv_api import DerivAPI 
import google.generativeai as genai

# ضمان ظهور المخرجات فوراً في سجلات Koyeb
os.environ['PYTHONUNBUFFERED'] = '1'

# --- 1. إعداد سيرفر الويب للتمويه (Flask) ---
app = Flask('')

@app.route('/')
def home():
    return "✅ البوت يعمل والتحليل مستمر!"

def run_web_server():
    print("🌐 [Web] جاري تشغيل سيرفر الويب على المنفذ 8080...", flush=True)
    app.run(host='0.0.0.0', port=8080)

# --- 2. إعداد المفاتيح والذكاء الاصطناعي ---
DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_API_KEY = "AIzaSyB_TvnVQ7ya2FrRhsmGJrtEpa-GK-M7VUg"

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

# بروتوكول التعليمات الصارمة (STRICT PROMPT)
STRICT_PROMPT = """
أنت خبير تداول محترف في المؤشرات الصناعية.
قم بتحليل السعر الحالي للمؤشر.
إذا كانت هناك فرصة ربح بنسبة 99%، حدد "شراء" أو "بيع" مع السبب باختصار.
إذا لم تكن متأكداً تماماً، رد فقط بـ: "لا توجد صفقة مضمونة حالياً".
"""

# --- 3. حلقة التداول والتحليل الأساسية ---
async def trading_loop():
    print("🚀 [System] بدء تشغيل محرك التحليل...", flush=True)
    try:
        # الاتصال بمنصة Deriv
        api = DerivAPI(app_id=1089)
        await api.authorize(DERIV_TOKEN)
        print("✅ [Deriv] تم الاتصال بالحساب بنجاح!", flush=True)

        symbols = ['R_75', 'BOOM1000', 'CRASH1000']
        
        while True:
            for symbol in symbols:
                try:
                    # جلب بيانات السعر
                    ticks = await api.ticks(symbol)
                    price = ticks.get('tick', {}).get('quote')
                    
                    if price:
                        # إرسال البيانات لجيميناي للتحليل
                        prompt = f"{STRICT_PROMPT}\nالمؤشر: {symbol}\nالسعر الحالي: {price}"
                        response = model.generate_content(prompt)
                        
                        # طباعة التحليل في السجلات
                        print(f"📊 [{symbol}] السعر: {price} | التحليل: {response.text.strip()}", flush=True)
                    
                except Exception as inner_e:
                    print(f"⚠️ [Warning] خطأ أثناء فحص {symbol}: {inner_e}", flush=True)
            
            # انتظار 20 ثانية قبل الفحص التالي
            await asyncio.sleep(20)

    except Exception as e:
        print(f"❌ [Error] خطأ رئيسي في الاتصال: {e}", flush=True)
        await asyncio.sleep(60) # انتظر دقيقة قبل إعادة المحاولة

# --- 4. نقطة الانطلاق ---
if __name__ == "__main__":
    # تشغيل سيرفر الويب في الخلفية
    t = Thread(target=run_web_server, daemon=True)
    t.start()
    
    # تشغيل حلقة التداول (Async)
    asyncio.run(trading_loop())
