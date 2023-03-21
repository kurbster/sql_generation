#!/usr/bin/env python3
import sys
import json
import signal
import logging

from pathlib import Path
PARENT_DIR = Path(__file__, '../..').resolve()
sys.path.append(str(PARENT_DIR))

import hydra
import records
# This is a hidden import from records we use it to properly
# catch sql exceptions from invalid queries
import sqlalchemy

from omegaconf import OmegaConf

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

@timeout
def make_query_call(conn, query):
    conn.query(query)

@hydra.main(config_path="configs", config_name="validate", version_base="1.2")
def main(cfg):
    logger.info(f'\n{OmegaConf.to_yaml(cfg)}')
    gen_data_path = PARENT_DIR / cfg.path_to_data
    for gen_data_dir in gen_data_path.iterdir():
        if gen_data_dir.is_file():
            continue
        logger.info(f'Testing generations for: {gen_data_dir}')
        db_name = gen_data_dir.name
        with open(gen_data_dir / cfg.input_fname) as f:
            gen_data = json.load(f)

        path_to_db = PARENT_DIR / cfg.path_to_database
        db = records.Database(f'sqlite:///{path_to_db}/{db_name}/{db_name}.sqlite')
        conn = db.get_connection()

        valid_sql = []
        invalid_sql = []
        for i, pair in enumerate(gen_data):
            logger.debug(f'I am the ith iteration: {i}')
            try:
                key = 'query' if 'query' in pair else 'gen_sql'
                # conn.query(pair[key])
                make_query_call(conn, pair[key])
            except (sqlalchemy.exc.OperationalError,
                    sqlalchemy.exc.ResourceClosedError) as e:
                logger.info('Found invalid sql')
                pair['error_msg'] = str(e)
                invalid_sql.append(pair)
            except TimeoutError as e:
                logger.warning(e)
                pair['error_msg'] = "(TimeoutError): Took longer than 10 seconds."
                invalid_sql.append(pair)
            except Exception as e:
                logger.error(f'There was an unexpected exception: {e}')
                logger.error(f'I am the db: {pair["db_id"]}')
                logger.error(f'I am the query {pair[key]}')
                logger.error(f'I am the question {pair["question"]}')
                # raise e
                break
            else:
                valid_sql.append(pair)
        
        with open(gen_data_dir / cfg.valid_output_fname, 'w') as f:
            json.dump(valid_sql, f, indent=4)

        with open(gen_data_dir / cfg.invalid_output_fname, 'w') as f:
            json.dump(invalid_sql, f, indent=4)

if __name__ == "__main__":
    main()