# Author: Chris Moody <chrisemoody@gmail.com>
# License: MIT

# This simple example loads the newsgroups data from sklearn
# and train an LDA-like model on it

from lda2vec import preprocess, LDA2Vec, Corpus
from sklearn.datasets import fetch_20newsgroups
import numpy as np
import logging

logging.basicConfig()

# Fetch data
texts = fetch_20newsgroups(subset='train').data
# Convert to unicode (spaCy only works with unicode)
texts = [unicode(d) for d in texts]

# Preprocess data
max_length = 10000   # Limit of 10k words per document
tokens, vocab = preprocess.tokenize(texts, max_length, tag=False,
                                    parse=False, entity=False)
corpus = Corpus()
# Make a ranked list of rare vs frequent words
corpus.update_word_count(tokens)
corpus.finalize()
# The tokenization uses spaCy indices, and so may have gaps
# between indices for words that aren't present in our dataset.
# This builds a new compact index
compact = corpus.to_compact(tokens)
# Remove extremely frequent or rare words
pruned = corpus.filter_count(compact, min_count=5)
# Words tend to have power law frequency, so selectively
# downsample the most prevalent words
clean = corpus.subsample_frequent(pruned)
# Get the count for each key
counts = corpus.keys_counts

# Model Parameters
# Number of documents
n_docs = len(texts)
# Number of unique words in the vocabulary
n_words = clean.max() + 1
# Number of dimensions in a single word vector
n_hidden = 128
# Number of topics to fit
n_topics = 10
# Number of times to pass through the data
epochs = 5


def chunks(n, *args):
    """Yield successive n-sized chunks from l."""
    # From stackoverflow question 312443
    for i in xrange(0, len(args[0]), n):
        yield [a[i:i+n] for a in args]

# Fit the model
model = LDA2Vec(n_words, max_length, n_hidden, counts)
model.add_component(n_docs, n_topics, name='document id')
doc_ids = np.arange(clean.shape[0])
fraction = 0.01
n_chunk = int(clean.shape[0] * fraction)
for _ in range(epochs):
    for chunk, doc_id in chunks(n_chunk, clean, doc_ids):
        model.fit_partial(chunk, fraction, components=[doc_id])
