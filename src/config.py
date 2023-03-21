from typing import Dict, List, Any
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

    # Stop is a list of stop words. But can be None
    stop: Any = field(default=None)
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
    suffix: str = ""
    table_prefix: str = ""
    # This is the path from the main git dir.
    data_output_dir: str = "data/generated_data"
    new_schema_few_shot_name: str = "schema_few_shot.txt"
    
    # These params control the few shot settings.
    # If this is defined then we use that file for all few-shotting
    # Else we calculate few shot at runtime.
    few_shot_file: str = ""

    # Path from the few_shot_prompts dir. This file contains every
    # Question for every dataset ranked by difficulty. We will
    # Use this for additional few shotting
    meta_few_shot_file: str = "grouped_questions.json"

    # This is how many times to query GPT3 per database
    n_generations_per_database: int = 1
    random_seed: int = 42

    # These are the list of different prompts to use. They
    # Will be the last line of text given to the model.
    prompts: List[str] = field(default_factory=list)
    
    # These params are used to add automatic few shot examples.
    # Which is used for the meta_few_shot_file and when few_shot_file == ""
    query_prefix: str = "SQL: "
    question_prefix: str = "Question: "
    n_few_shot_examples: int = 0

@dataclass
class CodexGenerationConfig(GenerationConfig):
    # These are the keys in the json to read
    db_key: str = "db_id"
    query_key: str = "query"
    question_key: str = "question"
    
    # Should be path from main git dir
    input_data_files: Dict[str, str] = field(default_factory=dict)

    # If true it will add a # to every line in the schema and few shot examples.
    # This more follows in line with the openAI SQL generation template
    # https://beta.openai.com/playground/p/default-sql-translate?model=code-davinci-002
    use_commented_few_shot: bool = False

@dataclass
class EvaluationConfig:
    # All paths are from the main git dir
    eval_files: List[str] = field(default_factory=list)

    db_key: str = "db_id"
    pred_key: str = "gen_sql"
    gold_key: str = "gold_sql"
    database_path: str = "data/spider/database"
    eval_output_fname: str = "results.csv"

@dataclass
class ExperimentConfig:
    api_cfg: APIConfig
    generation_cfg: GenerationConfig

cs = ConfigStore()
cs.store(name="base_cfg", node=ExperimentConfig)
cs.store(name="eval_cfg", node=EvaluationConfig)
cs.store(group="api_cfg", name="api_base_cfg", node=APIConfig)
cs.store(group="generation_cfg", name="codex_base_cfg", node=CodexGenerationConfig)
cs.store(group="generation_cfg", name="generation_base_cfg", node=GenerationConfig)