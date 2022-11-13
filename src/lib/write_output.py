import json

from typing import Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

@dataclass
class OutputManager:
    exp_time: str
    exp_output_dir: Path
    data_output_dir: Path

    def _make_output_dirs(self, db_name: str) -> Tuple[Path, Path]:
        """Create the output directories. The tuple returned contains
        the experiment output dir, then the data output dir.
        """
        exp_out = self.exp_output_dir / db_name
        data_out = self.data_output_dir / db_name
        exp_out.mkdir(exist_ok=True)
        data_out.mkdir(exist_ok=True)
        return exp_out, data_out

    def _write_exp_output(self, data, output_fpath: Path):
        with open(output_fpath, 'w') as f:
            json.dump(data, f, indent=4)

    def _write_data_output(self, data, output_fpath: Path):
        if output_fpath.exists():
            with open(output_fpath) as f:
                existing_data = json.load(f)
        else:
            existing_data = []
        existing_data.append(data)
        with open(output_fpath, 'w') as f:
            json.dump(existing_data, f, indent=4)
        

    def write_output(self, queue) -> int:
        """Write all output in the queue to disk.

        Args:
            queue (collections.deque): A queue of dictionaries
            with the key is a Tuple[db_name, output_type, itr]
            and the value is a dictionary which should be written
            to disk as a json obj.

        Returns:
            int: Number of seconds taken to write output.
        """
        start = datetime.now()
        while queue:
            data = queue.popleft()
            # Each data dictionary in the queue should have 1 item
            (db_name, output_type, itr), val = data.popitem()
            exp_output, data_output = self._make_output_dirs(db_name)
            if output_type == 'pair':
                fpath = data_output / f'{self.exp_time}.json'
                self._write_data_output(val, fpath)
            elif output_type in ('response', 'input_output'):
                fpath = exp_output / f'{output_type}_{itr}.json'
                self._write_exp_output(val, fpath)
            else:
                raise ValueError(
                    f"Output type {output_type} is not valid.",
                    "Output_type must be one of [response, input_output, pair]."
                )
        end = datetime.now()
        return (end - start).seconds