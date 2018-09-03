import os
import datetime
import random as rng
import time
import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.callbacks import CSVLogger
from sklearn.metrics import confusion_matrix

# Inputs
x_filename = '/home/valentin_m_andrei/datasets/500ms_specgram/x_train_normalized.txt'
y_filename = '/home/valentin_m_andrei/datasets/500ms_specgram/y_train.txt'
s_model_save_dir = '/home/valentin_m_andrei/checkpoints/'

# x_filename = 'E:/1_Proiecte_Curente/1_Speaker_Counting/datasets/x_dummy.txt'
# y_filename = 'E:/1_Proiecte_Curente/1_Speaker_Counting/datasets/y_dummy.txt'
# s_model_save_dir = 'E:/1_Proiecte_Curente/1_Speaker_Counting/checkpoints/'

# Architecture
n_size_x            = 127
n_size_y            = 48
n_conv_blocks       = 3
v_convs_per_block   = [3, 3, 3]
v_pool_size         = [1, 1, 2]
v_filters_per_conv  = [64, 128, 256]
v_krn_sz_per_conv   = [3, 3, 3]
f_dropout_conv      = 1.0
n_fc_layers         = 2
v_fc_layer_sz       = [1024, 512]
v_dropout_fc        = [0.25, 1.0]

# Training
f_use_for_validation    = 0.02
sz_batch                = 256
n_epochs                = 160
f_start_lr              = 0.001

# Plotting & debugging
# TODO

class ConfusionMatrix(keras.callbacks.Callback):
    def on_epoch_end(self, epoch, logs={}):
        print('Confusion matrix: ')
        y_prob = self.model.predict(self.validation_data[0])
        y_pred = np.argmax(y_prob, axis=1)
        y_true = np.argmax(self.validation_data[1], axis=1)
        print(confusion_matrix(y_true, y_pred))

def main(_):

    # os.environ["CUDA_VISIBLE_DEVICES"] = ""

    ###########################################################################
    # Load Train / Test Data
    ###########################################################################

    t_start = time.time()

    # Load Input Files
    inputs = np.loadtxt(x_filename)
    outputs = np.loadtxt(y_filename)

    # Experiment Parameters
    n_classes = outputs.shape[1]
    sz_set = inputs.shape[0]
    sz_validate = int(sz_set * f_use_for_validation)
    sz_train = int(sz_set - sz_validate)
    sz_input = inputs.shape[1]

    t_stop = time.time()

    # Debug Messages
    print("Input prepare time   : ", str(t_stop - t_start))
    print("Total inputs         : ", str(sz_set))
    print("Input length         : ", str(sz_input))
    print("Number of classes    : ", str(n_classes))
    print("Used for training    : ", str(sz_train))
    print("Used for validation  : ", str(sz_validate))

    ###########################################################################
    # Split Data into Train and Validate
    ###########################################################################

    x_train = inputs[0:sz_train][:]
    x_validate = inputs[sz_train:sz_set][:]
    y_train = outputs[0:sz_train][:]
    y_validate = outputs[sz_train:sz_set][:]

    ###########################################################################
    # Targeted Neural Network Architecture
    ###########################################################################

    the_network = keras.Sequential()

    # Reshape the layer into a 2D structure
    the_network.add(keras.layers.Reshape((n_size_x, n_size_y, 1), input_shape = (n_size_x * n_size_y,)))

    # Add the 2D convolutional blocks
    for i in range(0, n_conv_blocks):
        n_convs_per_block = v_convs_per_block[i]
        n_filters_per_conv = v_filters_per_conv[i]
        n_krn_size_per_conv = v_krn_sz_per_conv[i]
        n_pool_size = v_pool_size[i]

        # Add the connected convolutional layers
        for j in range (0, n_convs_per_block):
            the_network.add(keras.layers.Conv2D(filters = n_filters_per_conv,
                                                kernel_size = n_krn_size_per_conv,
                                                padding = "valid"))

        # Add max pooling layer
        if (n_pool_size != 1): 
            the_network.add(keras.layers.MaxPooling2D(pool_size = (n_pool_size, n_pool_size),
                                                      padding = "valid"))


    if (f_dropout_conv < 1.0):
        the_network.add(keras.layers.Dropout(f_dropout_prob_L1))

    # Add batch normalization
    the_network.add(keras.layers.BatchNormalization())

    # Prepare input for fully connected layers
    the_network.add(keras.layers.Flatten())

    # Add fully connected layers
    for i in range(0, n_fc_layers):
        the_network.add(keras.layers.Dense(v_fc_layer_sz[i], activation='relu'))

        # Add dropout
        if (v_dropout_fc[i] < 1.0):
            the_network.add(keras.layers.Dropout(v_dropout_fc[i]))

    # Add output layer
    the_network.add(keras.layers.Dense(n_classes, activation='softmax'))

    ###########################################################################
    # Run Training
    ###########################################################################

    the_network.compile(optimizer=tf.train.AdamOptimizer(f_start_lr), 
                        loss=keras.losses.categorical_crossentropy, 
                        metrics=['categorical_accuracy'])
   
    s_log_file = s_model_save_dir + "the_network_log.csv"

    class_predictions = ConfusionMatrix()

    csv_logger = CSVLogger(s_log_file, append=True, separator=';')
    
    model_saver = keras.callbacks.ModelCheckpoint(s_model_save_dir + "the_network.h5", 
                                                  monitor='val_categorical_accuracy', 
                                                  verbose=0, 
                                                  save_best_only=True, 
                                                  save_weights_only=False, 
                                                  mode='auto', 
                                                  period=1)

    t_stiart = time.time()
    the_network.fit(x = x_train, 
                    y = y_train, 
                    epochs=n_epochs, 
                    batch_size=sz_batch, 
                    validation_data=(x_validate, y_validate),
                    callbacks=[class_predictions, csv_logger, model_saver])
    
    t_stop = time.time()
    print("Training time : " + str(t_stop - t_start))

if __name__ == '__main__':

    tf.app.run()