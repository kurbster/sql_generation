#!/usr/bin/env python3
import sys
import time
import logging

from typing import Dict
from collections import deque
from pathlib import Path
PARENT_DIR = Path(__file__, '../..').resolve()
sys.path.append(str(PARENT_DIR))

import hydra
import openai

from omegaconf import OmegaConf
from openai.error import RateLimitError

from src.config import (
    APIConfig, ExperimentConfig, GenerationConfig,
    get_output_dir, get_exp_time
)

from lib.create_few_shot_prompt import generate_prompts
from lib.write_output import write_output

logger = logging.getLogger('apiLogger')

def query_model(api_cfg: APIConfig, gen_cfg: GenerationConfig, prompts: Dict[str, str]) -> Dict[str, str]:
    output_queue = deque()
    api_cfg = OmegaConf.to_container(api_cfg)
    def call_model(prompt, itr, db_name):
        # response = openai.Completion.create(
            # prompt=prompt,
            # **api_cfg
        # )
        response = {"choices": [{"text": 
        " Give me the formuoli\nSQL: select ravioli from formuoli"
        }]}
        result = parse_response(response, gen_cfg.query_prefix)
        result['input'] = prompt
        # Append the output from the model to the prompt
        prompt += f"{result['output']}\n\n{gen_cfg.suffix}"
        # Save the gpt response json, the input/output/query/question
        # To the experiment directory so we keep track of everything
        output_queue.append({(db_name, 'response', itr): response})
        output_queue.append({(db_name, 'result', itr): result})
        # Save the question query pair directly to the data dir
        output_queue.append({(db_name, 'pair', itr): 
            {'question': result['question'], 'query': result['question']}
        })
        return prompt

    for db_name, prompt in prompts.items():
        for i in range(gen_cfg.n_generations_per_database):
            logger.info(f'I am prompt for {db_name} in {i} iteration\n{prompt}')
            try:
                prompt = call_model(prompt, i, db_name)
            except RateLimitError:
                logger.error('We have hit our rate limit. Writing output then sleeping.')
                seconds_spent = write_output(output_queue)
                logger.debug(f'Spent: {seconds_spent} writing output')
                time.sleep(61 - seconds_spent)
                prompt = call_model(prompt)
    # Write any remaining output
    write_output(output_queue)

def parse_response(response: Dict[str, str], sql_prefix: str) -> Dict[str, str]:
    output = response['choices'][0]['text']
    question, query = output.split(sql_prefix)
    return {'output': output, 'question': question, 'query': query}

@hydra.main(config_path="configs", config_name="gpt", version_base="1.2")
def main(cfg: ExperimentConfig):
    logger.info(OmegaConf.to_yaml(cfg))
    
    prompts = generate_prompts(cfg.generation_cfg)
    
    output_dir = get_output_dir()
    gpt_responses = output_dir / "gpt_input_output"
    gpt_responses.mkdir()

    query_model(cfg.api_cfg, cfg.generation_cfg, prompts)

if __name__ == '__main__':
    main()