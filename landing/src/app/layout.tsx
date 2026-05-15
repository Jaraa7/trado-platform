import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "TradoAI — Trading Intelligence Beyond Limits",
  description: "87 specialized AI tools working 24/7 to analyze markets, find opportunities, and protect your capital.",
  openGraph: {
    title: "TradoAI",
    description: "87 AI tools. One platform.",
    url: "https://tradoai.net",
    siteName: "TradoAI",
    type: "website",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html suppressHydrationWarning>
      <body suppressHydrationWarning>{children}</body>
    </html>
  );
}
