export type NebiusModel = 'Qwen/Qwen2.5-Coder-32B-Instruct-fast' | 'deepseek-ai/DeepSeek-V3-0324-fast' | 'Qwen/QwQ-32B-fast' | 'meta-llama/Llama-3.3-70B-Instruct-fast' | 'Default (DeepSeek-V3 + Qwen2.5-Coder-32B)' | 'Qwen/Qwen3-235B-A22B' | 'Qwen/Qwen3-30B-A3B-fast';

export interface CodeBody {
  inputCode: string;
  model: NebiusModel;
  modifyExistingDocumentation: boolean;
  doWriteArgumentsAnnotations: boolean;
  doWriteDocstrings: boolean;
  doWriteComments: boolean;
  annotateWithAny: boolean;
  apiKey: string;
}

export interface DocumentResponse {
  code: string;
}
