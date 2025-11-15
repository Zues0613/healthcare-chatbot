import type { Metadata } from "next";
import { Inter } from "next/font/google";
import { Suspense } from "react";
import "./globals.css";
import NavigationLoader from "../components/NavigationLoader";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "Health Assistant - AI-Powered Health Information",
  description:
    "Get reliable health information and guidance. Not a substitute for professional medical advice.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <Suspense fallback={null}>
          <NavigationLoader />
        </Suspense>
        {children}
      </body>
    </html>
  );
}