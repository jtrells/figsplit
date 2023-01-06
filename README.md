# FigSplit

Wrapper to invoke the FigSplit service provided by the University of Delaware.

## Run

```bash
poetry run split --num_workers=NUM_WORKERS INPUT_PATH
```

- NUM_WORKERS (int): Number of processors to assign for multiprocessing
- INPUT_PATH (str): Folder path containing every folder to process; each subfolder contains the images to extract.
