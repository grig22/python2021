import pandas as pd

train_df = pd.read_csv('../data/train.csv')
review_summaries = [ll.lower() for ll in train_df['Reviews_Summary'].values]

from sklearn.feature_extraction.text import TfidfVectorizer
vectorizer = TfidfVectorizer()
tfidfed = vectorizer.fit_transform(review_summaries)

from sklearn.model_selection import train_test_split
X = tfidfed
y = train_df.Prediction.values
X_train, X_test, y_train, y_test = train_test_split(X, y, train_size=0.7, random_state=42)


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

