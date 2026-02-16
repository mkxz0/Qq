import os
import asyncio
from deriv_api import DerivAPI
import google.generativeai as genai

# جلب المفاتيح من إعدادات Koyeb (Environment Variables)
GEMINI_KEY = os.environ.get(AIzaSyB_TvnVQ7ya2FrRhsmGJrtEpa-GK-M7VUg)
DERIV_TOKEN = os.environ.get(uEMydREZrU7cARO)

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

STRICT_PROMPT = "أنت خبير تداول بظروف صارمة.. لا تعطي إشارة إلا بنسبة 99% وإلا قل: لا توجد صفقة مضمونة حالياً."

async def trading_loop():
    try:
        api = DerivAPI(app_id=1089)
        await api.authorize(DERIV_TOKEN)
        print("✅ متصل بـ Deriv.. بدأ البحث عن صفقات الـ 99%")

        while True:
            # مسح المؤشرات الأكثر ربحاً في المسابقات
            for symbol in ['R_75', 'BOOM1000', 'CRASH1000', 'R_100']:
                ticks = await api.get_ticks(symbol)
                price = ticks.get('tick', {}).get('quote')
                
                # إرسال البيانات لـ Gemini
                analysis = model.generate_content(f"{STRICT_PROMPT} \n المؤشر: {symbol} \n السعر اللحظي: {price}")
                
                if "إشارة:" in analysis.text:
                    print(f"🚀 [إشارة 99%] في {symbol}: {analysis.text}")
                
            await asyncio.sleep(15) # فاصل زمني لحماية الحساب من الحظر
    except Exception as e:
        print(f"❌ خطأ: {e}")
        await asyncio.sleep(30) # إعادة المحاولة بعد نصف دقيقة

if __name__ == "__main__":
    asyncio.run(trading_loop())
