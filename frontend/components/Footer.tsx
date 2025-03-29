import { Text } from "@gravity-ui/uikit";
import styles from "./Footer.module.css";
import { ThemeSwitcher } from "./ThemeSwitcher";

export const Footer = () => {
  return (
    <footer className={styles.footer}>
      <Text variant="body-2" color="secondary">
        © {new Date().getFullYear()} Powered by Nebius. Intelligent document analysis.
      </Text>
      <ThemeSwitcher />
    </footer>
  );
}; 