import type { Metadata } from "next";
import { Syne, DM_Sans } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";

const syne = Syne({
  subsets: ["latin"],
  weight: ["700", "800"],
  variable: "--font-syne-var",
  display: "swap",
});

const dmSans = DM_Sans({
  subsets: ["latin"],
  weight: ["400", "500"],
  style: ["normal", "italic"],
  variable: "--font-dm-sans-var",
  display: "swap",
});

export const metadata: Metadata = {
  title: "GOATflow",
  description: "Grab life by the horns. Leave the bull behind.",
  icons: { icon: "/assets/goatflow_appstore_logo_1773963712043.webp" },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`${syne.variable} ${dmSans.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-goat-black text-goat-white">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
