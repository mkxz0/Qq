import os
import asyncio
import logging
import requests
from flask import Flask
from threading import Thread
from deriv_api import DerivAPI 
import google.generativeai as genai
from datetime import datetime

# ==========================================
# الإعدادات الفنية (البيانات التي قدمتها)
# ==========================================
DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_KEY  = "AIzaSyCwSzF1whPVcYA_ug6XRJFiaO7Z0c47KMg"
TG_TOKEN    = "8556743927:AAHt1-VFztH9Bgp6hWmQDgOZGbl7C38nXr0"
TG_CHAT_ID  = "6163351981"  # تم استنتاجه من سياقك، تأكد منه من @userinfobot

# إعدادات التداول
STAKE_AMOUNT = 10     # مبلغ الصفقة
DURATION     = 1      # المدة
UNIT         = 'm'    # دقائق
# ==========================================

# إعداد السيرفر والذكاء الاصطناعي
os.environ['PYTHONUNBUFFERED'] = '1'
app = Flask('')

@app.route('/')
def health_check():
    return {"status": "online", "bot": "Professional Radar v2.0"}, 200

def send_tg(message):
    """إرسال تنبيهات احترافية لتليجرام"""
    try:
        url = f"https://api.telegram.org/bot{TG_TOKEN}/sendMessage"
        payload = {
            "chat_id": TG_CHAT_ID,
            "text": message,
            "parse_mode": "Markdown"
        }
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Telegram Error: {e}")

# تهيئة Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

async def execute_trade(api, symbol, side, ai_reason):
    """تنفيذ الصفقة على منصة Deriv وإرسال تقرير فوري"""
    contract_type = 'CALL' if side == 'BUY' else 'PUT'
    color_icon = "🟢" if side == "BUY" else "🔴"
    
    try:
        print(f"⚡ تنفيذ عملية {side} على {symbol}...")
        buy_order = await api.buy({
            "buy": 1,
            "price": STAKE_AMOUNT,
            "parameters": {
                "amount": STAKE_AMOUNT,
                "basis": "stake",
                "contract_type": contract_type,
                "currency": "USD",
                "duration": DURATION,
                "duration_unit": UNIT,
                "symbol": symbol
            }
        })
        
        contract_id = buy_order.get('buy', {}).get('contract_id')
        
        # رسالة تليجرام منسقة بشكل احترافي
        report = (
            f"🔔 *إشعار تداول جديد*\n"
            f"━━━━━━━━━━━━━━━\n"
            f"📊 **المؤشر:** `{symbol}`\n"
            f"⚖️ **النوع:** {color_icon} *{side}*\n"
            f"💰 **المبلغ:** `${STAKE_AMOUNT}`\n"
            f"⏳ **المدة:** `{DURATION} {UNIT}`\n"
            f"🆔 **رقم العقد:** `{contract_id}`\n"
            f"━━━━━━━━━━━━━━━\n"
            f"🧠 **تحليل الذكاء الاصطناعي:**\n"
            f"_{ai_reason}_"
        )
        send_tg(report)
        
    except Exception as e:
        error_msg = f"❌ *فشل في تنفيذ الصفقة*\nالمؤشر: {symbol}\nالخطأ: {str(e)}"
        send_tg(error_msg)

async def main_engine():
    """المحرك الرئيسي للرادار والتحليل"""
    symbols = {
        'R_75': 'Volatility 75',
        'BOOM1000': 'Boom 1000 Index',
        'CRASH1000': 'Crash 1000 Index'
    }
    
    send_tg("🚀 *تم إطلاق الرادار الاحترافي v2.0*\nنظام التداول والتحليل الذكي قيد العمل الآن...")
    
    while True:
        api = DerivAPI(app_id=1089)
        try:
            # الاتصال والتفويض
            auth = await api.authorize(DERIV_TOKEN)
            balance = auth.get('authorize', {}).get('balance')
            
            for sym_id, sym_name in symbols.items():
                print(f"🔍 فحص {sym_name}...")
                
                # جلب آخر سعر
                tick = await api.ticks(sym_id)
                price = tick.get('tick', {}).get('quote')
                
                if price:
                    # صياغة طلب التحليل لـ Gemini
                    prompt = (
                        f"أنت خبير تداول خوارزمي. السعر الحالي لـ {sym_name} هو {price}. "
                        f"حلل الحركة المتوقعة في الدقيقة القادمة. "
                        f"أجب بصيغة: [DECISION] ثم اذكر السبب باختصار شديد. "
                        f"القرارات المتاحة: BUY, SELL, WAIT."
                    )
                    
                    response = model.generate_content(prompt)
                    ai_text = response.text.strip()
                    
                    if "BUY" in ai_text.upper():
                        await execute_trade(api, sym_id, "BUY", ai_text)
                    elif "SELL" in ai_text.upper():
                        await execute_trade(api, sym_id, "SELL", ai_text)
                    else:
                        print(f"⏳ {sym_name}: انتظار فرصة أفضل.")
            
            await api.disconnect()
            
        except Exception as e:
            print(f"⚠️ خطأ في الدورة: {e}")
            if "expired" in str(e).lower():
                send_tg("🛑 *خطأ حرج:* يبدو أن هناك مشكلة في المفاتيح البرمجية.")
        
        # استراحة لمدة 60 ثانية لضمان جودة التحليل وعدم حظر الحساب
        await asyncio.sleep(60)

if __name__ == "__main__":
    # تشغيل سيرفر الويب للحفاظ على نشاط البوت في Koyeb
    server = Thread(target=lambda: app.run(host='0.0.0.0', port=8080), daemon=True)
    server.start()
    
    # تشغيل المحرك الرئيسي
    asyncio.run(main_engine())
