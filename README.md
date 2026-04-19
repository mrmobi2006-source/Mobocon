# 🤖 MOBO TUNNEL Bot - دليل النشر الكامل

## 📋 المتطلبات
- Python 3.11+
- استضافة تدعم Python (Render / Railway / VPS)

> ⚠️ **ملاحظة مهمة:** Netlify لا تدعم Python bots لأنها serverless. استخدم **Render.com** أو **Railway.app** مجاناً.

---

## 🚀 النشر على Render.com (مجاني - موصى به)

1. سجّل في https://render.com
2. اضغط **New → Web Service**
3. ارفع المجلد أو اربطه بـ GitHub
4. اضبط الإعدادات:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`
   - **Environment:** Python 3
5. أضف متغير البيئة:
   - `BOT_TOKEN` = `8741656871:AAEFrxiiRqvDYBxT7sS7FofW0YSP6VYGJXQ`
   - `BOT_USERNAME` = اسم مستخدم البوت (بدون @)
6. اضغط **Deploy**

---

## 🚀 النشر على Railway.app (مجاني)

1. سجّل في https://railway.app
2. اضغط **New Project → Deploy from GitHub**
3. أضف متغيرات البيئة نفسها
4. سيعمل تلقائياً

---

## 🚀 النشر على VPS (Ubuntu)

```bash
# تثبيت المتطلبات
pip install -r requirements.txt

# تشغيل البوت
python bot.py

# أو في الخلفية:
nohup python bot.py &

# أو مع systemd:
sudo nano /etc/systemd/system/mobotunnel.service
```

محتوى ملف systemd:
```ini
[Unit]
Description=MOBO TUNNEL Bot
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/path/to/bot
ExecStart=/usr/bin/python3 bot.py
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable mobotunnel
sudo systemctl start mobotunnel
```

---

## ⚙️ الإعداد الأولي بعد التشغيل

### 1. إضافة البوت كمشرف في قناتك
- اذهب إلى القناة → المشرفون → إضافة مشرف
- ابحث عن البوت وأضفه بصلاحيات: نشر الرسائل، تعديل الرسائل

### 2. الحصول على ID القناة
- أرسل رسالة في القناة
- أرسلها لـ @userinfobot أو استخدم: `https://api.telegram.org/bot{TOKEN}/getUpdates`
- ستجد `chat.id` وهو رقم يبدأ بـ `-100`

### 3. أوامر الإعداد الأساسية
```
/addchannel -1001234567890 اسم القناة
/setlogo  (ثم أرسل صورة)
/setdesc internet وصف ملفات الإنترنت
/setdesc youtube وصف ملفات اليوتيوب
/setreactions 1
```

---

## 📱 أوامر البوت الكاملة

### للمستخدمين
| الأمر | الوظيفة |
|-------|---------|
| /start | بدء البوت |
| /getfile | احصل على أحدث ملف |
| /help | المساعدة |

### للمشرفين
| الأمر | الوظيفة |
|-------|---------|
| /admin | لوحة التحكم |
| /publish | نشر ملف جديد |
| /stats | الإحصائيات |
| /addchannel [id] [name] | إضافة قناة |
| /removechannel [id] | حذف قناة |
| /channels | قائمة القنوات |
| /setdesc [type] [text] | تعديل وصف نوع |
| /setlogo | تعيين شعار |
| /setreactions [n] | عدد التفاعلات المطلوبة |

### للمشرف الرئيسي فقط (ID: 6154678499)
| الأمر | الوظيفة |
|-------|---------|
| /addadmin [id] [channels] | إضافة مشرف |
| /removeadmin [id] | حذف مشرف |
| /admins | قائمة المشرفين |
| /broadcast [msg] | رسالة لجميع المستخدمين |
| /addfiletype [id] [emoji] [name] | إضافة نوع ملف جديد |
| /filetypes | أنواع الملفات |

---

## 🔧 كيفية نشر ملف

1. أرسل `/publish` للبوت
2. اختر نوع الملف (يوتيوب / إنترنت مجاني)
3. أرسل الملف
4. أرسل صورة شعار (اختياري)
5. أرسل وصف المنشور أو `-` للافتراضي
6. اختر القناة

سيتم النشر تلقائياً مع **3 أزرار**:
- ⚡ فعّل البوت أولاً (زر كبير)
- ❤️ تفاعل | 📥 استلام الملف

---

## 🔐 ميزات الأمان
- ✅ منع تحميل أو تحويل الملفات (`protect_content=True`)
- ✅ التحقق من التفاعل قبل إرسال الملف
- ✅ صلاحيات منفصلة لكل مشرف
- ✅ تقييد القنوات لكل مشرف

---

## 📞 الدعم
المشرف الرئيسي ID: `6154678499`
