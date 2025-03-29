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

    const response = await fetch('http://localhost:1488/document', {
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