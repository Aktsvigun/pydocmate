import Head from 'next/head';
import { useEffect, useState } from 'react';
import { CodeBlock } from '@/components/CodeBlock';
// import { APIKeyInput } from '@/components/APIKeyInput';
import { ModelSelect } from '@/components/ModelSelect';
import { NebiusModel, CodeBody } from '@/types/types';
import { Header } from '@/components/Header';
import { Footer } from '@/components/Footer';
import { Button, Checkbox, Switch, Text, useLayoutContext } from '@gravity-ui/uikit';
import styles from '@/styles/Home.module.css';

export default function Home() {
  const { isMediaActive } = useLayoutContext();
  // We only have one code input and one code output
  const [inputCode, setInputCode] = useState<string>('');
  const [outputCode, setOutputCode] = useState<string>('');

  // Model selection
  const [model, setModel] = useState<NebiusModel>(
    'deepseek-ai/DeepSeek-V3',
  );

  // Four booleans
  const [modifyExistingDocumentation, setModifyExistingDocumentation] = useState<boolean>(true);
  const [doWriteArgumentsAnnotations, setDoWriteArgumentsAnnotations] = useState<boolean>(true);
  const [doWriteDocstrings, setDoWriteDocstrings] = useState<boolean>(true);
  const [doWriteComments, setDoWriteComments] = useState<boolean>(true);

  // General state
  const [loading, setLoading] = useState<boolean>(false);
  const [apiKey, setApiKey] = useState<string>('');

  // Load any existing API key from localStorage if you want it
  useEffect(() => {
    const storedKey = localStorage.getItem('apiKey');
    if (storedKey) {
      setApiKey(storedKey);
    }
  }, []);

  const handleApiKeyChange = (value: string) => {
    setApiKey(value);
    localStorage.setItem('apiKey', value);
  };

  const handleDocument = async () => {
    // Basic checks
    if (!inputCode.trim()) {
      alert('Please enter some Python code first.');
      return;
    }

    setLoading(true);
    setOutputCode('');

    try {
      // Prepare request body
      const body: CodeBody = {
        inputCode,
        model,
        modifyExistingDocumentation,
        doWriteArgumentsAnnotations,
        doWriteDocstrings,
        doWriteComments,
        apiKey, // not explicitly needed by your local server, but included in the type
      };

      const response = await fetch('/api/document', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
      });

      if (!response.ok) {
        setLoading(false);
        alert('Error calling backend /api/document.');
        return;
      }

      // SSE streaming response
      const reader = response.body?.getReader();
      if (!reader) {
        setLoading(false);
        alert('No readable stream returned by the server.');
        return;
      }

      const decoder = new TextDecoder();
      let done = false;

      while (!done) {
        const { value, done: doneReading } = await reader.read();
        done = doneReading;
        if (value) {
          const chunkValue = decoder.decode(value);
          setOutputCode(chunkValue); // Set state with the latest response
        }
      }


      setLoading(false);
    } catch (err) {
      console.error(err);
      setLoading(false);
      alert('Error streaming from backend.');
    }
  };

  return (
    <>
      <Head>
        <title>Python Code Documentation Assistant</title>
        <meta name="description" content="Use Nebius AI Studio to document your Python code." />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </Head>

      <div className={styles.container}>
        <Header />
        
        <main className={styles.main}>
          <div className={styles.title}>
            <Text variant="display-4" as="h1">
              Python Code Documentation Assistant
            </Text>
          </div>

          <div className={styles.controls}>
            <ModelSelect model={model} onChange={(val) => setModel(val)} />
            <Button
              view="normal"
              size={isMediaActive("l") ? "xl" : "m"}
              loading={loading}
              onClick={handleDocument}
              disabled={loading}
            >
              {loading ? 'Annotating your code...' : 'Submit'}
            </Button>
          </div>

          <div className={styles.checkboxes}>
            <Switch
              checked={modifyExistingDocumentation}
              onChange={(e) => setModifyExistingDocumentation(e.target.checked)}
              className={styles.nebiusSwitch}
            >
              Modify existing documentation
            </Switch>
            <Switch
              checked={doWriteArgumentsAnnotations}
              onChange={(e) => setDoWriteArgumentsAnnotations(e.target.checked)}
              className={styles.nebiusSwitch}
            >
              Write arguments annotations
            </Switch>
            <Switch
              checked={doWriteDocstrings}
              onChange={(e) => setDoWriteDocstrings(e.target.checked)}
              className={styles.nebiusSwitch}
            >
              Write docstrings
            </Switch>
            <Switch
              checked={doWriteComments}
              onChange={(e) => setDoWriteComments(e.target.checked)}
              className={styles.nebiusSwitch}
            >
              Write comments
            </Switch>
          </div>

          <div className={styles.codeBlocks}>
            <div className={styles.codeBlock}>
              <Text variant="display-2" as="h2" className={styles.codeBlockTitle}>
                Input Code
              </Text>
              <CodeBlock
                code={inputCode}
                editable={!loading}
                onChange={(val) => setInputCode(val)}
              />
            </div>

            <div className={styles.codeBlock}>
              <Text variant="display-2" as="h2" className={styles.codeBlockTitle}>
                Documented Code
              </Text>
              <CodeBlock
                code={outputCode}
                editable={false}
                onChange={() => {}}
              />
            </div>
          </div>
        </main>
        
        <Footer />
      </div>
    </>
  );
}