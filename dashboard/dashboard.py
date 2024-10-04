import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

def create_product_categories_state_df(df):
    product_categories_state= df.groupby(["customer_state", "product_category_name"]).size().reset_index(name="purchase_count")
    sorted_df = product_categories_state.sort_values(["customer_state", "purchase_count"], ascending=[True, False])
    product_categories_state_df = sorted_df.groupby("customer_state").head(1)
    return product_categories_state_df

def create_payment_type_to_oder_df(df):
    paymentType_to_order = df.groupby(by="payment_type").agg({
    "order_id" : "nunique"
    })
    paymentType_to_order = paymentType_to_order.sort_values(by="order_id", ascending=False)
    return paymentType_to_order

def create_rfm_df(df, recent_date):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_approved_at": "max",
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
#    st.image("assets/logo_qshop.jpg")
   start_date, end_date = st.date_input(
        label='Time Span',min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
  
main_df = df[(df["order_approved_at"] >= str(start_date)) & 
            (df["order_approved_at"] <= str(end_date))]


product_categories_state_df = create_product_categories_state_df(main_df)
payment_type_to_oder_df = create_payment_type_to_oder_df(main_df)
rfm_df = create_rfm_df(main_df,recent_date)

colors = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

fig, ax = plt.subplots(figsize=(24, 8))
sns.barplot(
    y="purchase_count", 
    x="customer_state",
    data=product_categories_state_df.sort_values(by="purchase_count", ascending=False),
    palette=colors,
    ax=ax
)
ax.set_title("Stacked Bar Chart of Purchase Count by State and Product Category", loc="center", fontsize=40)
ax.set_ylabel(None)
ax.set_xlabel(None)
ax.tick_params(axis='x', labelsize=35)
ax.tick_params(axis='y', labelsize=30)
st.pyplot(fig)


payment_types = ['credit_card', 'boleto', 'voucher', 'debit_card', 'not_defined']
order_counts = [76505, 19784, 3866, 1528, 3]

# Warna untuk pie chart
colors = ['#FFC1C1',  # Very light red (paling pudar)
          '#FF8A8A',  # Light red (lebih pudar)
          '#FF5757',  # Medium light red (merah terang sedang)
          '#FF2E2E',  # Medium red (merah sedang)
          '#FF0000']  # Solid red (merah tegas)


# Plotting pie chart
plt.figure(figsize=(10, 5))

plt.pie(
    order_counts,  # Data yang di-plot
    labels=payment_types,  # Labels untuk masing-masing metode pembayaran
    autopct='%1.1f%%',  # Menampilkan persentase
    startangle=140,  # Mulai dari sudut 140 derajat
    colors=colors,  # Gunakan warna yang didefinisikan
    textprops={'fontsize': 14}  # Ukuran font untuk label
)

# Tambahkan judul
plt.title('Distribution of Payment Methods', fontsize=16)

# Menambahkan legend dengan nilai absolut
plt.legend(
    labels=[f'{ptype}: {count}' for ptype, count in zip(payment_types, order_counts)],
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