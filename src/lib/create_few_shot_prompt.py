import sys
import logging

from typing import List
from pathlib import Path
PARENT_DIR = Path(__file__, '../..').resolve()
sys.path.append(str(PARENT_DIR))

from src.config import GenerationConfig

PATH_TO_MAIN_DIR = Path(__file__, '../../..').resolve()
PATH_TO_FEW_SHOT = PATH_TO_MAIN_DIR / 'few_shot_prompts'

logger = logging.getLogger("apiLogger")

def generate_prompts(cfg: GenerationConfig) -> List[str]:
    if cfg.few_shot_file == "":
        raise NotImplementedError(
            "Auto Few shotting is not yet implemented ",
            "You must provide a human annotated few shot file."
        )

    path_to_few_shot_file = PATH_TO_MAIN_DIR / cfg.few_shot_file
    assert path_to_few_shot_file.exists(), f"The few shot file: {path_to_few_shot_file} didn't exist"

    few_shot_prompt = get_few_shot_from_file(path_to_few_shot_file, cfg)

    prompts = {}
    # Here we should iterate through all of the databases
    # But for testing lets just use the architecture db
    dbs = ['architecture']
    for db in dbs:
        # This is for when we iterate over Path objects
        # db_name = db.name
        db_name = db
        with open(PATH_TO_FEW_SHOT / db_name / cfg.new_schema_few_shot_name) as f:
            new_schema = f.read()
        few_shot_prompt += [new_schema, cfg.prompt, cfg.suffix]
        prompts[db_name] = '\n'.join(few_shot_prompt)
    
    return prompts

def get_few_shot_from_file(path_to_few_shot_file: Path, cfg: GenerationConfig) -> List[str]:
    with open(path_to_few_shot_file) as f:
        few_shots = f.read()
    few_shot_prompt = [
        cfg.header, cfg.table_prefix, few_shots, cfg.table_prefix
    ]
    return few_shot_prompt