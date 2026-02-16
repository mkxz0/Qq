# استخدام نسخة بايثون مستقرة
FROM python:3.9-slim

# تثبيت أدوات النظام اللازمة لتحميل المكتبات من GitHub
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

# ضبط مجلد العمل
WORKDIR /app

# تثبيت المكتبات (لاحظ السطر الخاص بـ deriv-api)
RUN pip install --no-cache-dir flask asyncio google-generativeai
RUN pip install --no-cache-dir git+https://github.com/binary-com/python-deriv-api.git

# نسخ ملف الكود الخاص بك
COPY main.py .

# فتح المنفذ المطلوب
EXPOSE 8080

# تشغيل البوت
CMD ["python", "main.py"]
