# Running Blast Radius on Kaggle (the ~30-minute hands-on step)

Everything else is built. This is the only part that needs a Kaggle login. Follow top to
bottom. Expect a few models to error or hit free-tier quota (normal); we report that honestly.

## 0. One-time setup (on a laptop/desktop with the Kaggle CLI)
```bash
pip install kaggle                      # if not already installed
# Install the Kaggle Benchmarks helper skill (optional but handy):
#   ask your coding agent to install https://github.com/Kaggle/kaggle-skills
git clone https://github.com/simplynadaf/blast-radius-benchmark.git
cd blast-radius-benchmark

kaggle b init -y                        # fetches Model Proxy creds, writes .env + example
kaggle b t models                       # <-- COPY THIS LIST and send it back; we lock the lineup
```

## 1. Validate locally before pushing
```bash
python task.py                          # should run and produce a *.run.json
ls -1 *.run.json                        # confirm a run file exists
```
If `python task.py` fails with an auth error, run `kaggle b auth -y` (the key is short-lived).

## 2. Push the task
```bash
kaggle b t push blast_radius -f task.py --wait
```

## 3. Run against the model lineup
Run each model (repeat `-m`, do NOT space-separate). Use the slugs from `kaggle b t models`.
```bash
kaggle b t run blast_radius -m <model-1> --wait
kaggle b t run blast_radius -m <model-2> --wait
# ... one per model in the locked lineup ...
```

### Controlled reasoning experiment (the headline contrast)
Run one or two capable models twice, reasoning off vs high. The task takes a `reasoning` arg;
if the CLI run does not expose task kwargs directly, duplicate the task with the default flipped,
or set it in the final cell. (We will finalize this once we see `kaggle b t models` output.)

## 4. Check + download results
```bash
kaggle b t status blast_radius          # per-model run status
kaggle b t download blast_radius -o ./results   # pull the run outputs
```
Send back the `./results` folder (or the status table) so we can generate the charts and fill
the article numbers.

## 5. Publish the public benchmark + leaderboard (REQUIRED for a valid entry)
- In the Kaggle web UI, assemble the benchmark from the task and make it PUBLIC.
- In the task notebook's final cell, select the leaderboard task:
  ```python
  %choose blast_radius
  ```
- Copy the PUBLIC benchmark/leaderboard URL. **That link is mandatory in the dev.to post.**

## 6. Send back
1. The output of `kaggle b t models` (to lock the lineup).
2. The `./results` folder or `kaggle b t status` table (the real numbers).
3. The public Kaggle benchmark/leaderboard URL.

With those three, I fill the article numbers + charts, drop in the link, finalize the title,
and it is ready to publish before Oct 11, 11:59 PM PDT.
