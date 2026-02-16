# استخدم نسخة بايثون مستقرة جداً ومعروفة بتوافقها
FROM python:3.9-slim

# ضبط مجلد العمل
WORKDIR /app

# تثبيت المكتبات مباشرة هنا لضمان السرعة
RUN pip install --no-cache-dir flask asyncio google-generativeai deriv-api

# نسخ ملف الكود الخاص بك
COPY main.py .

# فتح المنفذ المطلوب
EXPOSE 8080

# تشغيل البوت
CMD ["python", "main.py"]
