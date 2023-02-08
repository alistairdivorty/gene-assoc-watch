import argparse, os, logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional
import torch
from torch.utils.data import Dataset, DataLoader
import pytorch_lightning as pl
from datasets import load_dataset
from transformers import (
    AdamW,
    T5ForConditionalGeneration,
    T5Tokenizer,
    get_linear_schedule_with_warmup,
)

logger = logging.getLogger(__name__)


class T5FineTuner(pl.LightningModule):
    def __init__(self, hparams):
        super(T5FineTuner, self).__init__()
        self.hparams.update(vars(hparams))

        self.model = T5ForConditionalGeneration.from_pretrained(
            hparams.model_name_or_path
        )
        self.tokenizer = T5Tokenizer.from_pretrained(hparams.tokenizer_name_or_path)

    def is_logger(self):
        return self.trainer.global_rank <= 0

    def forward(
        self,
        input_ids,
        attention_mask=None,
        decoder_input_ids=None,
        decoder_attention_mask=None,
        labels=None,
    ):
        return self.model(
            input_ids,
            attention_mask=attention_mask,
            decoder_input_ids=decoder_input_ids,
            decoder_attention_mask=decoder_attention_mask,
            labels=labels,
        )

    def _step(self, batch):
        labels = batch["target_ids"]
        labels[labels[:, :] == self.tokenizer.pad_token_id] = -100

        outputs = self(
            input_ids=batch["source_ids"],
            attention_mask=batch["source_mask"],
            labels=labels,
            decoder_attention_mask=batch["target_mask"],
        )

        loss = outputs[0]
        return loss

    def training_step(self, batch, batch_idx):
        loss = self._step(batch)

        tensorboard_logs = {"train_loss": loss}
        return {"loss": loss, "log": tensorboard_logs}

    def training_epoch_end(self, outputs):
        avg_train_loss = torch.stack([x["loss"] for x in outputs]).mean()
        tensorboard_logs = {"avg_train_loss": avg_train_loss}
        return {
            "avg_train_loss": avg_train_loss,
            "log": tensorboard_logs,
            "progress_bar": tensorboard_logs,
        }

    def validation_step(self, batch, batch_idx):
        loss = self._step(batch)
        return {"val_loss": loss}

    def validation_epoch_end(self, outputs):
        avg_loss = torch.stack([x["val_loss"] for x in outputs]).mean()
        tensorboard_logs = {"val_loss": avg_loss}
        return {
            "avg_val_loss": avg_loss,
            "log": tensorboard_logs,
            "progress_bar": tensorboard_logs,
        }

    def configure_optimizers(self):
        model = self.model
        no_decay = ["bias", "LayerNorm.weight"]
        optimizer_grouped_parameters = [
            {
                "params": [
                    p
                    for n, p in model.named_parameters()
                    if not any(nd in n for nd in no_decay)
                ],
                "weight_decay": self.hparams.weight_decay,
            },
            {
                "params": [
                    p
                    for n, p in model.named_parameters()
                    if any(nd in n for nd in no_decay)
                ],
                "weight_decay": 0.0,
            },
        ]

        optimizer = AdamW(
            optimizer_grouped_parameters,
            lr=self.hparams.learning_rate,
            eps=self.hparams.adam_epsilon,
        )
        self.opt = optimizer
        return [optimizer]

    def get_tqdm_dict(self):
        tqdm_dict = {
            "loss": "{:.3f}".format(self.trainer.avg_loss),
            "lr": self.lr_scheduler.get_last_lr()[-1],
        }
        return tqdm_dict

    def train_dataloader(self):
        train_dataset = get_dataset(
            tokenizer=self.tokenizer, type_path="train", args=self.hparams
        )
        dataloader = DataLoader(
            train_dataset,
            batch_size=self.hparams.train_batch_size,
            drop_last=True,
            shuffle=True,
            num_workers=4,
        )
        t_total = (
            (
                len(dataloader.dataset)
                // (self.hparams.train_batch_size * max(1, self.hparams.n_gpu))
            )
            // self.hparams.gradient_accumulation_steps
            * float(self.hparams.num_train_epochs)
        )
        scheduler = get_linear_schedule_with_warmup(
            self.opt,
            num_warmup_steps=self.hparams.warmup_steps,
            num_training_steps=t_total,
        )
        self.lr_scheduler = scheduler
        return dataloader

    def val_dataloader(self):
        val_dataset = get_dataset(
            tokenizer=self.tokenizer, type_path="val", args=self.hparams
        )
        return DataLoader(
            val_dataset, batch_size=self.hparams.eval_batch_size, num_workers=4
        )


