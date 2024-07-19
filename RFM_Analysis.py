import pandas as pd
import plotly.express as px
import plotly.io as pio
import plotly.graph_objects as go
import plotly.colors
from datetime import datetime
import pandas as pd
pio.templates.default = "plotly_white"

data = pd.read_csv("rfm_data.csv")


# Convert 'PurchaseDate' to datetime
data['PurchaseDate'] = pd.to_datetime(data['PurchaseDate'], errors='coerce')

# Calculate Recency
data['Recency'] = (datetime.now().date() - data['PurchaseDate'].dt.date).apply(lambda x: x.days)

# Calculate Frequency
frequency_data = data.groupby('CustomerID')['OrderID'].count().reset_index()
frequency_data.rename(columns={'OrderID': 'Frequency'}, inplace=True)
data = data.merge(frequency_data, on='CustomerID', how='left')
# Calculate Monetary Value
monetary_data = data.groupby('CustomerID')['TransactionAmount'].sum().reset_index()
monetary_data.rename(columns={'TransactionAmount': 'MonetaryValue'}, inplace=True)
data = data.merge(monetary_data, on='CustomerID', how='left')

# Define scoring criteria for each RFM value
recency_scores = [5, 4, 3, 2, 1]  # Higher score for lower recency (more recent)
frequency_scores = [1, 2, 3, 4, 5]  # Higher score for higher frequency
monetary_scores = [1, 2, 3, 4, 5]  # Higher score for higher monetary value

# Calculate RFM scores
data['RecencyScore'] = pd.cut(data['Recency'], bins=5, labels=recency_scores)
data['FrequencyScore'] = pd.cut(data['Frequency'], bins=5, labels=frequency_scores)
data['MonetaryScore'] = pd.cut(data['MonetaryValue'], bins=5, labels=monetary_scores)

# Convert RFM scores to numeric type
data['RecencyScore'] = data['RecencyScore'].astype(int)
data['FrequencyScore'] = data['FrequencyScore'].astype(int)
data['MonetaryScore'] = data['MonetaryScore'].astype(int)

# Calculate RFM score by combining the individual scores
data['RFM_Score'] = data['RecencyScore'] + data['FrequencyScore'] + data['MonetaryScore']

# Create RFM segments based on the RFM score
segment_labels = ['Low-Value', 'Mid-Value', 'High-Value']
data['Value Segment'] = pd.cut(data['RFM_Score'], bins=3, labels=segment_labels)


# RFM Segment Distribution
segment_counts = data['Value Segment'].value_counts().reset_index()
segment_counts.columns = ['Value Segment', 'Count']

pastel_colors = px.colors.qualitative.Pastel

# Create the bar chart
fig_segment_dist = px.bar(segment_counts, x='Value Segment', y='Count',color='Value Segment', color_discrete_sequence=pastel_colors,title='RFM Value Segment Distribution')

# Update the layout
fig_segment_dist.update_layout(xaxis_title='RFM Value Segment',yaxis_title='Count',showlegend=False)

# Show the figure
fig_segment_dist.show()


# Create a new column for RFM Customer Segments
data['RFM Customer Segments'] = ''

# Assign RFM segments based on the RFM score
data.loc[data['RFM_Score'] >= 9, 'RFM Customer Segments'] = 'Champions'
data.loc[(data['RFM_Score'] >= 6) & (data['RFM_Score'] < 9), 'RFM Customer Segments'] = 'Potential Loyalists'
data.loc[(data['RFM_Score'] >= 5) & (data['RFM_Score'] < 6), 'RFM Customer Segments'] = 'At Risk Customers'
data.loc[(data['RFM_Score'] >= 4) & (data['RFM_Score'] < 5), 'RFM Customer Segments'] = "Can't Lose"
data.loc[(data['RFM_Score'] >= 3) & (data['RFM_Score'] < 4), 'RFM Customer Segments'] = "Lost"

# Print the updated data with RFM segments
# print(data[['CustomerID', 'RFM Customer Segments']])




pastel_colors = plotly.colors.qualitative.Pastel

segment_counts = data['RFM Customer Segments'].value_counts()

