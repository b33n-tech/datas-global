import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import requests

st.title("Visualisation PIB - Banque mondiale")

# Liste simple de pays (code ISO)
pays_dispo = {
    "France": "FRA",
    "Allemagne": "DEU",
    "États-Unis": "USA",
    "Chine": "CHN",
    "Inde": "IND"
}

pays_choisi = st.selectbox("Choisis un pays :", list(pays_dispo.keys()))

# Années disponibles
annee_debut = 2000
annee_fin = 2021

def get_pib(pays_code):
    # URL API Banque mondiale pour PIB (NY.GDP.MKTP.CD)
    url = f"http://api.worldbank.org/v2/country/{pays_code}/indicator/NY.GDP.MKTP.CD?format=json&date={annee_debut}:{annee_fin}&per_page=100"
    response = requests.get(url)
    data = response.json()

    if len(data) < 2:
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

df_pib = get_pib(pays_dispo[pays_choisi])

if df_pib is not None and not df_pib.empty:
    st.write(f"PIB pour {pays_choisi} de {annee_debut} à {annee_fin}")
    st.dataframe(df_pib)

    fig, ax = plt.subplots()
    ax.plot(df_pib['Année'], df_pib['PIB (USD)'], marker='o')
    ax.set_title(f"PIB de {pays_choisi} (en USD)")
    ax.set_xlabel("Année")
    ax.set_ylabel("PIB (en dollars)")
    ax.grid(True)

    st.pyplot(fig)
else:
    st.write("Données non disponibles pour ce pays.")
