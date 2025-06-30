import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.title("Visualisation du PIB — Multi-source (Banque mondiale, OCDE, Eurostat)")

# Liste de pays et codes (ISO Alpha-3 pour WB/OCDE, Eurostat parfois utilise Alpha-2)
pays_dispo = {
    "France": {"wb": "FRA", "oecd": "FRA", "eurostat": "FR"},
    "Allemagne": {"wb": "DEU", "oecd": "DEU", "eurostat": "DE"},
    "États-Unis": {"wb": "USA", "oecd": "USA", "eurostat": "US"},
    "Chine": {"wb": "CHN", "oecd": "CHN", "eurostat": "CN"},
    "Inde": {"wb": "IND", "oecd": "IND", "eurostat": "IN"}
}

# Sélection de la base de données
databases = {
    "Banque mondiale": "world_bank",
    "OCDE": "oecd",
    "Eurostat": "eurostat"
}
db_choice = st.selectbox("Sélectionne la base de données :", list(databases.keys()))
pays_choisi = st.selectbox("Choisis un pays :", list(pays_dispo.keys()))

annee_debut = 2000
annee_fin = 2021

def get_pib_world_bank(pays_code):
    url = f"http://api.worldbank.org/v2/country/{pays_code}/indicator/NY.GDP.MKTP.CD?format=json&date={annee_debut}:{annee_fin}&per_page=100"
    response = requests.get(url)
    data = response.json()
    if len(data) < 2 or not isinstance(data[1], list):
        return None
    valeurs = data[1]
    années = []
    pib = []
    for item in valeurs:
        années.append(int(item['date']))
        pib.append(item['value'])
    df = pd.DataFrame({'Année': années, 'PIB (USD)': pib})
    df = df.dropna().sort_values('Année')
    return df

def get_pib_oecd(pays_code):
    # Utilise le SDMX-JSON de l'OCDE pour le PIB courant, millions USD, valeur annuelle
    url = f"https://stats.oecd.org/sdmx-json/data/NAAGDP/{pays_code}.B1_GE.CUR+CAP+USD.A/all?startTime={annee_debut}&endTime={annee_fin}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    try:
        years = []
        values = []
        # Navigation dans la réponse OCDE SDMX-JSON
        obs = data['dataSets'][0]['observations']
        dims = data['structure']['dimensions']['observation'][0]['values']
        for i, dim in enumerate(dims):
            year = dim['id']
            key = f"0:{i}"
            if key in obs:
                val = obs[key][0]
                if val is not None:
                    years.append(int(year))
                    values.append(val * 1_000_000)  # Convert from million USD to USD
        df = pd.DataFrame({'Année': years, 'PIB (USD)': values})
        df = df.dropna().sort_values('Année')
        return df
    except Exception:
        return None

def get_pib_eurostat(pays_code):
    # Utilise la table tec00001 (PIB en millions d’euros, prix courants)
    # On convertit en USD pour cohérence avec les autres sources (taux de change non appliqué ici, c'est une simplification)
    url = f"https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/tec00001?format=JSON&geo={pays_code}"
    response = requests.get(url)
    if response.status_code != 200:
        return None
    data = response.json()
    try:
        years = []
        values = []
        for i, year in enumerate(data['dimension']['time']['category']['index']):
            idx = data['dimension']['time']['category']['index'][year]
            val = data['value'].get(f"0:{idx}")
            if val is not None and annee_debut <= int(year) <= annee_fin:
                years.append(int(year))
                # Conversion simplifiée EUR -> USD (1 EUR ≈ 1.1 USD, mais c'est variable)
                values.append(val * 1_000_000 * 1.1)
        df = pd.DataFrame({'Année': years, 'PIB (USD approx)': values})
        df = df.dropna().sort_values('Année')
        return df
    except Exception:
        return None

# Sélection de la bonne fonction
if databases[db_choice] == "world_bank":
    df_pib = get_pib_world_bank(pays_dispo[pays_choisi]["wb"])
elif databases[db_choice] == "oecd":
    df_pib = get_pib_oecd(pays_dispo[pays_choisi]["oecd"])
elif databases[db_choice] == "eurostat":
    df_pib = get_pib_eurostat(pays_dispo[pays_choisi]["eurostat"])
else:
    df_pib = None

if df_pib is not None and not df_pib.empty:
    st.write(f"PIB pour {pays_choisi} de {annee_debut} à {annee_fin} ({db_choice})")
    st.dataframe(df_pib)

    fig, ax = plt.subplots()
    y_label = "PIB (en dollars)" if "PIB (USD)" in df_pib.columns else "PIB (USD approx.)"
    ax.plot(df_pib['Année'], df_pib[df_pib.columns[1]], marker='o')
    ax.set_title(f"PIB de {pays_choisi} ({db_choice})")
    ax.set_xlabel("Année")
    ax.set_ylabel(y_label)
    ax.grid(True)

    st.pyplot(fig)
else:
    st.write("Données non disponibles pour ce pays ou cette source.")
