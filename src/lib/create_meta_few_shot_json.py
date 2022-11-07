import json

from typing import List
from pathlib import Path
from collections import defaultdict

from evaluation import Evaluator
from process_sql import get_schema, get_sql, Schema

PATH_TO_SPIDER = Path(__file__, '../../../data/spider').resolve()
PATH_TO_DATABASE = PATH_TO_SPIDER / 'database'

def get_problems(dname: Path, fnames: List[str]):
    probs = []
    for fname in fnames:
        with open(dname / fname) as f:
            probs += json.load(f)

    db_grouped_probs = defaultdict(list)
    for prob in probs:
        db_grouped_probs[prob["db_id"]].append({
            "question": prob["question"],
            "query": prob["query"]
        })
    return db_grouped_probs

def main():
    all_problems = get_problems(PATH_TO_SPIDER,
        [
            "train_spider.json",
            "train_others.json",
            "dev.json"
        ]
    )

    grouped_results = defaultdict(lambda: defaultdict(list))
    evaluator = Evaluator()

    for db, question_pairs in all_problems.items():
        # The db would not exist for the databases
        # That we have removed
        db_name = PATH_TO_DATABASE / db / f'{db}.sqlite'
        if not db_name.exists():
            continue
        schema = Schema(get_schema(db_name))
        for pair in question_pairs:
            sql = get_sql(schema, pair['query'])
            hardness = evaluator.eval_hardness(sql)
            grouped_results[db][hardness].append(pair)

    with open('grouped_questions.json', 'w') as f:
        json.dump(grouped_results, f, indent=4)

if __name__ == '__main__':
    main()