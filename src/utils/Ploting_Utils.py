import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

def plot_distributions(df, n_cols=3) -> None:
    """
    Plot the distributions of all columns in a DataFrame using subplots.
    Parameters:
        df (pd.DataFrame): The DataFrame containing the data.
        n_cols (int): Number of columns in the subplot grid (default is 3).
    Returns:
        None: Displays the plots.
    """
    # Get column names and calculate the grid size
    columns = df.columns
    n_rows = (len(columns) + n_cols - 1) // n_cols  # Calculate the number of rows

    # Create a figure and axes
    fig, axes = plt.subplots(n_rows, n_cols, figsize=(5 * n_cols, 3 * n_rows))

    # Flatten axes for easy iteration
    axes = axes.flatten()

    # Plot each column in a subplot
    for i, col in enumerate(columns):
        ax = axes[i]
        if pd.api.types.is_categorical_dtype(df[col]) or pd.api.types.is_object_dtype(df[col]):
            # Plot for categorical data
            sns.countplot(x=df[col], ax=ax)
            ax.set_title(f'Count of {col.upper()}')
            ax.set_xlabel(col)
            ax.set_ylabel('Count')
        else:
            # Plot for numerical data
            sns.histplot(df[col], kde=True, bins=30, ax=ax)
            ax.set_title(f'Distribution of {col.upper()}')
            ax.set_xlabel(col)
            ax.set_ylabel('Frequency')

    # Remove any unused subplots
    for i in range(len(columns), len(axes)):
        fig.delaxes(axes[i])

    # Adjust layout
    plt.tight_layout()
    plt.show()

def plot_correlation_heatmap(df, figsize=(10, 8), cmap='coolwarm'):
    """
    Generate a correlation heatmap from a DataFrame.

    Parameters:
        df (pd.DataFrame): The DataFrame containing the data.
        figsize (tuple): The size of the plot (default is (10, 8)).
        cmap (str): Colormap for the heatmap (default is 'coolwarm').

    Returns:
        None: Displays the heatmap.
    """
    # Calculate the correlation matrix
    correlation_matrix = df.corr()

    # Set up the plot
    plt.figure(figsize=figsize)

    # Create the heatmap
    sns.heatmap(correlation_matrix, annot=True, cmap=cmap, fmt=".2f", linewidths=0.5)

    # Configure plot aesthetics
    plt.title('Correlation Heatmap', fontsize=16)
    plt.xticks(rotation=45)
    plt.yticks(rotation=45)

    # Display the heatmap
    plt.show()
