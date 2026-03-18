import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Takasbank PDF Translator",
  description: "On-premise PDF translation portal",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="tr">
      <body>{children}</body>
    </html>
  );
}
