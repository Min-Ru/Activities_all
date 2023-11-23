import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.metrics import classification_report
from transformers import BertTokenizer, BertModel
import torch
from torch import nn, optim
from torch.utils.data import DataLoader, TensorDataset
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import re


def importance_classify(train_data, test_data, class_weights=None):
    X_combined = pd.concat([train_data, test_data], ignore_index=True)
    # 計算活動持續天數
    X_combined['days'] = X_combined.apply(
        lambda row: (row['end_date'] - row['start_date']).days + 1, axis=1)
    # 切分特徵與標籤
    X = X_combined[['name', 'category', 'keywords', 'city_id', 'area_id', 'address', 'days']]  # noqa
    y = train_data['importance']  # 標籤

    # 填補缺失值
    X['keywords'] = X['keywords'].fillna('')
    X['city_id'] = X['city_id'].fillna(0)
    X['area_id'] = X['area_id'].fillna(0)

    # 去除名稱中帶有數字
    # 定義正則表達式模式，匹配数字
    pattern = re.compile(r'\d+')
    # 從列中去除數字
    X["name"] = X["name"].apply(lambda x: re.sub(pattern, '', x))

    # 使用預訓練的BERT模型進行特徵提取
    tokenizer = BertTokenizer.from_pretrained('bert-base-chinese')
    model = BertModel.from_pretrained(
        'bert-base-chinese', output_hidden_states=True)

    # 將文本轉換為BERT输入格式
    X_text = X['name'] + ' ' + X['category'] + ' ' + X['keywords'] + ' ' + X['address']  # noqa
    encoded = tokenizer(
        X_text.tolist(), padding=True, truncation=True, return_tensors='pt')

    # 獲取BERT模型輸出
    with torch.no_grad():
        output = model(**encoded)

    # 使用BERT的最後一个隐藏狀態作为文本特征
    text_features = output.hidden_states[-1][:, 0, :]

    # 獲取數值特徵
    X_numeric = X[['city_id', 'area_id', 'days']].values

    # 合併文本特徵和數值特徵
    X_features = np.hstack((text_features.numpy(), X_numeric))

    # 初始化分類器
    model = nn.Sequential(
        nn.Linear(X_features.shape[1], 128),
        nn.ReLU(),
        nn.Dropout(0.5),
        nn.Linear(128, 2)
    )

    # 定義损失函数和優化器
    criterion = nn.CrossEntropyLoss(weight=class_weights)
    optimizer = optim.Adam(model.parameters(), lr=0.001)

    # 將數據轉換為PyTorch張量
    X_train_tensor = torch.tensor(
        X_features[:-len(test_data)], dtype=torch.float32)
    y_train_tensor = torch.tensor(y.values, dtype=torch.long)
    X_test_tensor = torch.tensor(
        X_features[-len(test_data):], dtype=torch.float32)

    # 創建數據加载器
    train_dataset = TensorDataset(X_train_tensor, y_train_tensor)
    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    # 訓練模型
    num_epochs = 10
    for epoch in range(num_epochs):
        model.train()
        for inputs, labels in train_loader:
            optimizer.zero_grad()
            outputs = model(inputs)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()

    # 預測
    model.eval()
    with torch.no_grad():
        y_pred = model(X_test_tensor).argmax(dim=1)

    # 將y_pred從tensor轉成Series
    y_pred = pd.Series(y_pred)

    return y_pred


def importance_evaluation(data, y_test, y_pred):
    # 繪製混淆矩阵
    confusion = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(confusion, annot=True, fmt='d', cmap='Blues')
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title('Confusion Matrix')
    plt.show()
    # 計算準確率
    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy:", accuracy)
    # 計算混淆矩阵
    confusion = confusion_matrix(y_test, y_pred)
    print("Confusion Matrix:")
    print(confusion)
    # 生成分类报告
    class_names = ['Not Important', 'Important']  # 根据您的标签类别进行调整
    report = classification_report(y_test, y_pred, target_names=class_names)
    print("Classification Report:")
    print(report)
    # 列出分類正確與分類錯誤之dataframe
    # 預測值的index調成與test一樣
    y_pred.index = y_test.index
    # 找出分類正確和分類錯誤的索引
    correct_indices = y_test[y_pred == y_test].index
    incorrect_indices = y_test[y_pred != y_test].index

    # 提取分類正确和分類錯誤的數據
    correct_data = data.loc[correct_indices]
    incorrect_data = data.loc[incorrect_indices]

    # 將结果存為DataFrame
    correct_df = pd.DataFrame(correct_data)
    incorrect_df = pd.DataFrame(incorrect_data)

    return correct_df, incorrect_df
