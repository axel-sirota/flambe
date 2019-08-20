from typing import Optional, Dict

import torch
import numpy as np

from flambe.field.text import TextField
from flambe.tokenizer import LabelTokenizer


class LabelField(TextField):
    """Featurizes input labels.

    The class also handles multilabel inputs and one hot encoding.

    """
    def __init__(self,
                 one_hot: bool = False,
                 multilabel_sep: Optional[str] = None) -> None:
        """Initializes the LabelFetaurizer.

        Parameters
        ----------
        one_hot : bool, optional
            Set for one-hot encoded outputs, defaults to False
        multilabel_sep : str, optional
            If given, splits the input label into multiple labels
            using the given separator, defaults to None.

        """
        self.one_hot = one_hot
        self.multilabel_sep = multilabel_sep
        self.label_count_dict: Dict[str, int] = dict()

        tokenizer = LabelTokenizer(self.multilabel_sep)
        super().__init__(tokenizer=tokenizer,
                         lower=False,
                         unk_token=None,
                         pad_token=None)

    def setup(self, *data: np.ndarray) -> None:
        """Build the vocabulary.

        Parameters
        ----------
        data : Iterable[str]
            List of input strings.

        """
        # Iterate over all examples
        examples = (e for dataset in data for e in dataset if dataset is not None)

        # Get current last id
        index = len(self.vocab) - 1

        for example in examples:
            # Tokenize and add to vocabulary
            for token in self.tokenizer(example):
                if token not in self.vocab:
                    self.vocab[token] = index = index + 1
                    self.label_count_dict[token] = 1
                else:
                    self.label_count_dict[token] += 1

    def process(self, example):
        """Featurize a single example.

        Parameters
        ----------
        example: str
            The input label

        Returns
        -------
        torch.Tensor
            A list of integer tokens

        """
        # First process normally
        n = super().process(example)

        if self.one_hot:
            n = [int(i in n) for i in range(len(self.vocab))]
            n = torch.tensor(n).long()  # Back to Tensor

        return n

    @property
    def label_count(self) -> torch.Tensor:
        """Get the label count.

        Returns
        -------
        torch.Tensor
            Tensor containing the count for each label, indexed
            by the id of the label in the vocabulary.
        """
        counts = [self.label_count_dict[label] for label in self.vocab]
        return torch.tensor(counts)

    @property
    def label_freq(self) -> torch.Tensor:
        """Get the frequency of each label.

        Returns
        -------
        torch.Tensor
            Tensor containing the frequency of each label, indexed
            by the id of the label in the vocabulary.

        """
        counts = [self.label_count_dict[label] for label in self.vocab]
        return torch.tensor(counts) / sum(counts)

    @property
    def label_inv_freq(self) -> torch.Tensor:
        """Get the inverse frequency for each label.

        Returns
        -------
        torch.Tensor
            Tensor containing the inverse frequency of each label,
            indexed by the id of the label in the vocabulary.

        """
        return 1. / self.label_freq  # type: ignore
