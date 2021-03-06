# Copyright 2017 The PaperGrid Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

# In[3]:


import pandas as pd 
import numpy as np 
import re
import sys

from nltk import word_tokenize
from keras.models import Sequential, Model
from keras.layers.embeddings import Embedding
from keras.models import model_from_json
from keras.layers import Input, Activation, Dense, Dropout
from keras.layers import LSTM, Bidirectional


# In[4]:


quotables = pd.read_csv('author-quote.txt', delimiter='\t', header=None)
quotables = quotables.rename(columns={0:'author', 1:'quote'})


# In[5]:


print(quotables.sample(20))


# In[6]:


quotables['len_quotes'] = quotables.quote.map(lambda s: len(s))


# In[7]:


quotes = list(quotables.quote + '\n')


# In[8]:


removed_char = ['#', '$', '%', '(', ')', '=', ';' ,':',  '*', '+', '£' , '—','’']  
quotes_cleaned = []

for quote in quotes: 
    # remove unused character
    for s_char in removed_char:
        quote = quote.replace(s_char, ' ')
    
    # remove white space
    pattern = re.compile(r'\s{2,}')
    quote = re.sub(pattern, ' ', quote)

    quotes_cleaned.append(quote)

text = ' '.join(quotes_cleaned)
chars = sorted(list(set(text)))
char_indices = dict((c, i) for i, c in enumerate(chars))
indices_char = dict((i, c) for i, c in enumerate(chars))


# In[9]:


maxlen = 15
step = 6
sentences = []
next_chars = []

for quote in quotes_cleaned:
    for i in range(0, len(quote) - maxlen, step):
        sentences.append(quote[i: i + maxlen])
        next_chars.append(quote[i + maxlen])
    sentences.append(quote[-maxlen:])
    next_chars.append(quote[-1])
print('nb sequences:', len(sentences))


# In[10]:


print(sentences[:20])


# In[11]:


print('Vectorization...')
x = np.zeros((len(sentences), maxlen, len(chars)), dtype=np.bool)
y = np.zeros((len(sentences), len(chars)), dtype=np.bool)
for i, sentence in enumerate(sentences):
    for t, char in enumerate(sentence):
        x[i, t, char_indices[char]] = 1
    y[i, char_indices[next_chars[i]]] = 1


# In[12]:


print(x.shape, y.shape, len(chars))


# In[13]:


## Model 
print('Build model...')
input_sequences = Input((maxlen, len(chars)) , name="input_sequences")
lstm = Bidirectional(LSTM(256, return_sequences= True, input_shape=(maxlen, len(chars))), name = 'bidirectional')(input_sequences)
lstm = Dropout(0.1, name = 'dropout_bidirectional_lstm')(lstm)
lstm = LSTM(64, input_shape=(maxlen, len(chars)), name = 'lstm')(lstm)
lstm = Dropout(0.1,  name = 'drop_out_lstm')(lstm)

dense = Dense(15 * len(chars), name = 'first_dense')(lstm)
dense = Dropout(0.1,  name = 'drop_out_first_dense')(dense)
dense = Dense(5 * len(chars), name = 'second_dense')(dense)
dense = Dropout(0.1,  name = 'drop_out_second_dense')(dense)
dense = Dense(len(chars), name = 'last_dense')(dense)

next_char = Activation('softmax', name = 'activation')(dense)

model = Model([input_sequences], next_char)
model.compile(optimizer='adam', loss='categorical_crossentropy')


# In[14]:


print(model.summary())


# In[15]:


model.fit([x], y,
         batch_size=128,
          epochs= 15
         )


# In[61]:


model.fit([x], y,
         batch_size=2048,
          epochs= 2
         )


# In[88]:


model.fit([x], y,
         batch_size=1024,
          epochs= 2
         )


# In[21]:


two_first_words = [bigram for bigram in [' '.join(word_tokenize(quote)[:2]) for quote in quotes] if len(bigram) <= maxlen]

def sample(preds, temperature=1.0):
    # helper function to sample an index from a probability array
    preds = np.asarray(preds).astype('float64')
    preds = np.log(preds) / temperature
    exp_preds = np.exp(preds)
    preds = exp_preds / np.sum(exp_preds)
    probas = np.random.multinomial(1, preds, 1)
    return np.argmax(probas)


# In[22]:


def generate_quote(sentence = None, diversity = 0.8):
    
    if not sentence: ## if input is null then sample two first word from dataset
        random_index = np.random.randint(0, len(two_first_words))
        sentence = two_first_words[random_index]
        
    if len(sentence) > maxlen:
        sentence = sentence[-maxlen:]
    elif len(sentence) < maxlen:
        sentence = ' '*(maxlen - len(sentence)) + sentence
        
    generated = ''
    generated += sentence
    sys.stdout.write(generated)
    
    next_char = 'Empty'
    total_word = 0 
    
    max_word = 15
    
    while ((next_char not in ['\n', '.']) & (total_word <= 500)):
    
        x_pred = np.zeros((1, maxlen, len(chars)))
        for t, char in enumerate(sentence):
            x_pred[0, t, char_indices[char]] = 1.

        preds = model.predict(x_pred, verbose=0)[0]
        next_index = sample(preds, diversity)
        next_char = indices_char[next_index]

        if next_char == ' ':
           total_word += 1
        generated += next_char
        sentence = sentence[1:] + next_char

        sys.stdout.write(next_char)
        sys.stdout.flush()
    print()


# In[63]:


generate_quote()


# In[64]:


generate_quote()


# In[65]:


generate_quote()


# In[67]:


generate_quote()


# In[68]:


generate_quote()


# In[71]:


generate_quote()


# In[85]:


generate_quote()


# In[89]:


generate_quote()


# In[90]:


generate_quote()


# In[91]:


generate_quote()


# In[124]:


generate_quote()


# In[125]:


# serialize model to JSON
model_json = model.to_json()
with open("quoted_model_char.json", "w") as json_file:
    json_file.write(model_json)

# serialize weights to HDF5
model.save_weights("quoted_model_char.h5")
print("Saved quoted_model to disk")

