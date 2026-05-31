import './globals.css';
import type { Metadata } from 'next';

export const metadata: Metadata = {
  title: 'Social Analyst RAG Dashboard',
  description: 'Advanced Video Analysis Platform',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="bg-gray-50 text-gray-900 min-h-screen antialiased">
        {children}
      </body>
    </html>
  );
}