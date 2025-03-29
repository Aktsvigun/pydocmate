import { StreamLanguage } from '@codemirror/language';
import { python } from '@codemirror/legacy-modes/mode/python';
import { githubLight } from '@uiw/codemirror-theme-github';
import CodeMirror from '@uiw/react-codemirror';
import { FC, useEffect, useState } from 'react';
import { Button, Text } from '@gravity-ui/uikit';
import { Copy } from '@gravity-ui/icons';
import styles from './CodeBlock.module.css';

interface Props {
  code: string;
  editable?: boolean;
  onChange?: (value: string) => void;
}

export const CodeBlock: FC<Props> = ({
  code,
  editable = false,
  onChange = () => {},
}) => {
  const [copyText, setCopyText] = useState<string>('Copy');

  useEffect(() => {
    const timeout = setTimeout(() => {
      setCopyText('Copy');
    }, 2000);

    return () => clearTimeout(timeout);
  }, [copyText]);

  const handleCopy = () => {
    navigator.clipboard.writeText(code);
    setCopyText('Copied!');
  };

  return (
    <div className={styles.container}>
      <div className={styles.codeHeader}>
        <Text variant="body-2" className={styles.codeTitle}>
          {editable ? 'Your code' : 'Generated code'}
        </Text>
        <Button
          view="outlined"
          size="s"
          className={styles.copyButton}
          onClick={handleCopy}
        >
          <Copy width={16} height={16} />
          {copyText}
        </Button>
      </div>

      <CodeMirror
        editable={editable}
        value={code}
        minHeight="500px"
        extensions={[StreamLanguage.define(python)]}
        theme={githubLight}
        onChange={(value) => onChange(value)}
        className={styles.editor}
      />
    </div>
  );
};
