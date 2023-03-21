#!/usr/bin/env python3
import sys
import json
import signal
import logging

from typing import Dict, List
from collections import defaultdict
from pathlib import Path
PARENT_DIR = Path(__file__, '../..').resolve()
sys.path.append(str(PARENT_DIR))

import hydra
import records
import pandas as pd

from omegaconf import OmegaConf

from src.config import EvaluationConfig

logger = logging.getLogger("myLogger")

class TimeoutError(Exception):
    pass

def timeout(func):
    def _handle_timeout(signum, frame):
        raise TimeoutError("SQL took more than 10 seconds. Marking Invalid.")
    def wrapper(*a, **kw):
        signal.signal(signal.SIGALRM, _handle_timeout)
        signal.alarm(10)
        try:
            result = func(*a, **kw)
        finally:
            signal.alarm(0)
        return result
    return wrapper

def tokenize(string):
    """This is a slight modification from the original spider code
    https://github.com/taoyds/spider/blob/master/process_sql.py
    """ 
    string = str(string)
    string = string.replace(")from", ") from")
    string = string.replace("\'", "\"")  # ensures all string values wrapped by "" problem??
    quote_idxs = [idx for idx, char in enumerate(string) if char == '"']
    assert len(quote_idxs) % 2 == 0, f"Unexpected quote: {string}"

    # keep string value as token
    vals = {}
    for i in range(len(quote_idxs)-1, -1, -2):
        qidx1 = quote_idxs[i-1]
        qidx2 = quote_idxs[i]
        val = string[qidx1: qidx2+1]
        key = "__val_{}_{}__".format(qidx1, qidx2)
        string = string[:qidx1] + key + string[qidx2+1:]
        vals[key] = val

    toks = string.split()
    # replace with string value token
    for i in range(len(toks)):
        if toks[i] in vals:
            toks[i] = vals[toks[i]]

    # find if there exists !=, >=, <=
    eq_idxs = [idx for idx, tok in enumerate(toks) if tok == "="]
    eq_idxs.reverse()
    prefix = ('!', '>', '<')
    for eq_idx in eq_idxs:
        pre_tok = toks[eq_idx-1]
        if pre_tok in prefix:
            toks = toks[:eq_idx-1] + [pre_tok + "="] + toks[eq_idx+1: ]

    return toks

def convert_select_aliases(result: List[Dict[str, any]], alias_table: Dict[str, str]):
    for row in result:
        keys = tuple(row.keys())
        for key in keys:
            if key in alias_table:
                row[alias_table[key]] = row.pop(key)
    
def compute_exec_match(
    gold: List[Dict[str, any]],
    pred: List[Dict[str, any]],
    gold_alias_table: Dict[str, str],
    pred_alias_table: Dict[str, str]
) -> int:

    convert_select_aliases(gold, gold_alias_table)
    convert_select_aliases(pred, pred_alias_table)
    gold = [{k.lower(): v for k, v in row.items()} for row in gold]
    pred = [{k.lower(): v for k, v in row.items()} for row in pred]
    return gold == pred

def get_alias_table(query: str) -> Dict[str, str]:
    alias_table = {}
    query_toks = tokenize(query)
    if query_toks.count('from') > 1:
        logger.debug(
            f"""There was more than 1 from statement.
            query: {query}
            query_toks: {query_toks}"""
        )

    if query_toks.count('from') == 0:
        logger.critical(query_toks)
        assert False
        return {}

    select_stmt = query_toks[:query_toks.index('from')]
    for i, tok in enumerate(select_stmt):
        if tok == 'as':
            no_comma_alias = select_stmt[i+1].replace(',', '')
            alias_table[no_comma_alias] = select_stmt[i-1]
    return alias_table

@timeout
def get_pred_result(conn, query):
    result = conn.query(query)
    return result

# TODO: Implement hardness scores from spider
def evaluate(cfg: EvaluationConfig, input_path: Path, db_dir: Path):
    results = defaultdict(lambda: defaultdict(int))
    with open(input_path) as f:
        data = json.load(f)
    
    correct_examples = []
    for example in data:
        # Turn everything into lower because sqlite doesn't care
        # This makes parsing everything later easier
        gold = example[cfg.gold_key].lower()
        pred = example[cfg.pred_key].lower()
        db_name = example[cfg.db_key]

        if db_name in ['academic', 'imdb', 'scholar', 'yelp', 'geo']:
            continue

        db = records.Database(f'sqlite:///{db_dir}/{db_name}/{db_name}.sqlite')
        conn = db.get_connection()

        gold_return = conn.query(gold).as_dict()
        error_msg = None
        try:
            logger.debug(f'I am the DB: {db_name} I am the query: {pred}')
            # pred_return = conn.query(pred).as_dict()
            pred_return = get_pred_result(conn, pred).as_dict()
        except TimeoutError as e:
            logger.warning(e)
            error = 1
            is_correct = 0
            error_msg = "TimeoutError"
        except Exception as e: # There was an sql error with pred
            error = 1
            is_correct = 0
            logger.debug(f"""
            There was an error with the query: {pred}
            This was the exception: {str(e)}
            """)
            error_msg = str(e)
        else:
            error = 0
            gold_alias_table = get_alias_table(gold)
            pred_alias_table = get_alias_table(pred)
            is_correct = compute_exec_match(
                gold_return, pred_return,
                gold_alias_table, pred_alias_table
            )
        results[db_name]['correct'] += is_correct
        results[db_name]['error'] += error
        results[db_name]['total'] += 1
        new_example = example.copy()
        new_example["correct"] = bool(is_correct)
        new_example["error_msg"] = error_msg
        correct_examples.append(new_example)
    
    with open("/media/HD/Documents/sql_generation/data/PICARD/correct_predictions.json", "w") as f:
        json.dump(correct_examples, f, indent=4)

    return results

@hydra.main(config_path="configs", config_name="evaluate", version_base="1.2")
def main(cfg: EvaluationConfig):
    logger.info(OmegaConf.to_yaml(cfg))

    db_dir = PARENT_DIR / cfg.database_path
    assert db_dir.exists(), f'The path: {db_dir} did not exist.'
    for eval_file in cfg.eval_files:
        logger.info(f'Running evaluation for {eval_file}')
        input_data_path = PARENT_DIR / eval_file
        assert input_data_path.exists(), f'The path: {input_data_path} did not exist.'
        results = evaluate(cfg, input_data_path, db_dir)
        logger.info(f'Results for: {eval_file}')
        df = pd.DataFrame.from_dict(results, orient='index')
        df.loc['all'] = df.sum()
        df['accuracy'] = df['correct'] / df['total']
        df['error_ratio'] = df['error'] / df['total']
        logger.info(f'\n{df}')
        output_path = input_data_path.parent / f'{input_data_path.stem}_{cfg.eval_output_fname}'
        df.to_csv(output_path)

if __name__ == "__main__":
    main()
