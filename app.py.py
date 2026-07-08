import streamlit as st
import folium
from streamlit_folium import st_folium
from geopy.distance import geodesic
import pandas as pd

# 1. Configuração da Página
st.set_page_config(page_title="PUC Minas - Compras Sustentáveis", layout="wide")

st.title("🌱 Geovisualização: Compras Sustentáveis e Pegada de Carbono")
st.markdown("Protótipo de suporte à decisão para análise logística e impacto ambiental dos fornecedores da PUC Minas.")

# 2. Base de Dados Fictícia baseada na Pesquisa
dados_campuses = {
    "Nome": ["PUC Coração Eucarístico", "PUC Barreiro", "PUC São Gabriel"],
    "Lat": [-19.9242, -19.9740, -19.8582],
    "Lon": [-43.9922, -44.0203, -43.9189]
}
df_campuses = pd.DataFrame(dados_campuses)

dados_fornecedores = {
    "Nome": ["Fornecedor EcoPapel (Local)", "Distribuidora Alimentos BH", "TechLog Soluções (Nacional)", "Horta Orgânica Sarzedo"],
    "Categoria": ["Papelaria", "Alimentos", "Eletrônicos", "Alimentos"],
    "Pegada_Carbono": ["Baixa", "Média", "Alta", "Baixa"],
    "Lat": [-19.9400, -19.9100, -23.5505, -20.0333], # São Paulo incluído para simular transporte longo
    "Lon": [-43.9300, -44.0500, -46.6333, -44.1333]
}
df_fornecedores = pd.DataFrame(dados_fornecedores)

# 3. Painel Lateral de Filtros (Sidebar)
st.sidebar.header("📌 Filtros e Parâmetros")
categoria_sel = st.sidebar.multiselect("Categoria do Insumo", df_fornecedores["Categoria"].unique(), default=df_fornecedores["Categoria"].unique())
pegada_sel = st.sidebar.multiselect("Nível de Pegada de $CO_2$", df_fornecedores["Pegada_Carbono"].unique(), default=df_fornecedores["Pegada_Carbono"].unique())

buffer_km = st.sidebar.slider("Raio de Buffer Ecológico (km)", min_value=5, max_value=50, value=25)

# Filtrando dados
df_forn_filtrado = df_fornecedores[
    (df_fornecedores["Categoria"].isin(categoria_sel)) & 
    (df_fornecedores["Pegada_Carbono"].isin(pegada_sel))
]

# 4. Criação do Mapa Interativo com Folium
m = folium.Map(location=[-19.9242, -43.9922], zoom_start=10, control_scale=True)

# Adicionando os Campuses (Ícones Azuis com Buffer)
for idx, row in df_campuses.iterrows():
    folium.Marker(
        location=[row["Lat"], row["Lon"]],
        popup=f"<b>{row['Nome']}</b>",
        icon=folium.Icon(color="blue", icon="university", prefix="fa")
    ).add_to(m)
    
    # Serviço Geográfico: Buffer
    folium.Circle(
        location=[row["Lat"], row["Lon"]],
        radius=buffer_km * 1000,
        color="green",
        fill=True,
        fill_opacity=0.1,
        tooltip=f"Zona de Aquisição Sustentável ({buffer_km}km)"
    ).add_to(m)

# Adicionando os Fornecedores Filtrados (Cores por Pegada de Carbono)
cores_carbono = {"Baixa": "green", "Média": "orange", "Alta": "red"}

for idx, row in df_forn_filtrado.iterrows():
    folium.Marker(
        location=[row["Lat"], row["Lon"]],
        popup=f"<b>{row['Nome']}</b><br>Categoria: {row['Categoria']}<br>Pegada $CO_2$: {row['Pegada_Carbono']}",
        icon=folium.Icon(color=cores_carbono[row["Pegada_Carbono"]], icon="truck", prefix="fa")
    ).add_to(m)

# Renderizar Mapa no Streamlit
st_folium(m, width=1100, height=500, returned_objects=[])

# 5. Serviço Geográfico: Cálculo de Distância e Pegada de Carbono
st.subheader("📊 Análise de Distância Relativa e Emissões de Transporte")

col1, col2 = st.columns(2)
with col1:
    campus_escolhido = st.selectbox("Selecione o Campus de Destino", df_campuses["Nome"])
with col2:
    fornecedor_escolhido = st.selectbox("Selecione o Fornecedor de Origem", df_forn_filtrado["Nome"])

if campus_escolhido and fornecedor_escolhido:
    c_coords = (df_campuses[df_campuses["Nome"] == campus_escolhido]["Lat"].values[0], df_campuses[df_campuses["Nome"] == campus_escolhido]["Lon"].values[0])
    f_coords = (df_fornecedores[df_fornecedores["Nome"] == fornecedor_escolhido]["Lat"].values[0], df_fornecedores[df_fornecedores["Nome"] == fornecedor_escolhido]["Lon"].values[0])
    
    # Cálculo Geodésico
    distancia = geodesic(c_coords, f_coords).kilometers
    
    # Estimativa simples de CO2 (ex: 0.12kg de CO2 por km rodado em transporte médio)
    f_tipo = df_fornecedores[df_fornecedores["Nome"] == fornecedor_escolhido]["Pegada_Carbono"].values[0]
    fator_emissao = 0.05 if f_tipo == "Baixa" else (0.15 if f_tipo == "Média" else 0.40)
    co2_estimado = distancia * fator_emissao
    
    st.info(f"📏 **Distância Linear:** {distancia:.2f} km")
    if distancia <= buffer_km:
        st.success(f"✅ Este fornecedor está **dentro** do raio de abrangência sustentável de {buffer_km}km.")
    else:
        st.warning(f"⚠️ Este fornecedor está **fora** do raio ecológico ideal.")
        
    st.metric(label="Pegada de $CO_2$ Estimada do Transporte (Simulação)", value=f"{co2_estimado:.2f} kg CO₂e")