# Create a bar chart to compare segment counts
fig = go.Figure(data=[go.Bar(x=segment_counts.index, y=segment_counts.values,
                            marker=dict(color=pastel_colors))])

# Set the color of the Champions segment as a different color
champions_color = 'rgb(158, 202, 225)'
fig.update_traces(marker_color=[champions_color if segment == 'Champions' else pastel_colors[i]
                                for i, segment in enumerate(segment_counts.index)],
                  marker_line_color='rgb(8, 48, 107)',
                  marker_line_width=1.5, opacity=0.6)

# Update the layout
fig.update_layout(title='Comparison of RFM Segments',
                  xaxis_title='RFM Segments',
                  yaxis_title='Number of Customers',
                  showlegend=False)

fig.show()



# Calculate the average Recency, Frequency, and Monetary scores for each segment
segment_scores = data.groupby('RFM Customer Segments')[['RecencyScore', 'FrequencyScore', 'MonetaryScore']].mean().reset_index()

# Create a grouped bar chart to compare segment scores
fig = go.Figure()

# Add bars for Recency score
fig.add_trace(go.Bar(
    x=segment_scores['RFM Customer Segments'],
    y=segment_scores['RecencyScore'],
    name='Recency Score',
    marker_color='rgb(158,202,225)'
))

# Add bars for Frequency score
fig.add_trace(go.Bar(
    x=segment_scores['RFM Customer Segments'],
    y=segment_scores['FrequencyScore'],
    name='Frequency Score',
    marker_color='rgb(94,158,217)'
))

# Add bars for Monetary score
fig.add_trace(go.Bar(
    x=segment_scores['RFM Customer Segments'],
    y=segment_scores['MonetaryScore'],
    name='Monetary Score',
    marker_color='rgb(32,102,148)'
))

# Update the layout
fig.update_layout(
    title='Comparison of RFM Segments based on Recency, Frequency, and Monetary Scores',
    xaxis_title='RFM Segments',
    yaxis_title='Score',
    barmode='group',
    showlegend=True
)

fig.show()


# Calculate CLTV metrics

# Calculate Average Purchase Value (APV)
apv = data.groupby('CustomerID')['TransactionAmount'].mean().reset_index()
apv.rename(columns={'TransactionAmount': 'AveragePurchaseValue'}, inplace=True)
data = data.merge(apv, on='CustomerID', how='left')

# Calculate Purchase Frequency (PF)
purchase_frequency = data.groupby('CustomerID')['OrderID'].nunique().reset_index()
purchase_frequency.rename(columns={'OrderID': 'PurchaseFrequency'}, inplace=True)
data = data.merge(purchase_frequency, on='CustomerID', how='left')

# Assume an average customer lifespan (this can be adjusted based on historical data)
customer_lifespan = 3  # In years

# Calculate CLTV
data['CLTV'] = (data['AveragePurchaseValue'] * data['PurchaseFrequency']) * customer_lifespan

# Calculate the average CLTV for the "Lost" segment
lost_segment_cltv = data[data['RFM Customer Segments'] == "Lost"]['CLTV'].mean()

print(f"Average CLTV for Lost Segment: ${lost_segment_cltv:.2f}")

# Function to simulate re-engagement
def simulate_re_engagement(data):
    reactivation_rate = 0.2  # Assume 20% of lost customers can be re-engaged
    lost_customers = data[data['RFM Customer Segments'] == "Lost"]
    reactivated_customers = lost_customers.sample(frac=reactivation_rate, random_state=1)
    
    # Re-engage and update their segment to "Potential Loyalists"
    data.loc[reactivated_customers.index, 'RFM Customer Segments'] = 'Potential Loyalists'
    return data

# Apply the simulation
data = simulate_re_engagement(data)

# Check the new segment distribution
new_segment_counts = data['RFM Customer Segments'].value_counts()
print(new_segment_counts)

# Plot new segment distribution after re-engagement
fig = go.Figure(data=[go.Bar(x=new_segment_counts.index, y=new_segment_counts.values, marker=dict(color=pastel_colors))])

# Update the layout
fig.update_layout(title='New Distribution of RFM Segments after Re-engagement',
                  xaxis_title='RFM Segments',
                  yaxis_title='Number of Customers',
                  showlegend=False)

fig.show()