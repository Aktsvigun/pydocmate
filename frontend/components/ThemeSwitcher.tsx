import { Display, Moon, Sun } from "@gravity-ui/icons";
import { Icon, SegmentedRadioGroup } from "@gravity-ui/uikit";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";

import styles from "./ThemeSwitcher.module.css";

export const ThemeSwitcher = () => {
  const { theme, resolvedTheme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);

  // When mounted on client, use the theme from next-themes
  useEffect(() => {
    setMounted(true);
    console.log("ThemeSwitcher mounted, current theme:", theme, "resolved theme:", resolvedTheme);
  }, [theme, resolvedTheme]);

  // Log theme changes
  const handleThemeChange = (newTheme: string) => {
    console.log("Setting theme to:", newTheme);
    setTheme(newTheme);
  };

  if (!mounted) {
    return null;
  }

  return (
    <SegmentedRadioGroup value={theme} onUpdate={handleThemeChange}>
      <SegmentedRadioGroup.Option value="light" content={<Icon data={Sun} className={styles.icon} />} />
      <SegmentedRadioGroup.Option value="system" content={<Icon data={Display} className={styles.icon} />} />
      <SegmentedRadioGroup.Option value="dark" content={<Icon data={Moon} className={styles.icon} />} />
    </SegmentedRadioGroup>
  );
}; 