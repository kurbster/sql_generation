import sys
import json
import random
import logging
import textwrap

from typing import List, Dict
from pathlib import Path
PARENT_DIR = Path(__file__, '../..').resolve()
sys.path.append(str(PARENT_DIR))
PATH_TO_MAIN_DIR = Path(__file__, '../../..').resolve()
sys.path.append(str(PATH_TO_MAIN_DIR))

import hydra

from omegaconf import OmegaConf

from src.config import GenerationConfig, ExperimentConfig, CodexGenerationConfig

PATH_TO_FEW_SHOT = PATH_TO_MAIN_DIR / 'few_shot_prompts'

logger = logging.getLogger("myLogger")

# TODO: Rewrite this to match how we generate for Codex. Make this a List of Dict
# where the db_name is a key in the dict
def generate_prompts(cfg: GenerationConfig) -> Dict[str, List[Dict[str, str]]]:
    if cfg.few_shot_file == "":
        raise NotImplementedError(
            "Auto Few shotting is not yet implemented ",
            "You must provide a human annotated few shot file."
        )

    path_to_few_shot_file = PATH_TO_MAIN_DIR / cfg.few_shot_file
    assert path_to_few_shot_file.exists(), f"The few shot file: {path_to_few_shot_file} didn't exist"

    few_shot_db_name = path_to_few_shot_file.parent.name
    few_shot_prompt = get_few_shot_from_file(path_to_few_shot_file, cfg)

    with open(PATH_TO_FEW_SHOT / cfg.meta_few_shot_file) as f:
        meta_few_shot = json.load(f)

    prompts = {}
    # Here we should iterate through all of the databases
    # But for testing lets just use the architecture db
    # dbs = ['architecture', 'aircraft']
    # for db in dbs:
        # db_name = db
        # few_shot_examples = meta_few_shot[db_name]
        # with open(PATH_TO_FEW_SHOT / db_name / cfg.new_schema_few_shot_name) as f:
            # new_schema = f.read()

    not_complete = [
        "gymnast",
        "game_injury",
        "twitter_1",
        "book_2",
        "student_1",
        "store_1",
        "scientist_1",
        "county_public_safety",
        "ship_mission",
        "inn_1",
        "csu_1",
        "flight_company",
        "club_1",
        "theme_gallery",
        "performance_attendance",
        "entertainment_awards",
        "election",
        "flight_1",
        "wrestler",
        "flight_4",
        "swimming",
        "candidate_poll",
        "geo",
        "game_1",
        "network_2",
        "music_4",
        "perpetrator",
        "manufactory_1",
        "musical",
        "loan_1",
        "hospital_1",
        "program_share",
        "company_office",
        "cinema",
        "entrepreneur",
        "election_representative",
        "academic",
        "sports_competition",
        "match_season",
        "bike_1"
    ]

    for db in PATH_TO_FEW_SHOT.iterdir():
        if not db.is_dir():
            continue
 
        db_name = db.name
        # Skip creating a prompt for the db from the few shot file
        if db_name == few_shot_db_name:
            continue

        if db_name not in not_complete:
            continue
        few_shot_examples = meta_few_shot[db_name]
        with open(db / cfg.new_schema_few_shot_name) as f:
            new_schema = f.read()

        # TODO: Maybe make this a dict comprehension.
        db_prompts = []
        for prompt in cfg.prompts:
            for difficulty, examples in few_shot_examples.items():
                if difficulty != "easy":
                    continue
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
            # db_prompts.append({
                # 'difficulty_of_few_shot': 'None',
                # 'prompt': prompt,
                # 'text': '\n'.join(
                    # few_shot_prompt + [new_schema, prompt, cfg.suffix]
                # )
            # })
        prompts[db_name] = db_prompts
    
    return prompts

def get_few_shot_from_file(path_to_few_shot_file: Path, cfg: GenerationConfig) -> List[str]:
    with open(path_to_few_shot_file) as f:
        few_shots = f.read()
    few_shot_prompt = [
        cfg.header, cfg.table_prefix, few_shots, cfg.table_prefix
    ]
    return few_shot_prompt

def generate_codex_prompts(cfg: CodexGenerationConfig) -> List[Dict[str, str]]:
    # TODO: Add few shotting to codex prompts
    all_few_shot_schemas = read_all_schemas(cfg)
    prompts = []
    for dname, fname in cfg.input_data_files.items():
        with open(PATH_TO_MAIN_DIR / fname) as f:
            dataset = json.load(f)
        for data in dataset:
            db_name = data[cfg.db_key]
            schema = all_few_shot_schemas[db_name]
            prompt = "\n".join([
                cfg.header, cfg.table_prefix, schema,
            ])
            # We want the suffix and question to be on the same line right after the schema
            prompt += f"{cfg.suffix} {data[cfg.question_key]}"
            prompts.append({
                'dataset_name': dname,
                'db_id': db_name,
                'question': data[cfg.question_key],
                'gold_sql': data[cfg.query_key],
                'text': prompt,
            })
    return prompts

def read_all_schemas(cfg: CodexGenerationConfig) -> Dict[str, str]:
    schemas = {}
    for dpath in PATH_TO_FEW_SHOT.iterdir():
        if dpath.is_file():
            continue
        db_name = dpath.name
        with open(dpath / cfg.new_schema_few_shot_name) as f:
            schema = f.read()
        if cfg.use_commented_few_shot:
            # Add the comment prefix to every line
            schema = textwrap.indent(schema, "# ", lambda x: True)
        schemas[db_name] = schema
    return schemas

@hydra.main(config_path="../configs", config_name="gpt", version_base="1.2")
def main(cfg: ExperimentConfig):
    logger.info(OmegaConf.to_yaml(cfg))
    
    db_prompts = generate_prompts(cfg.generation_cfg)
    for db_name, prompts in db_prompts.items():
        for prompt in prompts:
            # logger.info(f'input:\n{prompt["text"]}')
            logger.info(f'db: {db_name} diff: {prompt["difficulty_of_few_shot"]}')

if __name__ == '__main__':
    main()