class LoggingCallback(pl.Callback):
    def on_validation_end(self, trainer, pl_module):
        logger.info("***** Validation results *****")

        if pl_module.is_logger():
            metrics = trainer.callback_metrics
            for key in sorted(metrics):
                if key not in ["log", "progress_bar"]:
                    logger.info("{} = {}\n".format(key, str(metrics[key])))

    def on_test_end(self, trainer, pl_module):
        logger.info("***** Test results *****")

        if pl_module.is_logger():
            metrics = trainer.callback_metrics

            output_test_results_file = os.path.join(
                pl_module.hparams.output_dir, "test_results.txt"
            )
            with open(output_test_results_file, "w") as writer:
                for key in sorted(metrics):
                    if key not in ["log", "progress_bar"]:
                        logger.info("{} = {}\n".format(key, str(metrics[key])))
                        writer.write("{} = {}\n".format(key, str(metrics[key])))


@dataclass(frozen=True)
class InputExample:
    example_id: str
    premise: str
    hypothesis: str
    label: Optional[str]


class Split(Enum):
    train = "train"
    dev = "dev"
    test = "test"


class DataProcessor:
    def get_train_examples(self):
        raise NotImplementedError()

    def get_dev_examples(self):
        raise NotImplementedError()

    def get_test_examples(self):
        raise NotImplementedError()

    def get_labels(self):
        raise NotImplementedError()


class MNLIProcessor(DataProcessor):
    def __init__(self):
        self.dataset = load_dataset("multi_nli")

    def get_train_examples(self):
        return self._create_examples(self.dataset["train"], "train")

    def get_dev_examples(self):
        return self._create_examples(self.dataset["validation_matched"], "dev")

    def get_test_examples(self):
        raise ValueError("Test examples not yet available.")

    def get_labels(self):
        return ["0", "1", "2"]

    def _create_examples(self, lines: list[list[str]], type: str):
        examples = [
            InputExample(
                example_id=line["pairID"],
                premise=line["premise"],
                hypothesis=line["hypothesis"],
                label=str(line["label"]),
            )
            for line in lines
        ]
        return examples


class MNLIDataset(Dataset):
    def __init__(self, tokenizer, type_path, max_len=512):
        self.type_path = type_path
        self.max_len = max_len
        self.tokenizer = tokenizer
        self.inputs = []
        self.targets = []

        self.proc = MNLIProcessor()

        self._build()

    def __getitem__(self, index):
        source_ids = self.inputs[index]["input_ids"].squeeze()
        target_ids = self.targets[index]["input_ids"].squeeze()

        src_mask = self.inputs[index]["attention_mask"].squeeze()
        target_mask = self.targets[index]["attention_mask"].squeeze()

        return {
            "source_ids": source_ids,
            "source_mask": src_mask,
            "target_ids": target_ids,
            "target_mask": target_mask,
        }

    def __len__(self):
        return len(self.inputs)

    def _build(self):
        if self.type_path == "train":
            examples = self.proc.get_train_examples()[:6]
        else:
            examples = self.proc.get_dev_examples()

        for example in examples:
            self._create_features(example)

    def _create_features(self, example):
        input_ = "mnli: premise: %s  hypothesis: %s" % (
            example.premise,
            example.hypothesis,
        )

        target = example.label

        tokenized_inputs = self.tokenizer.batch_encode_plus(
            [input_],
            max_length=self.max_len,
            pad_to_max_length=True,
            return_tensors="pt",
        )

        tokenized_targets = self.tokenizer.batch_encode_plus(
            [target], max_length=2, pad_to_max_length=True, return_tensors="pt"
        )

        self.inputs.append(tokenized_inputs)
        self.targets.append(tokenized_targets)


def get_dataset(tokenizer, type_path, args):
    return MNLIDataset(
        tokenizer=tokenizer,
        type_path=type_path,
        max_len=args.max_seq_length,
    )


def main():
    args_dict = dict(
        output_dir="output",
        model_name_or_path="razent/SciFive-large-Pubmed_PMC",
        tokenizer_name_or_path="razent/SciFive-large-Pubmed_PMC",
        max_seq_length=512,
        learning_rate=3e-4,
        weight_decay=0.0,
        adam_epsilon=1e-8,
        warmup_steps=0,
        train_batch_size=8,
        eval_batch_size=8,
        num_train_epochs=3,
        gradient_accumulation_steps=16,
        n_gpu=0,
        early_stop_callback=False,
        fp_16=False,
        opt_level="O1",
        max_grad_norm=1.0,
        seed=42,
    )

    args = argparse.Namespace(**args_dict)

    checkpoint_callback = pl.callbacks.ModelCheckpoint(
        dirpath=args.output_dir,
        monitor="val_loss",
        mode="min",
        save_top_k=5,
    )

    train_params = dict(
        accumulate_grad_batches=args.gradient_accumulation_steps,
        gpus=args.n_gpu,
        max_epochs=args.num_train_epochs,
        precision=16 if args.fp_16 else 32,
        gradient_clip_val=args.max_grad_norm,
        checkpoint_callback=checkpoint_callback,
        callbacks=[LoggingCallback()],
    )

    model = T5FineTuner(args)
    trainer = pl.Trainer(**train_params)
    trainer.fit(model)

    model.model.save_pretrained("t5_pubmed_mnli")


if __name__ == "__main__":
    main()
