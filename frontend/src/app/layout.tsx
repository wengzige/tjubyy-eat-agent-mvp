import "./globals.css";
import type { Metadata } from "next";

import { siteConfig } from "@/lib/siteConfig";

export const metadata: Metadata = {
  title: `${siteConfig.agentName} Agent`,
  description: `${siteConfig.schoolName}校园餐饮推荐 MVP`,
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
