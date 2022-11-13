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
from lib.write_output import OutputManager

logger = logging.getLogger("myLogger")

def generate_sql(api_cfg: APIConfig, gen_cfg: GenerationConfig, db_prompts: Dict[str, Dict[str, str]]):
    data_output_dir = PARENT_DIR / gen_cfg.data_output_dir
    output_queue = deque()
    api_cfg = OmegaConf.to_container(api_cfg)
    
    # Create output manager object to write output to disk
    output_dir = get_output_dir()
    gpt_response_dir = output_dir / "gpt_input_output"
    gpt_response_dir.mkdir()

    exp_time = get_exp_time()
    output_manager = OutputManager(
        exp_time=exp_time,
        exp_output_dir=gpt_response_dir,
        data_output_dir=data_output_dir
    )

    def call_model(
        prompt: str, given_prompt: str, difficulty: str,
        itr: int, db_name: str
    ):
        response = openai.Completion.create(
            prompt=prompt,
            **api_cfg
        )
        result = parse_response(response, gen_cfg.query_prefix)
        result['input'] = prompt
        # Append the output from the model to the prompt
        prompt += f"{result['output']}\n\n{gen_cfg.suffix}"
        # Save the gpt response json, the input/output/query/question
        # To the experiment directory so we keep track of everything
        output_queue.append({(db_name, 'response', itr): response})
        output_queue.append({(db_name, 'input_output', itr): result})
        # Save the question query pair directly to the data dir
        output_queue.append({(db_name, 'pair', itr): 
            {
                'question': result['question'],
                'query': result['query'],
                'prompt': given_prompt,
                'difficulty_of_few_shot': difficulty
            }
        })
        return prompt

    try:
        for db_name, prompts in db_prompts.items():
            itr = 0
            for prompt in prompts:
                diff = prompt["difficulty_of_few_shot"]
                given_prompt = prompt["prompt"]
                text = prompt["text"]
                logger.info(
                    'Generating SQL for db: {} with few shot difficulty: {} and prompt: {}'
                    .format(db_name, diff, given_prompt)
                )
                for _ in range(gen_cfg.n_generations_per_database):
                    logger.debug(f'I am prompt for {db_name} in iteration {itr}\n{text}')
                    try:
                        text = call_model(text, given_prompt, diff, itr, db_name)
                    except RateLimitError:
                        logger.error('We have hit our rate limit. Writing output then sleeping.')
                        seconds_spent = output_manager.write_output(output_queue)
                        logger.debug(f'Spent: {seconds_spent} seconds writing output')
                        time.sleep(61 - seconds_spent)
                        text = call_model(text, given_prompt, diff, itr, db_name)
                    itr += 1
    except Exception as e:
        # If there's an unexpected exception write output then exit
        output_manager.write_output(output_queue)
        raise e
    # Write any remaining output
    seconds_spent = output_manager.write_output(output_queue)
    logger.debug(f'Spent: {seconds_spent} seconds writing output')

def parse_response(response: Dict[str, str], sql_prefix: str) -> Dict[str, str]:
    output = response['choices'][0]['text']
    question, query = output.split(sql_prefix)
    return {'output': output, 'question': question, 'query': query}

@hydra.main(config_path="configs", config_name="gpt", version_base="1.2")
def main(cfg: ExperimentConfig):
    logger.info(OmegaConf.to_yaml(cfg))
    
    prompts = generate_prompts(cfg.generation_cfg)
    
    generate_sql(cfg.api_cfg, cfg.generation_cfg, prompts)

if __name__ == '__main__':
    main()