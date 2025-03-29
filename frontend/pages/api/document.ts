import { CodeBody, DocumentResponse } from '@/types/types';
export const config = {
  runtime: 'edge',
};

const handler = async (req: Request): Promise<Response> => {
  try {
    const {
      inputCode,
      model,
      modifyExistingDocumentation,
      doWriteArgumentsAnnotations,
      doWriteDocstrings,
      doWriteComments,
      // apiKey
    } =
      (await req.json()) as CodeBody;

    // Try both hostname and IP to ensure connectivity
    const backendUrl = process.env.NODE_ENV === 'production' 
      ? 'http://backend:4000' 
      : 'http://172.20.0.2:4000';
    
    console.log(`Connecting to backend at: ${backendUrl}`);
    
    const response = await fetch(`${backendUrl}/document`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: inputCode,
        model_checkpoint: model,
        modify_existing_documentation: modifyExistingDocumentation,
        do_write_arguments_annotations: doWriteArgumentsAnnotations,
        do_write_docstrings: doWriteDocstrings,
        do_write_comments: doWriteComments,
        // api_key: apiKey
      }),
    });

    if (!response.ok) {
      throw new Error(`Backend error: ${response.statusText}`);
    }

    return new Response(response.body, {
      headers: {
        'Content-Type': 'text/event-stream',
      },
    });

  } catch (error) {
    console.error(error);
    return new Response('Error', { status: 500 });
  }
};

export default handler;
