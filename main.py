import os
import asyncio
import logging
from flask import Flask
from threading import Thread
from deriv_api import DerivAPI 
import google.generativeai as genai
from datetime import datetime

# ==========================================
# الإعدادات الفنية الأساسية
# ==========================================
DERIV_TOKEN = "uEMydREZrU7cARO"
GEMINI_KEY  = "AIzaSyCwSzF1whPVcYA_ug6XRJFiaO7Z0c47KMg"

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
    return "🤖 Radar Bot is Scanning Markets...", 200

def run_web_server():
    app.run(host='0.0.0.0', port=8080)

# تهيئة Gemini
genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-pro')

async def execute_trade(api, symbol, side, ai_reason):
    """تنفيذ الصفقة على منصة Deriv وطباعة التفاصيل في السجلات"""
    contract_type = 'CALL' if side == 'BUY' else 'PUT'
    
    try:
        print(f"⚡ [EXECUTION] محاولة فتح صفقة {side} على {symbol}...")
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
        print(f"✅ [SUCCESS] تم التنفيذ بنجاح! رقم العقد: {contract_id}")
        print(f"🧠 [AI REASON]: {ai_reason}")
        print(f"{'━'*50}")
        
    except Exception as e:
        print(f"❌ [TRADE ERROR] فشل في تنفيذ الصفقة: {e}")

async def main_engine():
    """المحرك الرئيسي للرادار: جلب السعر، التحليل، التنفيذ"""
    symbols = {
        'R_75': 'Volatility 75',
        'BOOM1000': 'Boom 1000 Index',
        'CRASH1000': 'Crash 1000 Index'
    }
    
    print("\n" + "🚀" * 5 + " انطلاق نظام التداول الآلي الاحترافي " + "🚀" * 5)
    
    while True:
        api = DerivAPI(app_id=1089)
        try:
            # الاتصال والتفويض
            auth = await api.authorize(DERIV_TOKEN)
            account_id = auth.get('authorize', {}).get('loginid')
            balance = auth.get('authorize', {}).get('balance')
            
            print(f"\n🕒 الوقت: {datetime.now().strftime('%H:%M:%S')}")
            print(f"👤 الحساب: {account_id} | 💰 الرصيد: {balance}$")
            
            for sym_id, sym_name in symbols.items():
                # جلب السعر اللحظي بدقة
                try:
                    tick_data = await asyncio.wait_for(api.ticks({"ticks": sym_id, "subscribe": 0}), timeout=10)
                    price = tick_data.get('tick', {}).get('quote')
                except:
                    continue

                if price:
                    print(f"🔍 فحص {sym_name} (السعر الحالي: {price})...", end=" ", flush=True)
                    
                    # طلب التحليل من Gemini
                    prompt = (
                        f"أنت خبير تداول. السعر الحالي لـ {sym_name} هو {price}. "
                        f"هل تتوقع صعوداً (BUY) أم هبوطاً (SELL) في الدقيقة القادمة؟ "
                        f"أجب بكلمة واحدة (BUY/SELL/WAIT) ثم السبب باختصار."
                    )
                    
                    try:
                        response = model.generate_content(prompt)
                        ai_text = response.text.strip()
                        
                        if "BUY" in ai_text.upper():
                            print("🚀 [إشارة شراء]")
                            await execute_trade(api, sym_id, "BUY", ai_text)
                        elif "SELL" in ai_text.upper():
                            print("📉 [إشارة بيع]")
                            await execute_trade(api, sym_id, "SELL", ai_text)
                        else:
                            print("⏳ [انتظار]")
                    except Exception as ai_err:
                        print(f"⚠️ خطأ في تحليل AI: {ai_err}")
            
            await api.disconnect()
            
        except Exception as e:
            print(f"⚠️ خطأ عام في النظام: {e}")
        
        # الانتظار لمدة دقيقة بين كل فحص
        print(f"💤 استراحة قصيرة لتحديث البيانات...")
        await asyncio.sleep(60)

if __name__ == "__main__":
    # تشغيل سيرفر الويب في الخلفية للحفاظ على نشاط Koyeb
    Thread(target=run_web_server, daemon=True).start()
    
    # تشغيل محرك التداول
    try:
        asyncio.run(main_engine())
    except KeyboardInterrupt:
        print("🛑 تم إيقاف البوت يدوياً.")
