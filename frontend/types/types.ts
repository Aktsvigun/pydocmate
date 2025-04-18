export type NebiusModel = 'Qwen/Qwen2.5-Coder-32B-Instruct-fast' | 'deepseek-ai/DeepSeek-V3-0324-fast' | 'Qwen/QwQ-32B-fast' | 'meta-llama/Llama-3.3-70B-Instruct-fast' | 'Default (DeepSeek-V3 + Qwen2.5-Coder-32B)';

export interface CodeBody {
  inputCode: string;
  model: NebiusModel;
  modifyExistingDocumentation: boolean;
  doWriteArgumentsAnnotations: boolean;
  doWriteDocstrings: boolean;
  doWriteComments: boolean;
  apiKey: string;
}

export interface DocumentResponse {
  code: string;
}
