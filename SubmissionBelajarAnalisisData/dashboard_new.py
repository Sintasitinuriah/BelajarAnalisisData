import streamlit as st
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import requests
import zipfile
import os

def setup_sidebar(df):
    st.sidebar.title("📍 Lokasi Pelanggan")
    selected_state = st.sidebar.selectbox("Pilih Negara Bagian:", ['All'] + sorted(df['customer_state'].dropna().unique()))
    
    st.sidebar.title("📦 Kategori Produk")
    option = st.sidebar.selectbox("Pilih kategori yang ingin Anda lihat:", [
        "Kategori Produk Termahal", 
        "Kategori Produk Termurah", 
        "Kategori dengan Pendapatan Tertinggi"
    ])
    
    st.sidebar.title("⭐ Review Kategori Produk")
    analysis_type = st.sidebar.radio("Pilih Jenis Analisis:", [
        "Distribusi Skor Review", 
        "Rata-rata Skor Review"
    ])
    
    selected_rating = st.sidebar.multiselect(
        "Pilih Skor Review:", 
        sorted(df['review_score'].unique()), 
        default=sorted(df['review_score'].unique())
    )
    
    st.sidebar.title("🛒 Transaksi Produk")
    years = sorted(df['year'].unique())
    selected_year = st.sidebar.selectbox("Pilih Tahun", options=["Keseluruhan"] + years, index=0)
    
    return selected_state, option, analysis_type, selected_rating, selected_year

def get_world_geodata():
    url = "https://naturalearth.s3.amazonaws.com/110m_cultural/ne_110m_admin_0_countries.zip"
    zip_path = "ne_110m_admin_0_countries.zip"
    extract_path = "naturalearth_data"

    if not os.path.exists(zip_path):
        with requests.get(url, stream=True) as r:
            with open(zip_path, "wb") as f:
                f.write(r.content)

    if not os.path.exists(extract_path):
        with zipfile.ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_path)

    world = gpd.read_file(os.path.join(extract_path, "ne_110m_admin_0_countries.shp"))
    return world

def plot_customer_distribution(world, df_filtered, selected_state):
    st.markdown("<h4 style='text-align: left;'>📌 Distribusi Pelanggan</h4>", unsafe_allow_html=True)
    fig, ax = plt.subplots(figsize=(12, 6))  
    world.plot(ax=ax, color='lightgray', edgecolor='black')
    ax.scatter(df_filtered['geolocation_lng'], df_filtered['geolocation_lat'], alpha=0.3, s=10, color='red', label="Pelanggan")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Peta Distribusi Pelanggan {'di ' + selected_state if selected_state != 'All' else ''}")
    ax.legend()
    st.pyplot(fig)

def plot_payment_analysis(df):
    with st.expander('Analisis Metode Pembayaran', expanded=True):
        col1, col2 = st.columns([1,1])
        with col1:
            payment_counts = df['payment_type'].value_counts().reset_index()
            payment_counts.columns = ["payment_type", "count"]
            fig_histogram = px.histogram(df, x="payment_value", nbins=20, title="Distribusi Total Pembayaran", labels={"payment_value": "Total Pembayaran", "count": "Frekuensi"}, color_discrete_sequence=["skyblue"])
            st.plotly_chart(fig_histogram, use_container_width=True)
        with col2:
            fig_barplot = px.bar(payment_counts, x="payment_type", y="count", color="payment_type", color_discrete_sequence=px.colors.qualitative.Set1, title="Metode Pembayaran yang Paling Sering Digunakan")
            st.plotly_chart(fig_barplot, use_container_width=True)

def plot_category_analysis(df, option):
    with st.expander('Analisis Kategori Produk', expanded=True):
        df_category_price = df.groupby('product_category_name_english')['price'].mean().reset_index()
        df_category_price = df_category_price.sort_values(by='price', ascending=False)
        
        top_expensive = df_category_price.nlargest(10, 'price')
        top_cheap = df_category_price.nsmallest(10, 'price')
        df_category_revenue = df.groupby('product_category_name_english')['price'].sum().reset_index()
        df_category_revenue = df_category_revenue.sort_values(by='price', ascending=False)
        top_revenue = df_category_revenue.head(10)

        if option == "Kategori Produk Termahal":
            fig = px.bar(top_expensive, x="product_category_name_english", y="price", color="price", color_continuous_scale="reds", title="Kategori Produk Termahal")
        elif option == "Kategori Produk Termurah":
            fig = px.bar(top_cheap, x="product_category_name_english", y="price", color="price", color_continuous_scale="blues", title="Kategori Produk Termurah")
        else:
            fig = px.bar(top_revenue, x="product_category_name_english", y="price", color="price", color_continuous_scale="reds", title="Kategori dengan Pendapatan Tertinggi")

        st.plotly_chart(fig, use_container_width=True)

def plot_review_analysis(df, analysis_type, selected_rating):
    with st.expander('Skor Review Berdasarkan Kategori Produk', expanded=True):
        df_filtered = df[df['review_score'].isin(selected_rating)]
        if analysis_type == "Distribusi Skor Review":
            fig_box = px.box(df_filtered, x="product_category_name_english", y="review_score", color="product_category_name_english", title="Distribusi Skor Review Berdasarkan Kategori Produk")
            st.plotly_chart(fig_box, use_container_width=True)
        else:
            review_mean = df_filtered.groupby('product_category_name_english')['review_score'].mean().reset_index()
            fig_bar = px.bar(review_mean, x="product_category_name_english", y="review_score", color="review_score", title="Rata-rata Skor Review per Kategori Produk")
            st.plotly_chart(fig_bar, use_container_width=True)

