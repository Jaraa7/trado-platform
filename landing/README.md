# 🌐 TradoAI Landing Page

> Next.js 15 + Tailwind + Framer Motion — صفحة احترافية بالعربي مع RTL كامل

## 🚀 التشغيل المحلي

```bash
cd landing
npm install
cp .env.example .env.local
npm run dev
```

افتح: http://localhost:3000

## 📦 المحتوى

### الأقسام (Sections):
- ✅ **Navbar** - شريط علوي ذكي مع scroll-aware
- ✅ **Hero** - مع dashboard تفاعلي + form
- ✅ **TrustBar** - منصات التداول المدعومة
- ✅ **Features** - 6 مزايا رئيسية مع icons
- ✅ **HowItWorks** - 3 خطوات بسيطة
- ✅ **Agents** - عرض الـ 87 وكيل في 9 أقسام
- ✅ **Pricing** - 4 باقات + Whale/Institutional/Founder
- ✅ **FAQ** - 8 أسئلة شائعة قابلة للطي
- ✅ **CTA** - Call to action نهائي
- ✅ **Footer** - مع risk disclaimer قانوني

### المزايا:
- ✅ RTL عربي كامل
- ✅ خطوط Premium (Fraunces + IBM Plex Arabic + Geist Mono)
- ✅ Framer Motion animations
- ✅ Dark theme احترافي
- ✅ Responsive (mobile-first)
- ✅ SEO meta tags
- ✅ Glassmorphism + grain texture
- ✅ Gradient mesh backgrounds

## 🚢 النشر على Vercel

### خطوة 1: ربط GitHub
```bash
# تأكد من رفع المشروع
cd ~/trado-platform
git add landing/
git commit -m "🎨 Add Landing Page"
git push origin main
```

### خطوة 2: استيراد في Vercel
1. افتح https://vercel.com/new
2. Import `Jaraa7/trado-platform`
3. **Configure Project:**
   - Framework Preset: `Next.js`
   - Root Directory: `landing`
   - Build Command: `npm run build`
   - Output Directory: `.next`
4. أضف Environment Variables:
   ```
   NEXT_PUBLIC_SITE_URL=https://tradoai.net
   NEXT_PUBLIC_API_URL=https://trado-bot.fly.dev
   ```
5. اضغط **Deploy**

⏱️ 2-3 دقائق للبناء، ثم ستحصل على:
`https://trado-platform.vercel.app`

### خطوة 3: ربط tradoai.net
1. في Vercel: **Settings → Domains**
2. أضف: `tradoai.net` و `www.tradoai.net`
3. Vercel سيعطيك DNS records
4. في Bluehost: **Domains → Manage → DNS**
5. أضف records من Vercel

### خطوة 4: SSL تلقائياً
Vercel يفعّل HTTPS تلقائياً خلال دقائق.

## 🎯 الاختبار

```bash
# Build للإنتاج
npm run build

# تأكد لا توجد أخطاء
npm run lint
```

## 📊 الأداء المتوقع

- **Lighthouse Score:** 95+ في كل المقاييس
- **First Contentful Paint:** <1s
- **Time to Interactive:** <2s
- **Bundle Size:** <300KB gzipped

## 🎨 التخصيص

ملفات يمكنك تعديلها:
- `tailwind.config.js` - الألوان والـ animations
- `src/app/globals.css` - الخطوط والـ effects
- `src/components/sections/*.tsx` - محتوى كل قسم

---

**جاهز للنشر! 🚀**
