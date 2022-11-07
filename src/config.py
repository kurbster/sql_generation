from typing import Dict, List
from pathlib import Path
from dataclasses import dataclass, field

from hydra.core.config_store import ConfigStore
from hydra.core.hydra_config import HydraConfig

def get_output_dir():
    return Path(HydraConfig.get().output_subdir).resolve()

def get_exp_time():
    exp_time = HydraConfig.get().env.exp_time
    return exp_time.replace('-', '_').replace('/', '_')

@dataclass
class APIConfig:
    "See https://beta.openai.com/docs/api-reference/completions/create for more details"
    model: str

    top_p: float = 1.0
    temperature: float = 0.0
    presence_penalty: float = 0.0
    frequency_penalty: float = 0.0

    n: int = 1
    best_of: int = 1
    logprobs: int = 0
    max_tokens: int = 128

    echo: bool = False
    stream: bool = False

    stop: List[str] = field(default_factory=list)
    logit_bias: Dict[str, float] = field(default_factory=dict)

@dataclass
class GenerationConfig:
    """A prompt will be constructed like this. Anything capitalized
    will be defined in this config. Everything else is calculated in
    the code.
        <HEADER>\n
        <TABLE_PREFIX>\n
        <few_shot_schema>\n
        <few_shot_examples>\n
        <TABLE_PREFIX>\n
        <new_database_schema>\n
        <PROMPT>\n
        <SUFFIX>
    """
    header: str = ""
    prompt: str = ""
    suffix: str = ""
    table_prefix: str = ""
    new_schema_few_shot_name: str = "schema_few_shot.txt"
    # This is how many times to query GPT3 per database
    n_generations_per_database: int = 1
    
    # These params control the few shot settings.
    # If this is defined then we use that file for all few-shotting
    # Else we calculate few shot at runtime.
    few_shot_file: str = ""
    
    # These params are only used if few_shot_file is empty
    query_prefix: str = "SQL: "
    question_prefix: str = "Question: "
    n_few_shot_examples: int = 0

@dataclass
class ExperimentConfig:
    api_cfg: APIConfig
    generation_cfg: GenerationConfig

cs = ConfigStore()
cs.store(name="base_cfg", node=ExperimentConfig)
cs.store(group="api_cfg", name="api_base_cfg", node=APIConfig)
cs.store(group="generation_cfg", name="generation_base_cfg", node=GenerationConfig)