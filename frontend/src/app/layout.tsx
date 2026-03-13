import "./globals.css";
import type { Metadata } from "next";

import { siteConfig } from "@/lib/siteConfig";

export const metadata: Metadata = {
  title: `${siteConfig.agentName} | ${siteConfig.schoolName}`,
  description: `${siteConfig.schoolName}${siteConfig.campusLabel}校园餐饮信息服务`,
  icons: {
    icon: "/image/tju-provided-seal.png",
    apple: "/image/tju-provided-seal.png",
  },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
