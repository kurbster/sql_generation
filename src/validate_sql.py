#!/usr/bin/env python3
import sys
import json
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

@hydra.main(config_path="configs", config_name="validate", version_base="1.2")
def main(cfg):
    logger.info(f'\n{OmegaConf.to_yaml(cfg)}')
    gen_data_path = PARENT_DIR / cfg.path_to_data
    for gen_data_dir in gen_data_path.iterdir():
        logger.info(f'Testing generations for: {gen_data_dir}')
        db_name = gen_data_dir.name
        with open(gen_data_dir / cfg.input_fname) as f:
            gen_data = json.load(f)

        path_to_db = PARENT_DIR / cfg.path_to_database
        db = records.Database(f'sqlite:///{path_to_db}/{db_name}/{db_name}.sqlite')
        conn = db.get_connection()

        valid_sql = []
        invalid_sql = []
        for pair in gen_data:
            try:
                conn.query(pair['query'])
            except sqlalchemy.exc.OperationalError as e:
                logger.info('Found invalid sql')
                pair['error_msg'] = str(e)
                invalid_sql.append(pair)
            else:
                valid_sql.append(pair)
        
        with open(gen_data_dir / cfg.valid_output_fname, 'w') as f:
            json.dump(valid_sql, f, indent=4)

        with open(gen_data_dir / cfg.invalid_output_fname, 'w') as f:
            json.dump(invalid_sql, f, indent=4)

if __name__ == "__main__":
    main()