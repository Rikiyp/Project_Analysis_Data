import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

def create_product_categories_state_df(df):
    # Pivot table asli: total payment_value untuk setiap state dan kategori produk
    pivot_df = df.pivot_table(values='payment_value', index='customer_state', columns='product_category_name', aggfunc='sum', fill_value=0)

    # Langkah 1: Mencari product_category_name dengan payment_value terbanyak untuk setiap state
    max_payment_category_per_state = pivot_df.idxmax(axis=1)  # Mengambil kategori dengan nilai terbesar per state
    max_payment_value_per_state = pivot_df.max(axis=1)  # Mengambil nilai terbesar per state

    # Langkah 2: Membuat DataFrame baru dengan customer_state, kategori terbesar, dan nilai payment_value
    product_categories_state_df = pd.DataFrame({
        'Top Product Category': max_payment_category_per_state,
        'Payment Value': max_payment_value_per_state
    })
    return product_categories_state_df

def create_payment_type_to_oder_df(df):
    paymentType_to_order = df.groupby(by="payment_type").agg({
    "order_id": "nunique"
}).sort_values(by="order_id", ascending=False)
    return paymentType_to_order



def create_rfm_df(df, recent_date):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",
        "order_id": "nunique",
        "payment_value": "sum"
    })

    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)
    rfm_df.drop("max_order_timestamp", axis=1, inplace=True)
    return rfm_df
    

def load_main_data():
    df = pd.read_csv("dashboard/main_data.csv")
    datetime_columns = [
      "order_purchase_timestamp",
      "order_approved_at",
      "order_delivered_customer_date",
      "order_delivered_carrier_date",
      "order_estimated_delivery_date"
   ]
    df.sort_values(by="order_purchase_timestamp", inplace=True)
    for column in datetime_columns:
      df[column] = pd.to_datetime(df[column], errors="coerce")
    return df

df = load_main_data()

recent_date = df["order_purchase_timestamp"].max()
min_date = df["order_purchase_timestamp"].min()
max_date = df["order_purchase_timestamp"].max()

with st.sidebar:
    st.image("https://raw.githubusercontent.com/Rikiyp/Project_Analysis_Data/refs/heads/main/logostickers%20outline.png")
    start_date, end_date = st.date_input(
        label='Time Span',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
  
main_df = df[(df["order_purchase_timestamp"] >= str(start_date)) & 
            (df["order_purchase_timestamp"] <= str(end_date))]


product_categories_state_df = create_product_categories_state_df(main_df)
payment_type_to_oder_df = create_payment_type_to_oder_df(main_df)
rfm_df = create_rfm_df(main_df,recent_date)

st.title("Welcome to Infinite Shop Dashboard!")
st.subheader("Purchase Count by State and Product Category")

# Langkah 3: Membuat bar chart dengan warna berbeda untuk setiap kategori
plt.figure(figsize=(12, 7))

# Menggunakan palette seaborn untuk menghasilkan warna berbeda untuk setiap kategori
unique_categories = product_categories_state_df['Top Product Category'].unique()
colors = sns.color_palette('Set2', len(unique_categories))

# Map setiap kategori ke warna yang berbeda
category_color_map = {category: colors[i] for i, category in enumerate(unique_categories)}
bar_colors = product_categories_state_df['Top Product Category'].map(category_color_map)

# Plot bar chart dengan warna yang sesuai untuk setiap kategori
bars = plt.bar(product_categories_state_df.index, product_categories_state_df['Payment Value'], color=bar_colors)

# Menambahkan label dan judul
plt.xlabel('Customer State')
plt.ylabel('Payment Value')
plt.title('Top Product Category by Payment Value for Each State')
plt.xticks(rotation=45, ha='right')

# Menambahkan legend dengan nama kategori produk
handles = [plt.Rectangle((0,0),1,1, color=category_color_map[category]) for category in unique_categories]
plt.legend(handles, unique_categories, title="Product Category", bbox_to_anchor=(1.05, 1), loc='upper left')

# Menampilkan plot dengan Streamlit
st.pyplot(plt)

st.subheader("Distribution by Payment Methods")





# Warna untuk pie chart (opsional, bisa disesuaikan dengan preferensi)
colors = ['#FFC1C1',  # Very light red (paling pudar)
          '#FF8A8A',  # Light red (lebih pudar)
          '#FF5757',  # Medium light red (merah terang sedang)
          '#FF2E2E',  # Medium red (merah sedang)
          '#FF0000']  # Solid red (merah tegas)

# Plotting pie chart
plt.figure(figsize=(10, 5))

# Menggunakan data dari hasil groupby langsung untuk membuat pie chart
plt.pie(
    payment_type_to_oder_df['order_id'],  # Data yang di-plot langsung dari kolom 'order_id'
    labels=payment_type_to_oder_df.index,  # Label diambil dari index hasil groupby (yaitu payment_type)
    autopct='%1.1f%%',  # Menampilkan persentase
    startangle=140,  # Mulai dari sudut 140 derajat
    colors=colors[:len(payment_type_to_oder_df)],  # Menyesuaikan jumlah warna dengan jumlah data
    textprops={'fontsize': 14}  # Ukuran font untuk label
)

# Tambahkan judul
plt.title('Distribution of Payment Methods', fontsize=16)

# Menambahkan legend dengan nilai absolut
plt.legend(
    labels=[f'{ptype}: {count}' for ptype, count in zip(payment_type_to_oder_df.index, payment_type_to_oder_df['order_id'])],
    loc='upper right',
    fontsize=12
)

st.pyplot(plt)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "AUD", locale='es_CO') 
    st.metric("Average Monetary", value=avg_frequency)

rfm_df["sorted_customer_id"] = rfm_df["customer_id"].apply(lambda x: x[:5])
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))
colors = ["#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9", "#90CAF9"]

sns.barplot(y="recency", x="sorted_customer_id", data=rfm_df.sort_values(by="recency", ascending=True).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel("customer_id", fontsize=30)
ax[0].set_title("By Recency (days)", loc="center", fontsize=50)
ax[0].tick_params(axis='y', labelsize=30)
ax[0].tick_params(axis='x', labelsize=35)

sns.barplot(y="frequency", x="sorted_customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel("customer_id", fontsize=30)
ax[1].set_title("By Frequency", loc="center", fontsize=50)
ax[1].tick_params(axis='y', labelsize=30)
ax[1].tick_params(axis='x', labelsize=35)

sns.barplot(y="monetary", x="sorted_customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel("customer_id", fontsize=30)
ax[2].set_title("By Monetary", loc="center", fontsize=50)
ax[2].tick_params(axis='y', labelsize=30)
ax[2].tick_params(axis='x', labelsize=35)

st.pyplot(fig)