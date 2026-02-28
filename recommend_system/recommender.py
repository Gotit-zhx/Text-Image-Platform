import argparse
from recsys import ALSRecommenderService, Config


def parse_args():
    parser = argparse.ArgumentParser(description="ALS recommender trainer / demo")
    parser.add_argument("--csv", default="QK-article-cleaned.csv", help="Path to interactions CSV")
    parser.add_argument("--cache", default="cache", help="Cache directory for parquet/npz/model")
    parser.add_argument("--model", default="trained_model.npz", help="Model filename inside cache directory")
    parser.add_argument("--mode", choices=["train", "infer"], default="train", help="Train or run inference")
    parser.add_argument("--trials", type=int, default=None, help="Optuna trials for hyperparameter search (default: use Config)")
    parser.add_argument("--val_ratio", type=float, default=0.1, help="Validation ratio for split")
    parser.add_argument("--user", type=str, help="User id for inference demo")
    parser.add_argument("--k", type=int, default=10, help="Top-K for recommendations")
    return parser.parse_args()


def main():
    args = parse_args()
    cfg = Config(csv_path=args.csv, cache_dir=args.cache, model_filename=args.model)
    service = ALSRecommenderService(cfg)

    if args.mode == "train":
        service.train(n_trials=args.trials, validation_ratio=args.val_ratio)
    else:
        if args.user is None:
            raise SystemExit("--user is required for infer mode")
        service.load()
        recs = service.recommend(args.user, k=args.k)
        for item, score in recs:
            print(f"{item}\t{score:.4f}")


if __name__ == "__main__":
    main()
