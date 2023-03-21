# sql_generation
This respository contains the code used for my thesis `Using Language Models to Generate Text-to-SQL Training Data An Approach to Improve Performance of a Text-to-SQL Parser`. This code will generate SQL question/query pairs using GPT-3's API. Running the script `src/gen_sql.py` will call the API according to the config values specified in `src/configs/gpt.yaml`. The default value for the configuation can be found in `src/config.py`.

The code used to train and evaluate the model was from the [PICARD](https://github.com/ServiceNow/picard) repo.

The generated text-to-SQL data can be downloaded [here](https://drive.google.com/file/d/1L_n793IjBxGTEoQ1Do_gYSzJGjZx-QyW/view?usp=share_link).
