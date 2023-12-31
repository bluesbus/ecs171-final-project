import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from sklearn.metrics import mean_squared_error, r2_score

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class CustomDataset(Dataset):
    def __init__(self, data):
        self.data = data

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        # Assuming the last column (index -1) is the label 'rating'
        x = self.data[idx, :-1]
        y = self.data[idx, -1]
        return x, y
    

def train_model(model: torch.nn.Module, train_loader: DataLoader, learningRate: float, epochs: int, lambda1: float, lambda2: float):

    criterion = torch.nn.MSELoss() 
    optimizer = torch.optim.SGD(model.parameters(), lr=learningRate)

    mse_history = []

    for epoch in range(epochs):
        for i, (inputs, labels) in enumerate(train_loader):
            inputs = inputs.float().to(device)
            labels = labels.float().to(device)

            optimizer.zero_grad()
            outputs = model(inputs)
        
            all_params = torch.cat([x.view(-1) for x in model.parameters()])
            l1_regularization = lambda1 * torch.norm(all_params, 1)
            l2_regularization = lambda2 * torch.norm(all_params, 2)
        
            loss = criterion(outputs.view(-1), labels) + l1_regularization + l2_regularization
            loss.backward()
            optimizer.step()

    # Calculate MSE for this epoch and store it
        with torch.no_grad():
            epoch_losses = []
            for inputs, labels in train_loader:
                inputs = inputs.float().to(device)
                labels = labels.float().to(device)
                outputs = model(inputs)
                epoch_loss = criterion(outputs.view(-1), labels)
                epoch_losses.append(epoch_loss.item())
            mse_history.append(np.mean(epoch_losses))

        #print(f'Epoch [{epoch+1}/{epochs}], Loss: {mse_history[-1]:.4f}')
    
    # print(torch.cat([x.view(-1) for x in model.parameters()]))
    return model, mse_history

# Predict target variable using test data
def test_model(model: torch.nn.Module, test_loader: DataLoader):
    model.eval()  # Set the model to evaluation mode
    all_predictions = []
    all_labels = []
    all_inputs = []

    with torch.no_grad():
        for inputs, labels in test_loader:
            inputs = inputs.float().to(device)
            labels = labels.float().to(device)
            predictions = model(inputs).cpu()
            all_predictions.extend(predictions.view(-1).numpy())
            all_labels.extend(labels.cpu().numpy())
            all_inputs.extend(inputs.cpu().numpy())

# Convert to numpy arrays for plotting
    all_predictions = np.array(all_predictions)
    all_labels = np.array(all_labels)
    all_inputs = np.array(all_inputs)
    
    return all_predictions, all_labels, all_inputs

def make_and_eval(model, train_data: np.ndarray, test_data: np.ndarray, learningRate, epochs, lambda1, lambda2):
    train_dataset = CustomDataset(train_data)
    test_dataset = CustomDataset(test_data)

    train_loader = DataLoader(train_dataset, batch_size=64, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=64, shuffle=False)

    # train the model on train set
    model, mse_history = train_model(model, train_loader, learningRate, epochs, lambda1, lambda2)

    try:
    # test the model on test set
        all_predictions, all_labels, all_inputs = test_model(model, test_loader)
        mse = mean_squared_error(all_labels, all_predictions)
        rmse = np.sqrt(mse)
        r2 = r2_score(all_labels, all_predictions)
    except:
        mse, rmse, r2 = "failed", "failed", "failed"

    print(f'Mean Squared Error: {mse}')
    print(f'Root Mean Squared Error: {rmse}')
    print(f'R-squared: {r2}')
    
    return model, (mse_history, mse, rmse, r2)
