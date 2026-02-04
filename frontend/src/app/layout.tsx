import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({
    subsets: ["latin"],
    variable: "--font-inter",
});

export const metadata: Metadata = {
    title: "LegacyLens | AI-Powered Code Modernization",
    description: "Transform legacy C++/Java codebases into modern Python/Next.js using local LLMs and agentic workflows",
    keywords: ["code modernization", "AI", "C++", "Java", "Python", "refactoring", "LangGraph"],
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="en" className="dark">
            <body className={`${inter.variable} font-sans antialiased`}>
                {children}
            </body>
        </html>
    );
}
