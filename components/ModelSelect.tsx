// ./components/ModelSelect.tsx

import { NebiusModel } from '@/types/types';
import { FC } from 'react';
import { Select, SelectOption, SelectOptionGroup } from '@gravity-ui/uikit';

interface Props {
  model: NebiusModel;
  onChange: (model: NebiusModel) => void;
}

export const ModelSelect: FC<Props> = ({ model, onChange }) => {
  const options: (SelectOption | SelectOptionGroup)[] = [
    {
      label: 'Fast Models',
      options: [
        { value: 'Qwen/Qwen2.5-Coder-32B-Instruct-fast', content: 'Qwen2.5-Coder-32B-Instruct-fast' },
        { value: 'Qwen/QwQ-32B-fast', content: 'QwQ-32B-fast' },
        { value: 'meta-llama/Llama-3.3-70B-Instruct-fast', content: 'Llama-3.3-70B-Instruct-fast' },
      ],
    },
    {
      label: 'Normal Models',
      options: [
        { value: 'deepseek-ai/DeepSeek-V3', content: 'DeepSeek-V3' },
        { value: 'Qwen/Qwen2.5-Coder-32B-Instruct', content: 'Qwen2.5-Coder-32B-Instruct' },
        { value: 'Qwen/QwQ-32B', content: 'QwQ-32B' },
        { value: 'meta-llama/Llama-3.3-70B-Instruct', content: 'Llama-3.3-70B-Instruct' },
      ],
    },
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
