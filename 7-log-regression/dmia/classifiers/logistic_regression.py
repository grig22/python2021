import numpy as np
from scipy import sparse
# https://github.com/huyouare/CS231n/blob/master/assignment1/cs231n/classifiers/linear_classifier.py
# https://github.com/Dementiy/otus-python-0717/blob/master/homework07/logistic_regression.py
# https://github.com/maxis42/CS231n/blob/master/assignment1/cs231n/classifiers/linear_classifier.py

class LogisticRegression:
    def __init__(self):
        self.w = None
        self.loss_history = None

    def sigmoid(self, z):
        return 1.0 / (1.0 + np.exp(-z))

    def train(self, X, y, learning_rate=1e-3, reg=1e-5, num_iters=1000, batch_size=200, verbose=False):
        """
        Train this classifier using stochastic gradient descent.

        Inputs:
        - X: N x D array of training data. Each training point is a D-dimensional
             column.
        - y: 1-dimensional array of length N with labels 0-1, for 2 classes.
        - learning_rate: (float) learning rate for optimization.
        - reg: (float) regularization strength.
        - num_iters: (integer) number of steps to take when optimizing
        - batch_size: (integer) number of training examples to use at each step.
        - verbose: (boolean) If true, print progress during optimization.

        Outputs:
        A list containing the value of the loss function at each training iteration.
        """
        # Add a column of ones to X for the bias sake.
        X = LogisticRegression.append_biases(X)
        num_train, dim = X.shape
        if self.w is None:
            # lazily initialize weights
            self.w = np.random.randn(dim) * 0.01

        # Run stochastic gradient descent to optimize W
        self.loss_history = []
        # for it in xrange(num_iters):
        for it in range(num_iters):
            #########################################################################
            # TODO:                                                                 #
            # Sample batch_size elements from the training data and their           #
            # corresponding labels to use in this round of gradient descent.        #
            # Store the data in X_batch and their corresponding labels in           #
            # y_batch; after sampling X_batch should have shape (batch_size, dim)   #
            # and y_batch should have shape (batch_size,)                           #
            #                                                                       #
            # Hint: Use np.random.choice to generate indices. Sampling with         #
            # replacement is faster than sampling without replacement.              #
            #########################################################################
            X_batch = None
            y_batch = None
            indices = np.random.choice(num_train, batch_size)
            X_batch = X[indices, :]
            y_batch = y[indices]
            #########################################################################
            #                       END OF YOUR CODE                                #
            #########################################################################

            # evaluate loss and gradient
            loss, gradW = self.loss(X_batch, y_batch, reg)
            self.loss_history.append(loss)
            # perform parameter update
            #########################################################################
            # TODO:                                                                 #
            # Update the weights using the gradient and the learning rate.          #
            #########################################################################
            self.w += -1 * learning_rate * gradW
            #########################################################################
            #                       END OF YOUR CODE                                #
            #########################################################################

            if verbose and it % 100 == 0:
                print('iteration %d / %d: loss %f' % (it, num_iters, loss))

        return self

    def predict_proba(self, X, append_bias=False):
        """
        Use the trained weights of this linear classifier to predict probabilities for
        data points.

        Inputs:
        - X: N x D array of data. Each row is a D-dimensional point.
        - append_bias: bool. Whether to append bias before predicting or not.

        Returns:
        - y_proba: Probabilities of classes for the data in X. y_pred is a 2-dimensional
          array with a shape (N, 2), and each row is a distribution of classes [prob_class_0, prob_class_1].
        """
        if append_bias:
            X = LogisticRegression.append_biases(X)
        ###########################################################################
        # TODO:                                                                   #
        # Implement this method. Store the probabilities of classes in y_proba.   #
        # Hint: It might be helpful to use np.vstack and np.sum                   #
        ###########################################################################
        predictions = self.sigmoid(X.dot(self.w.T))
        y_proba = np.vstack([1 - predictions, predictions]).T
        ###########################################################################
        #                           END OF YOUR CODE                              #
        ###########################################################################
        return y_proba

    def predict(self, X):
        """
        Use the ```predict_proba``` method to predict labels for data points.

        Inputs:
        - X: N x D array of training data. Each column is a D-dimensional point.

        Returns:
        - y_pred: Predicted labels for the data in X. y_pred is a 1-dimensional
          array of length N, and each element is an integer giving the predicted
          class.
        """

        ###########################################################################
        # TODO:                                                                   #
        # Implement this method. Store the predicted labels in y_pred.            #
        ###########################################################################
        y_proba = self.predict_proba(X, append_bias=True)
        y_pred = y_proba.argmax(axis=1)

        ###########################################################################
        #                           END OF YOUR CODE                              #
        ###########################################################################
        return y_pred

    def loss(self, X_batch, y_batch, reg):
        return svm_loss_vectorized(self.w, X_batch, y_batch, reg)
        #
        # """Logistic Regression loss function
        # Inputs:
        # - X: N x D array of data. Data are D-dimensional rows
        # - y: 1-dimensional array of length N with labels 0-1, for 2 classes
        # Returns:
        # a tuple of:
        # - loss as single float
        # - gradient with respect to weights w; an array of same shape as w
        # """
        dw = np.zeros_like(self.w)  # initialize the gradient as zero
        loss = 0
        # Compute loss and gradient. Your code should not contain python loops.
        h = self.sigmoid(X_batch.dot(self.w))
        loss = -np.dot(y_batch, np.log(h)) - np.dot((1 - y_batch), np.log(1.0 - h))
        dw = (h - y_batch) * X_batch

        # Right now the loss is a sum over all training examples, but we want it
        # to be an average instead so we divide by num_train.
        # Note that the same thing must be done with gradient.
        num_train = X_batch.shape[0]
        loss = loss / num_train
        dw = dw / num_train

        # Add regularization to the loss and gradient.
        # Note that you have to exclude bias term in regularization.
        loss += (reg / (2.0 * num_train)) * np.dot(self.w[:-1], self.w[:-1])
        dw[:-1] = dw[:-1] + (reg * self.w[:-1]) / num_train

        return loss, dw

    @staticmethod
    def append_biases(X):
        return sparse.hstack((X, np.ones(X.shape[0])[:, np.newaxis])).tocsr()


