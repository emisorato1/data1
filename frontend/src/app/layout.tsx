import type { Metadata } from "next";
import { DM_Sans } from "next/font/google";
import "./globals.css";
import { ThemeProvider } from "@/components/theme-provider";

const dmSans = DM_Sans({
    subsets: ["latin"],
    weight: ["400", "500", "600", "700", "800"], // Regular, Medium, Semibold, Bold, ExtraBold
    variable: "--font-dm-sans",
});

export const metadata: Metadata = {
    title: "Banco Macro | IA Platform",
    description: "Acceso seguro a documentación bancaria interna",
    icons: {
        icon: "/favicon.svg",
    },
};

export default function RootLayout({
    children,
}: Readonly<{
    children: React.ReactNode;
}>) {
    return (
        <html lang="es" suppressHydrationWarning>
            <body className={`${dmSans.variable} font-sans antialiased`} suppressHydrationWarning>
                <ThemeProvider
                    attribute="class"
                    defaultTheme="system"
                    enableSystem
                >
                    {children}
                </ThemeProvider>
            </body>
        </html>
    );
}
