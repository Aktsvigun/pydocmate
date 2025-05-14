import { Button, ThemeProvider, useLayoutContext } from "@gravity-ui/uikit";
import Image from "next/image";
import Link from "next/link";

import styles from "./Header.module.css";

export const Header = () => {
  const { isMediaActive } = useLayoutContext();

  return (
    <ThemeProvider theme="dark" scoped rootClassName={styles.root}>
      <header className={styles.header}>
        <div className={styles.left}>
          {isMediaActive("l") && <span className={styles.poweredText}>Powered with</span>}
          <Image 
            src="/nebius-logo.svg" 
            width={102} 
            height={37} 
            className={styles.logo} 
            alt="Nebius"
            priority
          />
        </div>
        <nav className={styles.right}>
          <ul className={styles.navigationList}>
            <li>
              <Link
                href="https://github.com/nebius/ai-studio-solutions"
                target="_blank"
                className={styles.link}
              >
                <Image 
                  src="/github.svg" 
                  width={20} 
                  height={20} 
                  alt="GitHub"
                  priority
                />
                {isMediaActive("m") && "GitHub"}
              </Link>
            </li>
            <li>
              <Button
                view="outlined-contrast"
                size={isMediaActive("l") ? "l" : "m"}
                pin="circle-circle"
                href="https://nebius.com/services/studio-inference-service"
                target="_blank"
              >
                Build your AI app
              </Button>
            </li>
          </ul>
        </nav>
      </header>
    </ThemeProvider>
  );
}; 