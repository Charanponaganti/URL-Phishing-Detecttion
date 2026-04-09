import argparse
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from feature_extraction import FeatureExtractor
from models.rnn.rnn_base import RnnBase
from models.rnn.rnn_complex import RnnComplex


def main(args):
    fe = FeatureExtractor(char_index_path="dataset/char_index")
    fe.load_from_file("dataset/train/train.txt")

    x = fe.get_sequences(sequence_length=args.sequence_length)
    y = fe.get_labels()

    # choose model
    if args.model == "rnn_base":
        model_builder = RnnBase(args.embed_dim, args.sequence_length)
    elif args.model == "rnn_complex":
        model_builder = RnnComplex(args.embed_dim, args.sequence_length)
    else:
        raise ValueError(f"Unknown model: {args.model}. Choose 'rnn_base' or 'rnn_complex'.")

    model = model_builder.build(fe.tokener.word_index)
    model.compile(
        loss="binary_crossentropy",
        optimizer="adam",
        metrics=["accuracy"]
    )

    model.fit(
        x, y,
        epochs=args.epochs,
        batch_size=args.batch_size,
        validation_split=0.2
    )

    model.save("models/rnn/{}".format(args.model))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", type=str, default="rnn_base")
    parser.add_argument("--embed_dim", type=int, default=128)
    parser.add_argument("--sequence_length", type=int, default=512)
    parser.add_argument("--epochs", type=int, default=10)
    parser.add_argument("--batch_size", type=int, default=32)
    args = parser.parse_args()

    main(args)