def svm_loss_vectorized(W, X, y, reg):
  """
  Structured SVM loss function, vectorized implementation.
  Inputs and outputs are the same as svm_loss_naive.
  """
  loss = 0.0
  dW = np.zeros(W.shape) # initialize the gradient as zero

  #############################################################################
  # TODO:                                                                     #
  # Implement a vectorized version of the structured SVM loss, storing the    #
  # result in loss.                                                           #
  #############################################################################
  num_train = X.shape[0]

  loss = 0.0
  scores = X.dot(W) # (N, C)
  correct_class_scores = scores[range(num_train), y] # (N,)
  margins = scores - correct_class_scores[:,None] + 1 # (N, C)
  margins[range(num_train), y] = 0
  loss = np.sum(margins[margins > 0]) / num_train + reg * np.sum(W * W)
  #############################################################################
  #                             END OF YOUR CODE                              #
  #############################################################################

  #############################################################################
  # TODO:                                                                     #
  # Implement a vectorized version of the gradient for the structured SVM     #
  # loss, storing the result in dW.                                           #
  #                                                                           #
  # Hint: Instead of computing the gradient from scratch, it may be easier    #
  # to reuse some of the intermediate values that you used to compute the     #
  # loss.                                                                     #
  #############################################################################
  positive_margins = np.zeros(margins.shape) # (N, C)
  positive_margins[margins > 0] = 1
  positive_margins_cnts = np.sum(positive_margins, axis=1) # (N,)
  positive_margins[range(num_train), y] -= positive_margins_cnts
  dW = np.dot(X.T, positive_margins) # (N, D).T x (N, C) = (D, C)
  dW = dW / num_train + reg * 2 * W
  #############################################################################
  #                             END OF YOUR CODE                              #
  #############################################################################

  return loss, dW