def plot_transaction_trend(df, selected_year):
    with st.expander('Transaksi Produk per Bulan', expanded=True):
        filtered_df = df if selected_year == "Keseluruhan" else df[df['year'] == selected_year]
        monthly_orders = filtered_df.groupby('month_year').size()
        average_orders = monthly_orders.mean()
        df_plot = monthly_orders.reset_index()
        df_plot['month_year'] = df_plot['month_year'].astype(str)
        fig = px.line(df_plot, x='month_year', y=0, markers=True, 
                    title=f"📈 Tren Jumlah Pesanan Tahun {selected_year if selected_year != 'Keseluruhan' else 'Keseluruhan'}",
                    labels={"month_year": "Bulan & Tahun", 0: "Jumlah Pesanan"})

        fig.add_hline(y=average_orders, line_dash="dash", line_color="red",
                    annotation_text=f"Rata-rata: {average_orders:.0f}", annotation_position="top left")

        st.plotly_chart(fig, use_container_width=True)
        
def pelanggan_per_negara(df, selected_state):
    st.markdown("<h4 style='text-align: left;'>🌍 Pelanggan per Negara</h4>", unsafe_allow_html=True)
    country_counts = df.groupby('customer_state').size().reset_index(name='customer_count')
    country_counts = country_counts.sort_values(by='customer_count', ascending=False)
    if selected_state != 'All':
        country_counts = country_counts[country_counts['customer_state'] == selected_state]
    st.dataframe(country_counts, hide_index=True, width=None, column_config={
        "customer_state": st.column_config.TextColumn("States"),
        "customer_count": st.column_config.ProgressColumn("Transactions", format="%f", min_value=0, max_value=max(country_counts.customer_count))
    })

def payment_method_values(df):
    with st.expander('Payment Method Values', expanded=True):
        total_payment_value_per_type = df.groupby('payment_type')['payment_value'].sum().sort_values(ascending=False).reset_index()
        st.dataframe(total_payment_value_per_type, hide_index=True, width=None, column_config={
            "payment_type": st.column_config.TextColumn("Payment Types"),
            "payment_value": st.column_config.ProgressColumn("Values", format="%f", min_value=0, max_value=max(total_payment_value_per_type['payment_value']))
        })

def skor_review(df):
    with st.expander('Skor Review', expanded=True):
        fig_histogram = px.histogram(df, x="review_score", nbins=20, title="Distribusi Skor Review Pelanggan", labels={"review_score": "Skor Review", "Jumlah Review": "Frekuensi"}, color_discrete_sequence=["skyblue"])
        fig_histogram.update_traces(hovertemplate="<b>Pembayaran:</b> %{x}<br>Frekuensi: %{y}<extra></extra>", marker=dict(line=dict(color='black', width=1.2)))
        st.plotly_chart(fig_histogram, use_container_width=True)

def distribusi_status_pengiriman(df):
    with st.expander('Distribusi Status Pengiriman', expanded=True):
        delivery_status_counts = df['order_status'].value_counts().reset_index()
        delivery_status_counts.columns = ["order_status", "count"]
        fig_bar = px.bar(delivery_status_counts, x="order_status", y="count", title="Distribusi Status Pengiriman", color="order_status", color_discrete_sequence=px.colors.sequential.Reds)
        st.plotly_chart(fig_bar, use_container_width=True)

def klasifikasi_segmen_pelanggan(df):
    with st.expander('Klasifikasi Segmen Pelanggan', expanded=True):
        segment_counts = df['Customer_Segment'].value_counts()
        fig = px.pie(names=segment_counts.index, values=segment_counts.values, hole=0.4, title="Persentase Klasifikasi Segmen Pelanggan", color_discrete_sequence=px.colors.qualitative.Pastel)
        fig.update_layout(showlegend=True, legend=dict(title="Status Pengiriman", orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5))
        st.plotly_chart(fig, use_container_width=True)

def about_section():
    with st.expander('About', expanded=True):
        st.write('''
            - Data: [E-Commerce Public Dataset](<https://drive.google.com/file/d/1MsAjPM7oKtVfJL_wRp1qmCajtSG1mdcK/view?usp=sharing>).
            - :orange[**Sinta Siti Nuriah**]
            - :orange[**Belajar Analisis Data dengan Python**]
        ''')

def main():
    st.set_page_config(
        page_title="E-Commerce Dashboard", 
        page_icon="🛒", 
        layout="wide", 
        initial_sidebar_state="expanded"
    )
    
    world = get_world_geodata()
    df = pd.read_csv("./dataset/all_data.csv")
    df['order_purchase_timestamp'] = pd.to_datetime(df['order_purchase_timestamp'])
    df['month_year'] = df['order_purchase_timestamp'].dt.to_period('M')
    df['year'] = df['order_purchase_timestamp'].dt.year
    df = df.dropna(subset=['review_score'])
    df['review_score'] = df['review_score'].astype(int)
    
    st.markdown("<h1 style='text-align: center; color: white;'>E-Commerce Distribution Dashboard</h1>", unsafe_allow_html=True)
    
    selected_state, option, analysis_type, selected_rating, selected_year = setup_sidebar(df)
    
    df_filtered = df[['geolocation_lat', 'geolocation_lng', 'customer_state']].dropna()
    df_filtered = df_filtered[df_filtered['customer_state'] == selected_state] if selected_state != "All" else df_filtered
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        plot_customer_distribution(world, df_filtered, selected_state)
        plot_payment_analysis(df)
        plot_category_analysis(df, option)
        plot_review_analysis(df, analysis_type, selected_rating)
        plot_transaction_trend(df, selected_year)
    
    with col2:
        pelanggan_per_negara(df, selected_state)
        payment_method_values(df)
        skor_review(df)
        distribusi_status_pengiriman(df)
        klasifikasi_segmen_pelanggan(df)
        about_section()

if __name__ == "__main__":
    main()
