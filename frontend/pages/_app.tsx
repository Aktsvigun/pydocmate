import { ThemeProvider as GravityThemeProvider, configure } from '@gravity-ui/uikit';
import { ThemeProvider, useTheme } from 'next-themes';
import "../styles/globals.css";
import type { AppProps } from "next/app";
import { Inter } from "next/font/google";
import { useEffect, useState } from "react";

const inter = Inter({ subsets: ["latin"] });

// Configure Gravity UI
configure({
  lang: 'en',
});

function ThemedApp({ Component, pageProps }: AppProps<{}>) {
  const { resolvedTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  const [gravityTheme, setGravityTheme] = useState<'light' | 'dark'>('light');

  // Only update the theme after mounting to avoid hydration mismatch
  useEffect(() => {
    setMounted(true);
  }, []);

  useEffect(() => {
    if (mounted) {
      console.log("Resolved theme:", resolvedTheme);
      setGravityTheme(resolvedTheme === 'dark' ? 'dark' : 'light');
    }
  }, [resolvedTheme, mounted]);

  // If not mounted yet, use a generic fallback or return null
  if (!mounted) {
    // Return a generic placeholder without GravityThemeProvider
    // to avoid server-side useLayoutEffect issues.
    // This might cause a flash of unstyled content (FOUC) for Gravity components,
    // but should help prevent the hydration mismatch warning and potential reloads.
    return (
      <main className={inter.className}>
        <div style={{ visibility: 'hidden' }}>Loading...</div>
      </main>
    );
  }

  return (
    <GravityThemeProvider theme={gravityTheme}>
      <main className={inter.className}>
        <Component {...pageProps} />
      </main>
    </GravityThemeProvider>
  );
}

function App(props: AppProps<{}>) {
  return (
    <ThemeProvider attribute="data-theme" defaultTheme="system" enableSystem>
      <ThemedApp {...props} />
    </ThemeProvider>
  );
}

export default App;
