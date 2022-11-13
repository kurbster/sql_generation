import sys
import json
import random
import logging

from typing import List
from pathlib import Path
PARENT_DIR = Path(__file__, '../..').resolve()
sys.path.append(str(PARENT_DIR))
PATH_TO_MAIN_DIR = Path(__file__, '../../..').resolve()
sys.path.append(str(PATH_TO_MAIN_DIR))

import hydra

from omegaconf import OmegaConf

from src.config import GenerationConfig, ExperimentConfig

PATH_TO_FEW_SHOT = PATH_TO_MAIN_DIR / 'few_shot_prompts'

logger = logging.getLogger("myLogger")

def generate_prompts(cfg: GenerationConfig) -> List[str]:
    if cfg.few_shot_file == "":
        raise NotImplementedError(
            "Auto Few shotting is not yet implemented ",
            "You must provide a human annotated few shot file."
        )

    path_to_few_shot_file = PATH_TO_MAIN_DIR / cfg.few_shot_file
    assert path_to_few_shot_file.exists(), f"The few shot file: {path_to_few_shot_file} didn't exist"

    few_shot_prompt = get_few_shot_from_file(path_to_few_shot_file, cfg)

    with open(PATH_TO_FEW_SHOT / cfg.meta_few_shot_file) as f:
        meta_few_shot = json.load(f)

    prompts = {}
    # Here we should iterate through all of the databases
    # But for testing lets just use the architecture db
    dbs = ['architecture', 'aircraft']
    for db in dbs:
        # This is for when we iterate over Path objects
        # db_name = db.name
        db_name = db
        few_shot_examples = meta_few_shot[db_name]
        with open(PATH_TO_FEW_SHOT / db_name / cfg.new_schema_few_shot_name) as f:
            new_schema = f.read()

        # TODO: Maybe make this a dict comprehension.
        db_prompts = []
        for prompt in cfg.prompts:
            for difficulty, examples in few_shot_examples.items():
                few_shot_example = random.sample(examples, 1)[0]
                new_few_shot = "{}{}\n{}{}\n".format(
                    cfg.question_prefix, few_shot_example['question'],
                    cfg.query_prefix, few_shot_example['query']
                )
                db_prompts.append({
                    'difficulty_of_few_shot': difficulty,
                    'prompt': prompt,
                    'text': '\n'.join(
                        few_shot_prompt + [new_schema, prompt, new_few_shot, cfg.suffix]
                    )
                })
            # Include prompt with no extra few shot
            db_prompts.append({
                'difficulty_of_few_shot': 'None',
                'prompt': prompt,
                'text': '\n'.join(
                    few_shot_prompt + [new_schema, prompt, cfg.suffix]
                )
            })
        prompts[db_name] = db_prompts
    
    return prompts

def get_few_shot_from_file(path_to_few_shot_file: Path, cfg: GenerationConfig) -> List[str]:
    with open(path_to_few_shot_file) as f:
        few_shots = f.read()
    few_shot_prompt = [
        cfg.header, cfg.table_prefix, few_shots, cfg.table_prefix
    ]
    return few_shot_prompt

@hydra.main(config_path="../configs", config_name="gpt", version_base="1.2")
def main(cfg: ExperimentConfig):
    logger.info(OmegaConf.to_yaml(cfg))
    
    db_prompts = generate_prompts(cfg.generation_cfg)
    for db_name, prompts in db_prompts.items():
        for prompt in prompts:
            logger.info(f'input:\n{prompt["text"]}')
            logger.info(f'db: {db_name} diff: {prompt["difficulty_of_few_shot"]}')

if __name__ == '__main__':
    main()