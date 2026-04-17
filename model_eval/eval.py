import sys
from pathlib import Path
import gc
import numpy as np
from collections import defaultdict
from PIL import Image
from dataset import load_dataset
from metrics import dice, iou
import time

# add the parent directory to sys.path so we can find the core folder
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

from core import processor

# Configuration
MODELS = [
    "u2net",
    "u2netp",
    "silueta",
    "isnet-general-use",
    "sam",
    "birefnet-general",
    "birefnet-general-lite",
    "bria-rmbg",
]

DATASET_ROOT = Path("dataset")
CACHE_ROOT = Path(".cache")
RESULTS_ROOT = Path("results")
MAX_SIZE = (1024, 1024)
DICE_THRESHOLD = 0.95


def print_detailed_stats(model_name, results):
    """
    Calculates and prints performance statistics (Mean, Median, Std Dev, etc.)
    for a specific model. Also identifies and lists cases that fell below
    the quality threshold.
    """
    dices = np.array([r["dice"] for r in results])
    ious = np.array([r["iou"] for r in results])
    failures = [r for r in results if r["dice"] < DICE_THRESHOLD]
    times = np.array([r["time_s"] for r in results if r["time_s"] is not None])

    print(f"Analysis: {model_name}")
    stats_table = [
        ["Metric", "Mean", "Median", "Std Dev", "Min", "Max"],
        [
            "Dice",
            f"{np.mean(dices):.4f}",
            f"{np.median(dices):.4f}",
            f"{np.std(dices):.4f}",
            f"{np.min(dices):.4f}",
            f"{np.max(dices):.4f}",
        ],
        [
            "IoU",
            f"{np.mean(ious):.4f}",
            f"{np.median(ious):.4f}",
            f"{np.std(ious):.4f}",
            f"{np.min(ious):.4f}",
            f"{np.max(ious):.4f}",
        ],
    ]

    if len(times):
        stats_table.append(
            [
                "Time (s)",
                f"{np.mean(times):.4f}",
                f"{np.median(times):.4f}",
                f"{np.std(times):.4f}",
                f"{np.min(times):.4f}",
                f"{np.max(times):.4f}",
            ]
        )

    for row in stats_table:
        print(
            f"{row[0]:<10} {row[1]:>10} {row[2]:>10} {row[3]:>10} {row[4]:>10} {row[5]:>10}"
        )

    if failures:
        print(f"\nTHRESHOLD FAILURES (Dice < {DICE_THRESHOLD}):")
        for f in failures:
            print(f"  - {f['case']}: Dice={f['dice']:.4f}, IoU={f['iou']:.4f}")
    else:
        print(f"\nAll files passed threshold ({DICE_THRESHOLD})")
    print(f"\n{'=' * 65}\n")


def evaluate(dataset_root: Path):
    """
    Main orchestration function. It iterates through every model, processes
    every dataset case, calculates metrics, and saves visual results.
    """
    cases = load_dataset(dataset_root)
    all_results = defaultdict(list)

    for model in MODELS:
        print(f"Processing Model: {model}")
        model_results_dir = RESULTS_ROOT / model
        model_results_dir.mkdir(parents=True, exist_ok=True)

        # ensure cache directory exists for performance
        model_cache = CACHE_ROOT / model
        model_cache.mkdir(parents=True, exist_ok=True)

        for case in cases:
            gt_mask = case.load_expected_mask()
            cache_path = model_cache / f"{case.case_id}.npy"

            # check for cached mask to save time
            if cache_path.exists():
                pred_mask = np.load(cache_path)
                # if cached mask is wrong size, re-run
                if pred_mask.shape != gt_mask.shape:
                    t_start = time.perf_counter()
                    _, pred_mask = processor.process_image(
                        case.input_path, model, MAX_SIZE
                    )
                    elapsed = time.perf_counter() - t_start
                else:
                    elapsed = None
            else:
                t_start = time.perf_counter()
                # Run model and save mask + visual image
                result_img, pred_mask = processor.process_image(
                    case.input_path, model, MAX_SIZE
                )
                elapsed = time.perf_counter() - t_start
                np.save(cache_path, pred_mask)
                result_img.save(model_results_dir / f"{case.case_id}.png")

            # Final size check for metrics
            if pred_mask.shape != gt_mask.shape:
                temp_img = Image.fromarray(pred_mask.astype(np.uint8) * 255)
                temp_img = temp_img.resize(
                    (gt_mask.shape[1], gt_mask.shape[0]), Image.Resampling.NEAREST
                )
                pred_mask = np.array(temp_img) > 0

            all_results[model].append(
                {
                    "case": case.case_id,
                    "dice": dice(gt_mask, pred_mask),
                    "iou": iou(gt_mask, pred_mask),
                    "time_s": elapsed,
                }
            )

        print_detailed_stats(model, all_results[model])
        processor.clear_sessions()
        gc.collect()


if __name__ == "__main__":
    evaluate(DATASET_ROOT)
