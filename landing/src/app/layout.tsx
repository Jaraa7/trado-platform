import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TradoAI — منصة التداول الذكي بالـ AI",
  description: "87 وكيل ذكي يعملون 24/7 لمساعدتك في التداول. تحليل عميق، إشارات دقيقة، إدارة مخاطر احترافية للمتداول العربي.",
  keywords: ["AI trading", "تداول بالذكاء الاصطناعي", "crypto", "TradoAI", "تحليل تقني"],
  authors: [{ name: "TradoAI" }],
  openGraph: {
    title: "TradoAI — منصة التداول الذكي",
    description: "AI Trading Platform مع 87 وكيل ذكي",
    url: "https://tradoai.net",
    siteName: "TradoAI",
    locale: "ar_KW",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "TradoAI",
    description: "AI Trading Platform",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ar" dir="rtl">
      <body>
        <div className="grain">{children}</div>
      </body>
    </html>
  );
}
