'''
Train DM Challenge classifier
GPU run command:
    THEANO_FLAGS=mode=FAST_RUN,device=gpu,floatX=float32 python train.py <in:dataset> <out:trained_model>

'''
from __future__ import print_function
import numpy as np
import sys
import tables
from keras.models import Sequential, Model
from keras.layers import Input
from keras.layers.core import Flatten, Dense, Dropout
from keras.layers.convolutional import Convolution2D, MaxPooling2D, ZeroPadding2D
from keras.optimizers import SGD, RMSprop
from sklearn.model_selection import train_test_split
from datetime import datetime
from keras.applications.vgg16 import VGG16

MODEL_PATH = 'model_{}.h5'.format(datetime.now().strftime('%Y%m%d%H%M%S'))

# training parameters
BATCH_SIZE = 50
NB_EPOCH = 10

# dataset
DATASET_BATCH_SIZE = 1000

# command line arguments
dataset_file = sys.argv[1]
model_file = sys.argv[2] if len(sys.argv) > 2 else MODEL_PATH

# loading dataset
print('Loading train dataset: {}'.format(dataset_file))
datafile = tables.open_file(dataset_file, mode='r')
dataset = datafile.root
print(dataset.data[:].shape)

# setup model
print('Preparing model')
# model = VGG_16(VGG16, dataset.data[0].shape)
base_model = VGG16(weights='imagenet', include_top=False, input_tensor=Input(shape=(3, 224, 224)))
x = base_model.output
x = Flatten()(x)
x = Dense(4096, activation='relu')(x)
x = Dropout(0.5)(x)
x = Dense(4096, activation='relu')(x)
x = Dropout(0.5)(x)
predictions = Dense(1, activation='sigmoid')(x)
# predictions = Dense(1, activation='softmax')(x)

# this is the model we will train
model = Model(input=base_model.input, output=predictions)

# freeze base_model layers
for layer in base_model.layers:
    layer.trainable = False

# compile the model (should be done *after* setting layers to non-trainable)
model.compile(loss='binary_crossentropy', optimizer='rmsprop', metrics=['accuracy'])
# sgd = SGD(lr=1e-3, decay=1e-6, momentum=0.9, nesterov=True)
# model.compile(optimizer=sgd, loss='binary_crossentropy', metrics=['accuracy'])

# training model
num_rows = dataset.data.nrows
if num_rows > DATASET_BATCH_SIZE:
    # batch training
    num_iterate = num_rows / DATASET_BATCH_SIZE
    print('Training model using {} data in batch of {}'.format(num_rows, DATASET_BATCH_SIZE))
    for e in range(NB_EPOCH):
        print('Epoch {}/{}'.format(e + 1, NB_EPOCH))
        for i in range(num_iterate):
            print('Data batch {}/{}'.format(i + 1, num_iterate))
            begin = i + i * DATASET_BATCH_SIZE
            end = begin + DATASET_BATCH_SIZE
            X_train, X_test, Y_train, Y_test = train_test_split(
                dataset.data[begin:end], dataset.labels[begin:end],
                test_size=0.10
            )
            model.fit(X_train, Y_train,
                      batch_size=BATCH_SIZE,
                      nb_epoch=1,
                      validation_data=(X_test, Y_test),
                      shuffle=True)
else:
    # one-go training
    X_train, X_test, Y_train, Y_test = train_test_split(dataset.data[:], dataset.labels[:], test_size=0.10)
    model.fit(X_train, Y_train,
              batch_size=BATCH_SIZE,
              nb_epoch=NB_EPOCH,
              validation_data=(X_test, Y_test),
              shuffle=True)

# evaluating
print('Evaluating')
score = model.evaluate(X_test, Y_test)
print('{}: {}%'.format(model.metrics_names[1], score[1] * 100))

# saving model
print('Saving model')
model.save(model_file)

# close dataset
datafile.close()

print('Done.')
