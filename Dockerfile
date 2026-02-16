# استخدام نظام بايثون مستقر
FROM python:3.10-slim

# ضبط مجلد العمل داخل الخادم
WORKDIR /app

# نسخ ملف المكتبات وتثبيتها
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ كل ملفات المشروع
COPY . .

# إخبار Koyeb أننا سنستخدم المنفذ 8080
EXPOSE 8080

# الأمر النهائي لتشغيل البوت
CMD ["python", "main.py"]