// ./components/ModelSelect.tsx

import { NebiusModel } from '@/types/types';
import { FC, Fragment } from 'react';
import { Select, SelectOption } from '@gravity-ui/uikit';

interface Props {
  model: NebiusModel;
  onChange: (model: NebiusModel) => void;
}

export const ModelSelect: FC<Props> = ({ model, onChange }) => {
  const options: SelectOption[] = [
    { 
      value: 'Default (DeepSeek-V3 + Qwen2.5-Coder-32B)', 
      content: (
        <Fragment>
          <strong>Default (DeepSeek-V3 + Qwen2.5-Coder-32B)</strong>
        </Fragment>
      ) 
    },
    { value: 'deepseek-ai/DeepSeek-V3-0324-fast', content: 'DeepSeek-V3-0324' },
    { value: 'Qwen/Qwen2.5-Coder-32B-Instruct-fast', content: 'Qwen2.5-Coder-32B' },
    { value: 'Qwen/QwQ-32B-fast', content: 'QwQ-32B' },
    { value: 'meta-llama/Llama-3.3-70B-Instruct-fast', content: 'Llama-3.3-70B' },
  ];

  return (
    <Select
      value={[model]}
      options={options}
      onUpdate={(value) => onChange(value[0] as NebiusModel)}
      placeholder="Select a model"
      size="m"
      pin="brick-brick"
    />
  );
};
