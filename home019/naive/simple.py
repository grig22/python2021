import pandas as pd
import numpy as np

train_df = pd.read_csv('../data/train.csv')
review_summaries = [ll.lower() for ll in train_df['Reviews_Summary'].values]

from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer()
X = vectorizer.fit_transform(review_summaries)
print(X.shape)

from sklearn.model_selection import train_test_split
Y = train_df.Prediction.values
X_train, X_test, y_train, y_test = train_test_split(X, Y, train_size=0.7, random_state=42)


from sklearn import linear_model
clf = linear_model.SGDClassifier(
    max_iter=1000,
    random_state=42,
    loss="log",
    penalty="l2",
    alpha=1e-3,
    eta0=1.0,
    learning_rate="constant")

clf.fit(X_train, y_train)

from sklearn.metrics import accuracy_score
print(f"Train accuracy = {accuracy_score(y_train, clf.predict(X_train)):.3f}")
print(f"Test accuracy = {accuracy_score(y_test, clf.predict(X_test)):.3f}")


def sigmoid(
        x,  # размеченный образец
        w,  # вектор весов
        #  TODO b0
):
    z = w.dot(x)
    return 1.0 / (1.0 + np.exp(-z))

#  https://web.stanford.edu/~jurafsky/slp3/5.pdf
#  https://dphi.tech/blog/tutorial-on-logistic-regression-using-python/

#  https://machinelearningmastery.com/implement-logistic-regression-stochastic-gradient-descent-scratch-python/


class LogisticRegression:
    def __init__(self):
        self.W = None

    def fit(self, x, y):
        num_samples, num_features = x.shape
        num_samples = 1000
        print(f"num_samples = {num_samples}, num_features = {num_features}")
        print(y.shape)
        self.W = np.ones(num_features)

        l_rate = 0.5
        n_epoch = 1000

        for epoch in range(n_epoch):
            sum_error = 0
            for ii in range(num_samples):
                row = x[ii].toarray().flatten()
                yhat = sigmoid(row, self.W)
                error = y[ii] - yhat
                sum_error += error ** 2
                for i in range(num_features):
                    self.W[i] = self.W[i] + l_rate * error * yhat * (1.0 - yhat) * row[i]
            print('>epoch=%d, lrate=%.3f, error=%.3f' % (epoch, l_rate, sum_error))


log_reg = LogisticRegression()
log_reg.fit(X_train, y_train)